"""Chat event publisher — backend → shared substrate.

Publishes `chat.request.received` and `chat.response.completed` events
to `.brain/ledger/events.jsonl` so chat becomes a peer on the same
substrate every lever + consumer reads. Best-effort: if publication
fails, the chat request still completes normally.

Events carry a ``request_id`` that correlates the received/completed
pair. Downstream (bull_audit, MCP resources, future training curriculum)
joins on it.

Import path note: we import ``scripts.levers.run_lever.publish_event``
only here. No module under ``backend/app/`` imports back into
``scripts.levers``, so no cycle risk. A dedicated import-smoke test
(``tests/test_chat_events.py::test_no_circular_import``) guards this.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from scripts.levers.run_lever import publish_event as _publish
except ImportError as _e:
    logger.warning(
        "chat event publisher unavailable — chat.* events will not land on "
        "the shared ledger. Cause: %s",
        _e,
    )
    _publish = None  # type: ignore[assignment]


def publish_chat_request_received(request_id: str, session_id: Any) -> None:
    """Fire at the top of a chat POST handler. Never raises."""
    if _publish is None:
        return
    try:
        _publish(
            "chat.request.received",
            request_id=request_id,
            session_id=session_id,
        )
    except Exception as e:
        logger.warning("chat.request.received publish failed: %s", e)


def publish_chat_response_completed(
    request_id: str,
    session_id: Any,
    outcome: str,
    **extra: Any,
) -> None:
    """Fire in the finally block of a chat POST handler.

    ``outcome`` must be one of the substrate OUTCOMES. Use ``"clean"``
    for a successful response, ``"error"`` for any failure. Bad values
    are rejected by ``publish_event`` and surface as a
    ``lever.schema.violation`` event, not an exception.
    """
    if _publish is None:
        return
    try:
        _publish(
            "chat.response.completed",
            outcome=outcome,
            request_id=request_id,
            session_id=session_id,
            **extra,
        )
    except Exception as e:
        logger.warning("chat.response.completed publish failed: %s", e)
