"""Operational health derived only from observed runtime evidence."""


def component_health(
    runtime: dict, context: dict, *, registry_configured: bool, database_ok: bool = True
) -> list[dict]:
    components = []

    def add(name, status, reason, action):
        components.append({"component": name, "status": status, "reason": reason, "action": action})

    add("backend", "HEALTHY", "The API handled this request.", "No action required.")
    add(
        "frontend",
        "NOT CONFIGURED",
        "Frontend runs as a separate service; the API cannot observe browser rendering.",
        "Check the frontend /healthz endpoint and open the console.",
    )
    add(
        "database",
        "HEALTHY" if database_ok else "FAILED",
        "SQLite reads succeeded." if database_ok else "SQLite could not be read.",
        (
            "Maintain backups."
            if database_ok
            else "Check database permissions, disk space, and lock contention."
        ),
    )
    fresh = bool(runtime.get("telemetry_fresh") and runtime.get("is_running"))
    provenance = context.get("data_provenance", "UNKNOWN")
    registry_ok = bool(fresh and runtime.get("registry_discovery_live"))
    for name in ("ckb_rpc", "ckb_indexer", "receiver_discovery"):
        add(
            name,
            "HEALTHY" if registry_ok else "DEGRADED" if registry_configured else "NOT CONFIGURED",
            (
                "Last completed discovery succeeded; this is not an independent continuous RPC probe."
                if registry_ok
                else "Current registry discovery is not verified."
            ),
            (
                "No action required."
                if registry_ok
                else "Verify CKB RPC/indexer URLs, TLS certificates, and the deployed registry code hash."
            ),
        )
    signal_fresh = fresh and runtime.get("signal_fresh", False)
    add(
        "feed_transport",
        "HEALTHY" if signal_fresh else "DEGRADED",
        (
            "Recent observations arrived."
            if signal_fresh
            else "No fresh observation evidence is available."
        ),
        (
            "Check receiver feed connections and receiver clocks."
            if not signal_fresh
            else "No action required."
        ),
    )
    correlated = runtime.get("observation_counts", {}).get("correlated", 0)
    add(
        "correlation",
        "HEALTHY" if fresh and correlated else "DEGRADED",
        (
            "Correlated groups were observed in this process."
            if correlated
            else "No correlated group has been observed."
        ),
        "Provide the same transmission from at least four distinct qualified receivers.",
    )
    solved = runtime.get("successful_solves", 0)
    add(
        "solver",
        "HEALTHY" if fresh and solved else "DEGRADED",
        (
            "The numerical solver has produced positions."
            if solved
            else "No successful numerical solve is recorded."
        ),
        "Inspect clock rejection, receiver geometry, and solver failure diagnostics.",
    )
    failed_store = bool(runtime.get("last_storage_error"))
    add(
        "storage",
        (
            "FAILED"
            if failed_store
            else "HEALTHY" if fresh and runtime.get("last_store_at") else "DEGRADED"
        ),
        (
            "A position could not be stored."
            if failed_store
            else "Storage health is based on the last successful write."
        ),
        (
            "Check disk space, permissions and SQLite locks."
            if failed_store
            else "Inspect last-write age; configure backups and retention."
        ),
    )
    add(
        "replay_engine",
        (
            "HEALTHY"
            if provenance == "HISTORICAL_REPLAY" and context.get("replay_status") == "completed"
            else "DEGRADED" if provenance == "HISTORICAL_REPLAY" else "NOT CONFIGURED"
        ),
        (
            "Historical replay is isolated in this database."
            if provenance == "HISTORICAL_REPLAY"
            else "This database is not a historical replay session."
        ),
        (
            "Inspect replay event results and source limitations."
            if provenance == "HISTORICAL_REPLAY"
            else "Run the historical replay command with a separate database."
        ),
    )
    return components
