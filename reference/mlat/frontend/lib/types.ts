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
  data_source?: 'ckb_registry' | 'replay' | 'simulation' | 'runtime';
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
    deployment_transaction: string;
  };
  receiver: {
    receiver_identity: string;
    receiver_label: string;
  };
  lifecycle: RegistryLifecycleEvent[];
}

export interface PositionsResponse {
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
