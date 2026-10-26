export type StatusTone = 'healthy' | 'attention' | 'replay' | 'failure' | 'selection' | 'neutral' | 'trust';

export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

export interface InvestigationFact {
  label: string;
  value: string;
  mono?: boolean;
  tone?: StatusTone;
}

export interface InvestigationEvent {
  title: string;
  detail: string;
  tone?: StatusTone;
  meta?: string;
}

export interface InvestigationCard {
  title: string;
  detail: string;
  state?: string;
  tone?: StatusTone;
}

export interface InvestigationAction {
  label: string;
  href: string;
  tone?: 'primary' | 'secondary';
}

export interface InvestigationDockState {
  entityType: 'overview' | 'aircraft' | 'receiver' | 'pipeline' | 'metrics' | 'environment' | 'settings' | 'system';
  title: string;
  subtitle?: string;
  statusLabel?: string;
  statusTone?: StatusTone;
  facts?: InvestigationFact[];
  timeline?: InvestigationEvent[];
  evidence?: InvestigationCard[];
  actions?: InvestigationAction[];
}

export interface Position {
  data_provenance?: 'SYNTHETIC' | 'HISTORICAL_REPLAY' | 'LIVE' | 'UNKNOWN';
  source_id?: string;
  timestamp_ns?: string;
  source_timestamp_ns?: string;
  correlation_id?: string;
  receiver_geometry?: Array<{ receiver_id: string; latitude: number; longitude: number; altitude_m: number }>;
  aircraft_id: string;
  timestamp?: number;
  latitude?: number;
  longitude?: number;
  altitude?: number;
  uncertainty?: number;
  num_receivers?: number;
  position?: {
    latitude?: number;
    longitude?: number;
    altitude?: number;
  };
  quality?: {
    score?: number;
    bucket?: string;
    uncertainty_m?: number;
    confidence_calibrated?: boolean;
    interpretation?: string;
  };
  correlation?: {
    receiver_ids?: string[];
    receiver_count?: number;
    time_span_s?: number;
  };
  solver?: {
    method?: string;
    residual_m?: number;
    iterations?: number;
  };
}

export interface Receiver {
  receiver_id: string;
  receiver_identity?: string | null;
  receiver_label?: string;
  data_source?: 'ckb_registry' | 'replay' | 'simulation' | 'runtime' | 'historical_replay';
  qualification?: { state?: 'QUALIFIED' | 'UNQUALIFIED' | 'REJECTED'; received_at?: number; reason?: string; action?: string; clock_source?: string; clock_uncertainty_ns?: number; maximum_clock_uncertainty_ns?: number; data_provenance?: string };
  latitude?: number;
  longitude?: number;
  altitude?: number;
  status?: string;
  last_seen?: number;
  updated_at?: string;
  capabilities?: string[];
  registry?: {
    sequence?: string;
    updated_at?: string;
    owner_lock_args?: string;
    owner_lock?: {
      code_hash: string;
      hash_type: string;
      args: string;
    };
    metadata_hash?: string | null;
    out_point?: Record<string, JsonValue>;
    stream_endpoint?: string;
    stream_protocol?: string;
    stream_format?: string;
  };
}

export interface RegistryLifecycleEvent {
  action: 'create' | 'update' | 'transfer' | 'revoke';
  sequence: string;
  status: string;
  updated_at: string;
  owner_lock_args: string;
  transaction_hash: string;
  block_number?: string;
  explorer_url: string;
}

export interface RegistryEvidenceData {
  schema_version: number;
  source: 'saved_testnet_evidence';
  live_query: boolean;
  network: string;
  status: string;
  generated_at: string;
  private_keys_included: boolean;
  contract: {
    code_hash: string;
    hash_type: string;
    deployment_transaction: string;
  };
  receiver: {
    receiver_identity: string;
    receiver_label: string;
  };
  lifecycle: RegistryLifecycleEvent[];
}

export interface PositionsResponse {
  data_provenance?: Position['data_provenance'];
  positions: Position[];
  count?: number;
  time_window_seconds?: number;
}

export interface ReceiversResponse {
  receivers: Receiver[];
  count?: number;
}

export interface ModeData {
  mode?: string;
  runtime_status?: string;
  demo_mode?: boolean;
  demo_label?: string;
  simulation_mode?: boolean;
  synthetic_feed_mode?: boolean;
  strict_production_mode?: boolean;
  benchmarkable_output?: boolean;
  websocket_available?: boolean;
  configured_transport?: string;
  ckb_network?: string;
  receiver_registry_type_hash?: string;
  receiver_registry_hash_type?: string;
  registry_code_immutable?: boolean;
  registry_discovery_live?: boolean;
  registry_last_refresh_at?: number;
  registry_refresh_error?: string | null;
  registry_quarantined_identity_count?: number;
  evidence_mode?: string;
  [key: string]: unknown;
}

export interface HealthData {
  components?: Array<{ component: string; status: 'HEALTHY' | 'DEGRADED' | 'FAILED' | 'NOT CONFIGURED'; reason: string; action: string }>;
  status?: string;
  freshness?: {
    last_signal_age_s?: number;
    last_store_age_s?: number;
  };
  runtime?: Record<string, JsonValue>;
  database?: Record<string, JsonValue>;
  broadcaster?: Record<string, JsonValue>;
  [key: string]: unknown;
}

export interface ShellSnapshot {
  modeData: ModeData | null;
  healthData: HealthData | null;
  aircraftData: { aircraft?: string[]; count?: number } | null;
  receiverData: ReceiversResponse | null;
}

export interface ReadinessData {
  ready?: boolean;
  dimensions?: Record<string, Record<string, JsonValue>>;
  external_benchmark?: Record<string, JsonValue>;
  not_yet_proven?: Record<string, JsonValue>;
  [key: string]: unknown;
}

export interface PipelineStageData {
  id: string;
  label: string;
  status: string;
  detail?: string;
  metrics?: Record<string, JsonValue>;
}

export interface PipelineData {
  stages?: PipelineStageData[];
  blockers?: string[];
  live_evidence_ready?: boolean;
  pipeline_operational?: boolean;
  provenance?: Record<string, JsonValue>;
  benchmark?: Record<string, JsonValue>;
  [key: string]: unknown;
}

export interface MetricsData {
  current?: Record<string, number | string | boolean | null>;
  history?: Array<Record<string, number | string | boolean | null>>;
  sample_count?: number;
  reliability?: Record<string, number | string | boolean | null>;
  provenance?: Record<string, JsonValue>;
  [key: string]: unknown;
}

export interface SolverBenchmarkMetricSummary {
  count?: number;
  minimum?: number;
  median: number;
  p95: number;
  mean?: number;
  maximum: number;
}

export interface SolverBenchmarkEvent {
  event_id: string;
  data_source: 'SIMULATION' | 'HISTORICAL_RECORDING';
  is_live: false;
  solved: boolean;
  errors_m: {
    horizontal?: number;
    vertical?: number;
    three_dimensional?: number;
  } | null;
  acceptance?: {
    passed: boolean;
    maximum_3d_error_m: number;
    criterion: string;
  };
  ground_truth: {
    latitude: number;
    longitude: number;
    altitude_m: number;
  };
  receiver_geometry: Array<{
    receiver_id: string;
    latitude: number;
    longitude: number;
    altitude_m: number;
  }>;
  source?: {
    dataset?: string;
    license?: string;
    original_dataset?: string;
    upstream_repository?: string;
    limitations?: string[];
  };
}

export interface SolverBenchmarkReport {
  schema_version: 1;
  benchmark_id: 'compact-public-solver-v1' | 'compact-public-solver-v2';
  claim_scope: 'solver_only';
  is_live: false;
  synthetic_control: SolverBenchmarkEvent;
  published_event: SolverBenchmarkEvent;
  compact_dataset: {
    data_source: 'HISTORICAL_RECORDING';
    is_live: false;
    event_counts: {
      total: number;
      solved: number;
      unsolved: number;
    };
    solve_rate: number;
    residual_m?: SolverBenchmarkMetricSummary;
    failure_categories?: Record<string, number>;
    iterations?: { successful?: SolverBenchmarkMetricSummary; definition?: string };
    accuracy_m: {
      horizontal: SolverBenchmarkMetricSummary | null;
      vertical: SolverBenchmarkMetricSummary | null;
      three_dimensional: SolverBenchmarkMetricSummary | null;
    };
    source: {
      source_id: string;
      license: string;
      original_dataset?: string;
      upstream_repository?: string;
      upstream_version?: string;
      limitations: string[];
    };
  };
  interpretation: {
    solver_numeric_behavior_measured: boolean;
    production_pipeline_validated: boolean;
    registry_identity_validated: boolean;
    live_operation_validated: boolean;
    clock_attestation_validated?: boolean;
    physical_receiver_claims_validated?: boolean;
  };
}
