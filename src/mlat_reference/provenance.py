"""Persistent source vocabulary shared by storage, runtime and API."""

DATA_PROVENANCE = frozenset({"SYNTHETIC", "HISTORICAL_REPLAY", "LIVE", "UNKNOWN"})


def validate_provenance(value: str) -> str:
    if value not in DATA_PROVENANCE:
        raise ValueError("data_provenance must be SYNTHETIC, HISTORICAL_REPLAY, LIVE or UNKNOWN")
    return value
