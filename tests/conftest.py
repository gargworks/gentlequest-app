# Root-level test configuration
# Skip test files that import symbols not yet shipped
collect_ignore_glob = [
    "test_coder_agent.py",
    "test_fixer_loop.py",
    "test_fluid_sync.py",
]

# Skip tests whose source modules live under gitignored `.brain/training/`.
# Each of these test files does `sys.path.insert(0, …/.brain/training)` and
# then imports the training script. On CI that directory doesn't exist, so
# collection fails with ModuleNotFoundError. Local dev where the dir exists
# keeps running them.
from pathlib import Path

_TRAINING_DIR = Path(__file__).resolve().parent.parent / ".brain" / "training"
if not _TRAINING_DIR.exists():
    collect_ignore_glob += [
        "test_colab_push_data.py",
        "test_process_all_sources.py",
        "test_run_evals.py",
    ]
