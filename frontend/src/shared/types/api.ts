/** VoxEthos research API contracts. No model prediction fields are defined. */
export interface CapabilityStatus {
  status: string;
  description: string;
}

export interface AudioValidation {
  container: string;
  encoding: string;
  sample_rate_hz: number;
  channels: number;
  frame_count: number;
  duration_seconds: number;
  technical_quality_status: string;
  signal_present: boolean;
  peak_amplitude: number;
  rms_amplitude: number;
  active_window_ratio: number;
  silence_window_ratio: number;
  clipping_ratio: number;
  dc_offset: number;
  zero_crossing_rate: number;
  reason_codes: string[];
}

export interface SpeechSegment {
  start_seconds: number;
  end_seconds: number;
  duration_seconds: number;
}

export interface SpeechActivity {
  status: 'ACTIVITY_PRESENT' | 'INSUFFICIENT_ACTIVITY' | 'NO_ACTIVITY' | 'NOT_EVALUATED';
  estimator: string;
  total_frame_count: number;
  active_frame_count: number;
  active_ratio: number;
  estimated_duration_seconds: number;
  segments: SpeechSegment[];
  limitation: string;
}

export interface ProsodyPoint {
  time_seconds: number;
  rms: number;
  f0_hz: number | null;
}

export interface Prosody {
  status: 'EXPERIMENTAL_DSP';
  estimator: string;
  median_f0_hz: number | null;
  p10_f0_hz: number | null;
  p90_f0_hz: number | null;
  voiced_frame_count: number;
  total_frame_count: number;
  voiced_frame_ratio: number;
  pause_count_estimate: number;
  energy_track: ProsodyPoint[];
  limitation: string;
}

export interface VoxEthosAnalysis {
  project: 'VoxEthos';
  analysis_id: string;
  created_at: string;
  processing_ms: number;
  audio_validation: AudioValidation;
  speech_activity: SpeechActivity;
  prosody: Prosody;
  capabilities: Record<string, CapabilityStatus>;
  model_plan: {
    name: 'VoxEdge';
    status: 'PLANNED_NOT_LOADED';
    inference_performed: false;
  };
  privacy: {
    raw_audio_persisted_by_application: false;
    processing_scope: 'REQUEST_SCOPED';
    formal_privacy_evaluation: 'NOT_IMPLEMENTED';
    limitation: string;
  };
  consent: {
    acknowledged: true;
    version: string;
    scope: string;
    acknowledged_at: string;
    identity_or_rights_verified: false;
    persistent_record_created: false;
    limitation: string;
  };
  pipeline: Array<{ stage: string; status: string; duration_ms: number }>;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface CapabilityCatalogResponse {
  project: 'VoxEthos';
  capabilities: Record<string, CapabilityStatus>;
}
