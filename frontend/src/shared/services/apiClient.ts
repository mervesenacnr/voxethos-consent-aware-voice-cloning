import { platformConfig } from '../config/platform';
import type { CapabilityCatalogResponse, HealthResponse, VoxEthosAnalysis } from '../types';

export class ApiError extends Error {
  constructor(public readonly code: string, message: string, public readonly status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isNullableNumber(value: unknown): boolean {
  return value === null || isFiniteNumber(value);
}

function isProsody(value: unknown): boolean {
  return isRecord(value)
    && value.status === 'EXPERIMENTAL_DSP'
    && typeof value.estimator === 'string'
    && isNullableNumber(value.median_f0_hz)
    && isNullableNumber(value.p10_f0_hz)
    && isNullableNumber(value.p90_f0_hz)
    && isFiniteNumber(value.voiced_frame_count)
    && isFiniteNumber(value.total_frame_count)
    && isFiniteNumber(value.voiced_frame_ratio)
    && isFiniteNumber(value.pause_count_estimate)
    && Array.isArray(value.energy_track)
    && value.energy_track.every((point: unknown) => isRecord(point)
      && isFiniteNumber(point.time_seconds)
      && isFiniteNumber(point.rms)
      && isNullableNumber(point.f0_hz))
    && typeof value.limitation === 'string';
}

function isAudioValidation(value: unknown): boolean {
  return isRecord(value)
    && typeof value.container === 'string'
    && typeof value.encoding === 'string'
    && isFiniteNumber(value.sample_rate_hz)
    && isFiniteNumber(value.channels)
    && isFiniteNumber(value.frame_count)
    && isFiniteNumber(value.duration_seconds)
    && typeof value.technical_quality_status === 'string'
    && typeof value.signal_present === 'boolean'
    && isFiniteNumber(value.peak_amplitude)
    && isFiniteNumber(value.rms_amplitude)
    && isFiniteNumber(value.active_window_ratio)
    && isFiniteNumber(value.silence_window_ratio)
    && isFiniteNumber(value.clipping_ratio)
    && isFiniteNumber(value.dc_offset)
    && isFiniteNumber(value.zero_crossing_rate)
    && Array.isArray(value.reason_codes)
    && value.reason_codes.every((code: unknown) => typeof code === 'string');
}

function isSpeechActivity(value: unknown): boolean {
  return isRecord(value)
    && ['ACTIVITY_PRESENT', 'INSUFFICIENT_ACTIVITY', 'NO_ACTIVITY', 'NOT_EVALUATED'].includes(value.status as string)
    && typeof value.estimator === 'string'
    && isFiniteNumber(value.total_frame_count)
    && isFiniteNumber(value.active_frame_count)
    && isFiniteNumber(value.active_ratio)
    && isFiniteNumber(value.estimated_duration_seconds)
    && Array.isArray(value.segments)
    && value.segments.every((segment: unknown) => isRecord(segment)
      && isFiniteNumber(segment.start_seconds)
      && isFiniteNumber(segment.end_seconds)
      && isFiniteNumber(segment.duration_seconds))
    && typeof value.limitation === 'string';
}

function isCapabilities(value: unknown): boolean {
  return isRecord(value) && Object.values(value).every((capability: unknown) => isRecord(capability)
    && typeof capability.status === 'string' && typeof capability.description === 'string');
}

function isPrivacy(value: unknown): boolean {
  return isRecord(value) && value.raw_audio_persisted_by_application === false
    && value.processing_scope === 'REQUEST_SCOPED'
    && value.formal_privacy_evaluation === 'NOT_IMPLEMENTED'
    && typeof value.limitation === 'string';
}

function isConsent(value: unknown): boolean {
  return isRecord(value) && value.acknowledged === true
    && typeof value.version === 'string' && typeof value.scope === 'string'
    && typeof value.acknowledged_at === 'string'
    && value.identity_or_rights_verified === false && value.persistent_record_created === false
    && typeof value.limitation === 'string';
}

function isPipeline(value: unknown): boolean {
  return Array.isArray(value) && value.every((step: unknown) => isRecord(step)
    && typeof step.stage === 'string' && typeof step.status === 'string' && isFiniteNumber(step.duration_ms));
}

function parseAnalysis(value: unknown): VoxEthosAnalysis {
  if (!isRecord(value)
    || value.project !== 'VoxEthos'
    || typeof value.analysis_id !== 'string'
    || typeof value.created_at !== 'string'
    || !isFiniteNumber(value.processing_ms)
    || !isAudioValidation(value.audio_validation)
    || !isSpeechActivity(value.speech_activity)
    || !isProsody(value.prosody)
    || !isCapabilities(value.capabilities)
    || !isRecord(value.model_plan)
    || !isPrivacy(value.privacy)
    || !isConsent(value.consent)
    || !isPipeline(value.pipeline)) {
    throw new ApiError('MALFORMED_RESPONSE', 'The research API returned an invalid response.');
  }
  if (value.model_plan.status !== 'PLANNED_NOT_LOADED' || value.model_plan.inference_performed !== false) {
    throw new ApiError('UNEXPECTED_MODEL_STATE', 'The API did not return the declared non-inference prototype state.');
  }
  if (value.model_plan.name !== 'VoxEdge') {
    throw new ApiError('MALFORMED_RESPONSE', 'The research API returned an invalid response.');
  }
  return value as unknown as VoxEthosAnalysis;
}

export class ApiClient {
  private readonly baseUrl: string;

  constructor(baseUrl = platformConfig.apiBaseUrl) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  }

  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async capabilities(): Promise<CapabilityCatalogResponse> {
    return this.request<CapabilityCatalogResponse>('/api/v1/capabilities');
  }

  async analyze(audio: File, consentAcknowledged: boolean): Promise<VoxEthosAnalysis> {
    const form = new FormData();
    // Use a neutral name so a user's local filename is not needlessly sent to the API.
    form.append('audio', audio, 'upload.wav');
    form.append('consent_acknowledged', String(consentAcknowledged));
    return this.request<VoxEthosAnalysis>('/api/v1/analyze', { method: 'POST', body: form }, parseAnalysis);
  }

  private async request<T>(path: string, init?: RequestInit, parse: (value: unknown) => T = (value) => value as T): Promise<T> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, init);
    } catch {
      throw new ApiError('SERVER_ERROR', 'The VoxEthos API is unavailable. Start the local backend and try again.');
    }
    if (!response.ok) {
      let payload: { error?: { code?: string; message?: string } } = {};
      try {
        payload = await response.json();
      } catch { /* use the status fallback */ }
      throw new ApiError(payload.error?.code ?? `HTTP_${response.status}`, payload.error?.message ?? 'The request failed.', response.status);
    }
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      throw new ApiError('MALFORMED_RESPONSE', 'The VoxEthos API returned invalid JSON.', response.status);
    }
    return parse(payload);
  }
}

export const apiClient = new ApiClient();
