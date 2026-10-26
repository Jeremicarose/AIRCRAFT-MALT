"""Structured pipeline events with an explicit, secret-free field allowlist."""

import json
import logging

_FIELDS = frozenset(
    {
        "receiver_id",
        "correlation_id",
        "reason",
        "disposition",
        "data_provenance",
        "receiver_count",
        "residual_m",
        "iterations",
        "position_id",
        "event_id",
        "count",
        "duration_ms",
        "exception_type",
        "sequence",
    }
)


def event(logger: logging.Logger, name: str, *, level: int = logging.INFO, **fields) -> None:
    payload: dict[str, str | int | float | bool | None] = {"event": name}
    for key, value in fields.items():
        if key in _FIELDS and isinstance(value, (str, int, float, bool, type(None))):
            payload[key] = value[:160] if isinstance(value, str) else value
    logger.log(level, json.dumps(payload, sort_keys=True, allow_nan=False))
