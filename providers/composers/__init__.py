"""TB quality-compound composers.

Helpers that orchestrate "TB grounds, frontier model composes" flows for
the /tb/turn endpoint and the run_tb_principal CLI wrapper. Subprocess
primitive (`claude -p`) lives here so callers don't duplicate the
fallback / timeout / error-banner pattern.
"""

from .sonnet_principal import compose_with_sonnet, wrap_tb_advice
from .haiku_verifier import verify_grounding
from . import templates

__all__ = [
    "compose_with_sonnet",
    "wrap_tb_advice",
    "verify_grounding",
    "templates",
]
