"""Shared runtime configuration loading for MLAT entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
import os

from network.ckb_client import NetworkConfig
from demo_scenarios import get_demo_scenario, get_scenario_metadata


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DemoSettings:
    """Environment-derived hosted demo settings."""

    enabled: bool
    scenario: str
    read_only: bool
    label: str
    auto_connect: bool
    scenario_metadata: dict


@dataclass(frozen=True)
class RuntimeSettings:
    """Environment-derived runtime settings."""

    network_config: NetworkConfig
    db_path: str
    simulation_retention_hours: int
    statistics_retention_days: int
    health_stale_signal_seconds: int
    stats_interval_seconds: int
    require_live_benchmarkable_output: bool
    strict_production_mode: bool
    demo: DemoSettings


def _validate_runtime_settings(
    *,
    strict_production_mode: bool,
    demo_enabled: bool,
    config: NetworkConfig,
) -> None:
    """Reject invalid demo/live combinations before runtime startup."""
    if not strict_production_mode:
        return

    configured_transport = (config.fourdsky_transport or "auto").strip().lower()
    violations: list[str] = []

    if demo_enabled:
        violations.append("DEMO_MODE=true")
    if configured_transport == "simulation":
        violations.append("FOURDSKY_TRANSPORT=simulation")
    if configured_transport == "auto":
        violations.append("FOURDSKY_TRANSPORT=auto")
    if config.simulate_if_unavailable:
        violations.append("SIMULATE_IF_UNAVAILABLE=true")

    if violations:
        joined = ", ".join(violations)
        raise ValueError(
            "STRICT_PRODUCTION_MODE requires explicit live ingest configuration and forbids: "
            f"{joined}."
        )



def load_runtime_settings(
    *,
    max_receivers_default: int,
    db_path_default: str = "mlat_data.db",
) -> RuntimeSettings:
    """Load shared network and storage settings from environment."""
    fourdsky_endpoint = os.getenv("FOURDSKYENDPOINT") or os.getenv("FOURDSKY_ENDPOINT", "")
    fourdsky_api_key = os.getenv("FOURDSKYAPIKEY") or os.getenv("FOURDSKY_API_KEY")
    strict_production_mode = env_bool("STRICT_PRODUCTION_MODE", False)

    config = NetworkConfig(
        ckb_network=os.getenv("CKB_NETWORK", "testnet"),
        ckb_rpc_url=os.getenv("CKB_RPC_URL", "https://testnet.ckb.dev/rpc"),
        ckb_indexer_url=os.getenv("CKB_INDEXER_URL", "https://testnet.ckb.dev/indexer"),
        receiver_registry_type_hash=os.getenv("RECEIVER_REGISTRY_TYPE_HASH", ""),
        api_key=fourdsky_api_key,
        fourdskyendpoint=fourdsky_endpoint,
        fourdsky_transport=os.getenv("FOURDSKY_TRANSPORT", "auto"),
        fourdsky_auth_header=os.getenv("FOURDSKY_AUTH_HEADER", "X-API-Key"),
        fourdsky_auth_scheme=os.getenv("FOURDSKY_AUTH_SCHEME") or None,
        fourdsky_auth_token=os.getenv("FOURDSKY_AUTH_TOKEN") or None,
        fourdsky_subscribe_message=os.getenv("FOURDSKY_SUBSCRIBE_MESSAGE") or None,
        fourdsky_bridge_command=os.getenv("FOURDSKY_BRIDGE_COMMAND") or None,
        max_receivers=int(os.getenv("MAX_RECEIVERS", str(max_receivers_default))),
        simulate_if_unavailable=env_bool("SIMULATE_IF_UNAVAILABLE", True),
        strict_production_mode=strict_production_mode,
        ssl_verify=env_bool("CKB_SSL_VERIFY", True),
        max_record_age_seconds=int(os.getenv("CKB_MAX_RECORD_AGE_SECONDS", "86400")),
        hybrid_simulation_min_receivers=int(
            os.getenv("CKB_HYBRID_SIMULATION_MIN_RECEIVERS", "4")
        ),
        demo_scenario=os.getenv("DEMO_SCENARIO", "default"),
    )
    db_path = os.getenv("DATABASE_PATH", db_path_default)
    demo_enabled = env_bool("DEMO_MODE", False)
    demo_scenario = os.getenv("DEMO_SCENARIO", "default")
    scenario = get_demo_scenario(demo_scenario)
    demo_label = os.getenv("DEMO_LABEL", scenario.label)

    _validate_runtime_settings(
        strict_production_mode=strict_production_mode,
        demo_enabled=demo_enabled,
        config=config,
    )

    return RuntimeSettings(
        network_config=config,
        db_path=db_path,
        simulation_retention_hours=int(os.getenv("SIMULATION_RETENTION_HOURS", "24")),
        statistics_retention_days=int(os.getenv("STATISTICS_RETENTION_DAYS", "7")),
        health_stale_signal_seconds=int(os.getenv("HEALTH_STALE_SIGNAL_SECONDS", "120")),
        stats_interval_seconds=int(os.getenv("STATS_INTERVAL_SECONDS", "60")),
        require_live_benchmarkable_output=env_bool("REQUIRE_LIVE_BENCHMARKABLE_OUTPUT", False),
        strict_production_mode=strict_production_mode,
        demo=DemoSettings(
            enabled=demo_enabled,
            scenario=scenario.slug,
            read_only=env_bool("DEMO_READ_ONLY", demo_enabled),
            label=demo_label,
            auto_connect=env_bool("DEMO_AUTO_CONNECT", demo_enabled),
            scenario_metadata={
                **get_scenario_metadata(scenario.slug),
                "label": demo_label,
            },
        ),
    )
