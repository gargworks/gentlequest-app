"""Entry point so ``python -m scripts.measurement_proxy`` starts the chassis."""

from .proxy import main

raise SystemExit(main())
