"""Phase 3 §3.8 — topic clustering pipeline.

Clusters embeddings of `kind in (telegram, whatsapp, conversation_turn)`
chunks into topical groups. Generates auto-suggested labels (top
keywords + representative chunks); Lokesh confirms via
`scripts/label_clusters.py`.

Algorithm decision: DEC-013.
- Primary: BERTopic v0.16+ (auto-imported if available; ships with
  c-TF-IDF labeling, hierarchical merging, dynamic topic modeling).
- Fallback: sklearn.cluster.HDBSCAN + sklearn.feature_extraction
  (TfidfVectorizer for keywords). Always available; no extra dep.
- Runtime decision: BERTopic if installed AND silhouette ≥ 0.4 on a
  small probe; otherwise sklearn fallback.

Brain corpus (kind=brain) and archive corpus clustered SEPARATELY —
joining produces useless mush ("tech_with_manju" topics). The pipeline
takes a pre-filtered chunk set; caller scopes by `kind`.

Cluster sizing: target 10–20 clusters. min_cluster_size scales with
corpus: max(50, total // 30) so a year of archive yields meaningful
clusters, not noise.

Outputs:
    cluster_proposal.jsonl — one line per cluster with:
        cluster_id, label_proposed, n_chunks, keywords[], top_chunks[],
        embedding (centroid), sample_external_ids[]
    cluster_centroids.json — written via thread_topic_resolver.write_centroids
        once Lokesh approves labels in label_clusters.py.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


# ── Constants (env-tunable knobs live in the runner CLI) ─────────────

DEFAULT_MIN_CLUSTER_FLOOR = 50
DEFAULT_MIN_CLUSTER_RATIO = 30   # min_cluster_size = max(floor, total // ratio)
DEFAULT_TARGET_CLUSTERS = (10, 20)
SILHOUETTE_GREEN = 0.4           # DEC-013 threshold; below = fallback
TOP_KEYWORDS = 8
TOP_REPRESENTATIVE_CHUNKS = 5


# ── Result types ─────────────────────────────────────────────────────

@dataclass
class ClusterResult:
    """Per-cluster summary emitted to cluster_proposal.jsonl."""
    cluster_id: int               # -1 = noise (HDBSCAN convention)
    label_proposed: str           # auto-generated; Lokesh confirms in label CLI
    n_chunks: int
    centroid: List[float]         # mean embedding of cluster members
    keywords: List[str]           # top-N TF-IDF keywords for the cluster
    top_chunks: List[str]         # top-N representative chunks (closest to centroid)
    sample_external_ids: List[str]
    label_status: str = "proposed"  # "proposed" | "approved" | "skipped"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "label_proposed": self.label_proposed,
            "n_chunks": self.n_chunks,
            "centroid": self.centroid,
            "keywords": self.keywords,
            "top_chunks": self.top_chunks,
            "sample_external_ids": self.sample_external_ids,
            "label_status": self.label_status,
        }


@dataclass
class ClusterRun:
    """Output of cluster() — list of ClusterResult + run-level metadata."""
    algorithm: str                      # "bertopic" | "sklearn_hdbscan"
    silhouette: Optional[float]
    n_clusters: int
    n_noise: int
    clusters: List[ClusterResult] = field(default_factory=list)


# ── Math helpers (numpy-free for portability) ────────────────────────

def _l2_normalize(vec: Sequence[float]) -> List[float]:
    n = math.sqrt(sum(x * x for x in vec))
    if n == 0:
        return list(vec)
    return [x / n for x in vec]


def _mean_embedding(vecs: Sequence[Sequence[float]]) -> List[float]:
    if not vecs:
        return []
    dim = len(vecs[0])
    out = [0.0] * dim
    for v in vecs:
        for i in range(dim):
            out[i] += v[i]
    n = len(vecs)
    return [x / n for x in out]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return sum(a[i] * b[i] for i in range(len(a))) / (na * nb)


def min_cluster_size(total: int) -> int:
    """Heuristic: max(50, total // 30). Scales with corpus."""
    return max(DEFAULT_MIN_CLUSTER_FLOOR, total // DEFAULT_MIN_CLUSTER_RATIO)


# ── Auto-label heuristic ─────────────────────────────────────────────

def auto_label_from_keywords(keywords: Sequence[str], max_chars: int = 30) -> str:
    """Build a slug-style label from top keywords. Lokesh's CLI replaces
    these with real names; this is the placeholder."""
    if not keywords:
        return "unlabeled"
    parts = [k.lower() for k in keywords[:3]]
    label = "_".join(parts)[:max_chars].rstrip("_")
    return label or "unlabeled"


# ── Keyword extraction (TF-IDF — sklearn fallback path) ──────────────

def extract_keywords_tfidf(
    cluster_docs: Sequence[str],
    background_docs: Sequence[str],
    top_n: int = TOP_KEYWORDS,
) -> List[str]:
    """Top-N TF-IDF keywords for a cluster vs the rest of the corpus.

    Lazy-imports sklearn so the module is loadable without it; clustering
    callers must have sklearn (we depend on HDBSCAN below).
    """
    if not cluster_docs:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        # Cheap fallback: most-frequent non-stopword tokens
        return _frequency_keywords(cluster_docs, top_n)

    # Combine cluster + a sample of background for IDF balance
    background_sample = list(background_docs[:max(1, len(cluster_docs) * 3)])
    all_docs = list(cluster_docs) + background_sample
    try:
        vec = TfidfVectorizer(
            stop_words="english",
            min_df=1, max_df=0.85,
            ngram_range=(1, 2),
            max_features=2000,
        )
        m = vec.fit_transform(all_docs)
    except ValueError:
        # Empty vocabulary (all stop words / single short doc) → frequency fallback
        return _frequency_keywords(cluster_docs, top_n)

    import numpy as np
    cluster_n = len(cluster_docs)
    # .sum(axis=0) on a sparse matrix returns np.matrix; np.asarray + ravel
    cluster_scores = m[:cluster_n].sum(axis=0)
    feature_names = vec.get_feature_names_out()
    scores = np.asarray(cluster_scores).ravel()
    pairs = sorted(
        ((feature_names[i], scores[i]) for i in range(len(feature_names))),
        key=lambda p: -p[1],
    )
    return [name for name, score in pairs[:top_n] if score > 0]


def _frequency_keywords(docs: Sequence[str], top_n: int) -> List[str]:
    """Sklearn-free fallback: top-N most-frequent tokens (length > 2,
    not in a tiny built-in stop list)."""
    import re
    from collections import Counter
    stop = {
        "the", "and", "for", "you", "are", "but", "not", "with",
        "this", "that", "have", "was", "were", "from", "your", "they",
    }
    counter: Counter = Counter()
    for doc in docs:
        for tok in re.findall(r"[a-z]{3,}", doc.lower()):
            if tok not in stop:
                counter[tok] += 1
    return [w for w, _ in counter.most_common(top_n)]


# ── Sklearn HDBSCAN clustering path ──────────────────────────────────

def _cluster_sklearn(
    embeddings: List[List[float]],
    *,
    min_size: int,
) -> Tuple[List[int], Optional[float]]:
    """Run sklearn HDBSCAN. Returns (labels, silhouette).
    silhouette is None if all points classified as noise or only 1 cluster."""
    try:
        from sklearn.cluster import HDBSCAN
        from sklearn.metrics import silhouette_score
    except ImportError as e:
        raise RuntimeError(
            "scripts/cluster_topics: sklearn is required for the fallback "
            "clustering path. Install via `pip install scikit-learn`."
        ) from e

    import numpy as np
    X = np.asarray(embeddings, dtype="float32")

    clusterer = HDBSCAN(
        min_cluster_size=min_size,
        min_samples=max(2, min_size // 5),
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(X)
    unique = set(labels) - {-1}

    sil: Optional[float] = None
    if len(unique) >= 2:
        # Filter out noise points for silhouette
        mask = labels != -1
        if mask.sum() >= len(unique) + 1:
            try:
                sil = float(silhouette_score(X[mask], labels[mask],
                                             metric="cosine"))
            except ValueError:
                sil = None

    return labels.tolist(), sil


# ── BERTopic clustering path (optional) ──────────────────────────────

def _cluster_bertopic(
    embeddings: List[List[float]],
    docs: List[str],
    *,
    min_size: int,
) -> Tuple[List[int], Optional[float]]:
    """Run BERTopic. Raises RuntimeError if not installed."""
    try:
        from bertopic import BERTopic
    except ImportError as e:
        raise RuntimeError(
            "BERTopic not available; caller should fall back to sklearn."
        ) from e

    import numpy as np
    model = BERTopic(min_topic_size=min_size, verbose=False)
    labels, _ = model.fit_transform(docs, embeddings=np.asarray(embeddings))

    # Compute silhouette via sklearn helper so the metric is comparable
    # across paths
    try:
        from sklearn.metrics import silhouette_score
        unique = set(labels) - {-1}
        if len(unique) >= 2:
            mask = np.asarray(labels) != -1
            if mask.sum() >= len(unique) + 1:
                sil = float(silhouette_score(
                    np.asarray(embeddings)[mask],
                    np.asarray(labels)[mask],
                    metric="cosine",
                ))
            else:
                sil = None
        else:
            sil = None
    except ImportError:
        sil = None
    return list(labels), sil


# ── Public API ───────────────────────────────────────────────────────

def cluster(
    embeddings: List[List[float]],
    docs: List[str],
    external_ids: List[str],
    *,
    min_size: Optional[int] = None,
    prefer_bertopic: bool = True,
) -> ClusterRun:
    """Run clustering on a pre-filtered chunk set.

    Args:
        embeddings: per-chunk vectors (1024-dim qwen3-embedding)
        docs: per-chunk content (parallel to embeddings)
        external_ids: per-chunk source-stable id (parallel)
        min_size: HDBSCAN min_cluster_size (auto-computed if None)
        prefer_bertopic: try BERTopic first (DEC-013); fallback to
                         sklearn HDBSCAN if BERTopic unavailable OR
                         silhouette < 0.4.

    Caller is responsible for scoping by `kind` (don't mix brain +
    archive corpus per anti-corner trap §3.8).
    """
    n = len(embeddings)
    if n == 0 or len(docs) != n or len(external_ids) != n:
        return ClusterRun(
            algorithm="none", silhouette=None,
            n_clusters=0, n_noise=0,
        )

    if min_size is None:
        min_size = min_cluster_size(n)

    # Try BERTopic first if requested
    algorithm = "sklearn_hdbscan"
    labels: List[int]
    silhouette: Optional[float]

    if prefer_bertopic:
        try:
            labels, silhouette = _cluster_bertopic(
                embeddings, docs, min_size=min_size,
            )
            algorithm = "bertopic"
            # If BERTopic produced poor coherence, fall back to sklearn
            if silhouette is not None and silhouette < SILHOUETTE_GREEN:
                logger.info(
                    "cluster_topics: BERTopic silhouette %.3f < %s; "
                    "falling back to sklearn HDBSCAN",
                    silhouette, SILHOUETTE_GREEN,
                )
                labels, silhouette = _cluster_sklearn(
                    embeddings, min_size=min_size,
                )
                algorithm = "sklearn_hdbscan"
        except RuntimeError:
            labels, silhouette = _cluster_sklearn(
                embeddings, min_size=min_size,
            )
    else:
        labels, silhouette = _cluster_sklearn(embeddings, min_size=min_size)

    # Build per-cluster summaries
    clusters: Dict[int, Dict[str, List]] = {}
    for i, lbl in enumerate(labels):
        slot = clusters.setdefault(lbl, {"emb": [], "doc": [], "eid": []})
        slot["emb"].append(embeddings[i])
        slot["doc"].append(docs[i])
        slot["eid"].append(external_ids[i])

    n_noise = len(clusters.get(-1, {}).get("emb", []))
    real_clusters = {k: v for k, v in clusters.items() if k != -1}

    # All non-cluster docs become the background for TF-IDF IDF balance
    all_docs_flat = [d for d in docs]

    cluster_results: List[ClusterResult] = []
    for cid, slot in sorted(real_clusters.items()):
        members_emb = slot["emb"]
        members_doc = slot["doc"]
        members_eid = slot["eid"]
        centroid = _mean_embedding(members_emb)

        # Background = all docs not in this cluster (for TF-IDF)
        background = [
            d for i, d in enumerate(all_docs_flat) if labels[i] != cid
        ]
        keywords = extract_keywords_tfidf(members_doc, background)

        # Top-N representative chunks (closest to centroid)
        scored = sorted(
            range(len(members_emb)),
            key=lambda i: -_cosine(members_emb[i], centroid),
        )
        top_idx = scored[:TOP_REPRESENTATIVE_CHUNKS]
        top_chunks = [members_doc[i][:240] for i in top_idx]
        sample_eids = [members_eid[i] for i in top_idx]

        cluster_results.append(ClusterResult(
            cluster_id=int(cid),
            label_proposed=auto_label_from_keywords(keywords),
            n_chunks=len(members_emb),
            centroid=centroid,
            keywords=keywords,
            top_chunks=top_chunks,
            sample_external_ids=sample_eids,
        ))

    return ClusterRun(
        algorithm=algorithm,
        silhouette=silhouette,
        n_clusters=len(cluster_results),
        n_noise=n_noise,
        clusters=cluster_results,
    )


# ── Drift detection (per spec §3.10) ─────────────────────────────────

def find_cluster_drift(
    centroids: Dict[str, Dict[str, Any]],
    new_chunks: List[Tuple[List[float], str, str]],
    *,
    threshold_low: float = 0.4,
    threshold_split: float = 0.7,
) -> List[Tuple[str, str]]:
    """Find chunks that don't fit any approved cluster well.

    Returns list of (external_id, label) where label is one of:
        "needs_review" — best cluster cosine < threshold_low (orphan)
        "potential_split:<cluster>" — best cluster cosine in
            [threshold_low, threshold_split) (drift toward split)

    Pure function — caller decides whether to surface or auto-act.
    """
    out: List[Tuple[str, str]] = []
    if not centroids:
        return out
    for emb, content, eid in new_chunks:
        best_cluster: Optional[str] = None
        best_sim = -1.0
        for label, cluster in centroids.items():
            ce = cluster.get("embedding") or []
            if not ce:
                continue
            sim = _cosine(emb, ce)
            if sim > best_sim:
                best_sim = sim
                best_cluster = label
        if best_cluster is None:
            continue
        if best_sim < threshold_low:
            out.append((eid, "needs_review"))
        elif best_sim < threshold_split:
            out.append((eid, f"potential_split:{best_cluster}"))
    return out


# ── Auto-route on insert (per spec §3.11) ────────────────────────────

def assign_topic(
    embedding: List[float],
    centroids: Dict[str, Dict[str, Any]],
    *,
    threshold: float = 0.5,
) -> Optional[str]:
    """Assign a single new chunk to the nearest approved cluster centroid.

    Returns the cluster label if cosine ≥ threshold; else None (chunk
    stays unclustered until next re-cluster pass picks it up).
    """
    if not embedding or not centroids:
        return None
    best_label: Optional[str] = None
    best_sim = -1.0
    for label, cluster in centroids.items():
        ce = cluster.get("embedding") or []
        if not ce:
            continue
        sim = _cosine(embedding, ce)
        if sim > best_sim:
            best_sim = sim
            best_label = label
    if best_sim >= threshold:
        return best_label
    return None


# ── Persistence: cluster proposals → JSONL ───────────────────────────

def write_cluster_proposal(
    run: ClusterRun,
    path: Path,
) -> bool:
    """Atomic write of cluster proposals to JSONL. label_clusters.py
    reads this for the interactive labeling pass."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "_meta": {
                    "algorithm": run.algorithm,
                    "silhouette": run.silhouette,
                    "n_clusters": run.n_clusters,
                    "n_noise": run.n_noise,
                },
            }) + "\n")
            for c in run.clusters:
                f.write(json.dumps(c.to_dict()) + "\n")
        tmp.replace(path)
        return True
    except OSError as e:
        logger.error("cluster_proposal: write failed (%s)", e)
        return False
