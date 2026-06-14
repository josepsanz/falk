"""Send alert messages to a Telegram chat via the Bot API."""

from __future__ import annotations

import logging

import requests

from falk.config import load_config

logger = logging.getLogger(__name__)

_SEND_MESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"
_REQUEST_TIMEOUT_S = 10


def send_alert(message: str) -> bool:
    """Send ``message`` to the configured Telegram chat.

    Alerting must never break the calling job, so a missing/disabled config or
    a transport error is logged and reported via the return value rather than
    raised.

    Returns:
        True if the message was delivered, False otherwise.
    """
    config = load_config().get("telegram") or {}
    if not config.get("enabled"):
        return False

    try:
        response = requests.post(
            _SEND_MESSAGE_URL.format(token=config["bot_token"]),
            json={"chat_id": config["chat_id"], "text": message},
            timeout=_REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()
    except (requests.RequestException, KeyError):
        logger.exception("Failed to send Telegram alert")
        return False

    return True
