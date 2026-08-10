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
  identity_id?: string;
  receiver_label?: string;
  latitude?: number;
  longitude?: number;
  altitude?: number;
  status?: string;
  last_seen?: number;
  updated_at?: number;
  capabilities?: string[];
  registry?: {
    sequence?: number;
    owner_lock_args?: string;
    metadata_hash?: string | null;
    out_point?: Record<string, JsonValue>;
  };
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
  receiver_registry_type_hash?: string;
  registry_discovery_live?: boolean;
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
