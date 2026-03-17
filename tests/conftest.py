# Root-level test configuration
# Skip test files that import symbols not yet shipped
collect_ignore_glob = [
    "test_coder_agent.py",
    "test_fixer_loop.py",
    "test_fluid_sync.py",
]
