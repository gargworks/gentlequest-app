# sovereign/ — Code that NEVER ships to the public repo.
#
# Everything in this directory is excluded from `git archive` via
# .gitattributes export-ignore. On public builds, any
# `from .sovereign import X` hits ImportError and gracefully degrades.
#
# Contents:
#   local_llm.py        — Third Brother provider (Ollama/vLLM/llama.cpp)
#   orchestrator_ext.py — TB routing + PrivateGraphTrainer
#   archive_cli.py      — handle_archive_command + argparse setup
#   chat_hooks.py       — DPO/CoT/Shadow capture in chat loop
#   provider_config.py  — claude-code provider + moat features
