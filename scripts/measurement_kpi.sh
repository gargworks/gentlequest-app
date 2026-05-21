#!/bin/zsh
# KPI dashboard for the Phase-1 R² measurement experiment.
# Run anytime to see green/yellow/red status of all gates.
#
# Usage: bash ~/ai-mvp-backend/scripts/measurement_kpi.sh

set -u
REPO="/Users/lokeshgarg/ai-mvp-backend"
CUTOFF_UTC="2026-04-27T11:52:24+00:00"   # PR #173 merge time = post-fix start

cd "$REPO" || exit 1

python3 <<'PY'
import json, collections, subprocess
from datetime import datetime, timezone

CUTOFF = datetime.fromisoformat("2026-04-27T11:52:24+00:00")
GREEN = "\033[32m"; YELLOW = "\033[33m"; RED = "\033[31m"; NC = "\033[0m"; BOLD = "\033[1m"

def color(value, green_thresh, yellow_thresh, higher_is_better=True):
    if higher_is_better:
        if value >= green_thresh: return f"{GREEN}{value}{NC}"
        if value >= yellow_thresh: return f"{YELLOW}{value}{NC}"
        return f"{RED}{value}{NC}"
    else:
        if value <= green_thresh: return f"{GREEN}{value}{NC}"
        if value <= yellow_thresh: return f"{YELLOW}{value}{NC}"
        return f"{RED}{value}{NC}"

def status_emoji(passing): return "✅" if passing else "❌"

print(f"\n{BOLD}=== Phase-1 measurement KPI dashboard ==={NC}")
print(f"Post-fix cutoff: {CUTOFF.isoformat()} (PR #173 merge)\n")

surfaces = [
    ("cc_main", f"{__import__('os').path.expanduser('~')}/ai-mvp-backend/.brain/measurement/turns.jsonl"),
    ("cc_peer", f"{__import__('os').path.expanduser('~')}/ai-mvp-backend/.brain/measurement/turns.peer.jsonl"),
]

import tempfile, os
all_results = []
for label, path in surfaces:
    if not os.path.exists(path):
        print(f"  {label}: file missing — proxy never ran"); continue
    counts = collections.Counter(); post = 0
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    with open(path) as f:
        for line in f:
            try: rec = json.loads(line)
            except: continue
            ts = rec.get("timestamp")
            if not ts: continue
            t = datetime.fromisoformat(ts.replace("Z","+00:00"))
            if t < CUTOFF: continue
            tmp.write(line); post += 1
            counts[rec.get("per_stream_attribution",{}).get("attribution_confidence","?")] += 1
    tmp.close()
    if post == 0:
        print(f"  {label}: 0 post-fix turns yet (waiting for capture)"); os.unlink(tmp.name); continue
    high_pct = (counts.get("high",0) / post) * 100
    out = subprocess.run(
        ["python3", f"{os.path.expanduser('~')}/ai-mvp-backend/.brain/measurement/analysis/phase1_baseline_fit.py",
         "--input", tmp.name, "--json"],
        capture_output=True, text=True
    )
    os.unlink(tmp.name)
    fit = json.loads(out.stdout)["fit"] if out.returncode == 0 else {"r_squared": 0, "n": 0}
    all_results.append((label, post, high_pct, fit["r_squared"], counts))

print(f"  {BOLD}{'Surface':<10}{'N':<8}{'High%':<10}{'R²':<10}{'Distribution':<40}{NC}")
print(f"  {'-'*78}")
for label, post, high_pct, r2, counts in all_results:
    n_color = color(post, 500, 200, True).replace(str(post), f"{post:<8}")
    h_color = color(round(high_pct,1), 90, 80, True).replace(str(round(high_pct,1)), f"{high_pct:<6.1f}%")
    r2_color = color(round(r2,3), 0.8, 0.5, True).replace(str(round(r2,3)), f"{r2:<8.4f}")
    dist_str = ", ".join(f"{k}:{v}" for k,v in counts.most_common())
    print(f"  {label:<10}{n_color:<22}{h_color:<24}{r2_color:<24}{dist_str:<40}")

print(f"\n  {BOLD}Acceptance gates (per runbook §4):{NC}")
gates = []
for label, post, high_pct, r2, counts in all_results:
    attr_pass = high_pct >= 90
    r2_pass = r2 >= 0.8
    n_pass = post >= 500
    overall = attr_pass and r2_pass and n_pass
    gates.append((label, attr_pass, r2_pass, n_pass, overall))
    print(f"    {label}: attribution {status_emoji(attr_pass)} ({high_pct:.1f}% / target ≥90%)  |  R² {status_emoji(r2_pass)} ({r2:.4f} / target ≥0.8)  |  N {status_emoji(n_pass)} ({post} / target ≥500)")

print(f"\n  {BOLD}Verdict:{NC}")
all_pass = all(g[4] for g in gates) if gates else False
if all_pass:
    print(f"    {GREEN}ALL GREEN — compute empirical multiplier; unlock feedback_anti_drift_external_copy_no_5_10x.md{NC}")
else:
    failures = []
    for label, ap, rp, np_, _ in gates:
        if not (ap and rp and np_):
            missing = []
            if not ap: missing.append("attribution")
            if not rp: missing.append("R²")
            if not np_: missing.append("N")
            failures.append(f"{label}({'+'.join(missing)})")
    print(f"    {YELLOW}PENDING — gates failing on: {', '.join(failures)}{NC}")
    print(f"    Locked positioning: feedback_anti_drift_external_copy_no_5_10x.md STAYS LOCKED until all-green.")

# Operational health
print(f"\n  {BOLD}Operational health:{NC}")
import subprocess
for port in (8787, 8788):
    r = subprocess.run(["lsof","-nP",f"-iTCP:{port}","-sTCP:LISTEN"], capture_output=True, text=True)
    listening = "LISTEN" in r.stdout
    print(f"    proxy :{port}  {status_emoji(listening)}")
print()
PY
