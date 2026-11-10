import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { createServer } from 'vite';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let server;
let ApiClient;
let ApiError;
let FeatureDashboard;
const originalFetch = globalThis.fetch;

before(async () => {
  server = await createServer({ configFile: false, server: { middlewareMode: true }, appType: 'custom' });
  ({ ApiClient, ApiError } = await server.ssrLoadModule('/src/shared/services/apiClient.ts'));
  ({ FeatureDashboard } = await server.ssrLoadModule('/src/features/research/FeatureDashboard.tsx'));
});
after(async () => {
  globalThis.fetch = originalFetch;
  await server?.close();
});

function validAnalysis() {
  return {
    project: 'VoxEthos', analysis_id: 'example', created_at: '2026-01-01T00:00:00Z', processing_ms: 42,
    audio_validation: {
      container: 'WAV', encoding: 'PCM16', sample_rate_hz: 16000, channels: 1, frame_count: 16000,
      duration_seconds: 1, technical_quality_status: 'VALID', signal_present: true, peak_amplitude: 0.5,
      rms_amplitude: 0.2, active_window_ratio: 0.8, silence_window_ratio: 0.2, clipping_ratio: 0,
      dc_offset: 0, zero_crossing_rate: 0.1, reason_codes: [],
    },
    speech_activity: {
      status: 'ACTIVITY_PRESENT', estimator: 'energy_and_zero_crossing_heuristic', total_frame_count: 1,
      active_frame_count: 1, active_ratio: 1, estimated_duration_seconds: 1,
      segments: [{ start_seconds: 0, end_seconds: 1, duration_seconds: 1 }], limitation: 'estimate',
    },
    prosody: {
      status: 'EXPERIMENTAL_DSP', estimator: 'windowed_autocorrelation_v1', median_f0_hz: null,
      p10_f0_hz: null, p90_f0_hz: null, voiced_frame_count: 0, total_frame_count: 1,
      voiced_frame_ratio: 0, pause_count_estimate: 0,
      energy_track: [{ time_seconds: 0, rms: 0.2, f0_hz: null }], limitation: 'estimate',
    },
    capabilities: { prosody: { status: 'EXPERIMENTAL_DSP', description: 'estimate' } },
    model_plan: { name: 'VoxEdge', status: 'PLANNED_NOT_LOADED', inference_performed: false },
    privacy: { raw_audio_persisted_by_application: false, processing_scope: 'REQUEST_SCOPED', formal_privacy_evaluation: 'NOT_IMPLEMENTED', limitation: 'estimate' },
    consent: { acknowledged: true, version: '1', scope: 'research', acknowledged_at: '2026-01-01T00:00:00Z', identity_or_rights_verified: false, persistent_record_created: false, limitation: 'estimate' },
    pipeline: [{ stage: 'validate', status: 'COMPLETE', duration_ms: 1 }],
  };
}

async function analyze(payload) {
  globalThis.fetch = async () => new Response(JSON.stringify(payload), { status: 200, headers: { 'Content-Type': 'application/json' } });
  return new ApiClient('http://localhost').analyze(new File(['audio'], 'private.wav', { type: 'audio/wav' }), true);
}

test('a valid analysis is accepted and renders the dashboard', async () => {
  const result = await analyze(validAnalysis());
  assert.match(renderToStaticMarkup(createElement(FeatureDashboard, { result })), /Research analysis/);
});

test('a valid pitched analysis renders numeric pitch and an empty energy track', async () => {
  const payload = validAnalysis();
  payload.prosody.median_f0_hz = 130;
  payload.prosody.p10_f0_hz = 100;
  payload.prosody.p90_f0_hz = 170;
  payload.prosody.energy_track = [];
  const result = await analyze(payload);
  const html = renderToStaticMarkup(createElement(FeatureDashboard, { result }));
  assert.match(html, /130\.0 Hz/);
  assert.match(html, /No measurable feature frames/);
});

test('rejects a shallow success response instead of letting the dashboard crash', async () => {
  const payload = validAnalysis();
  payload.prosody = {};
  await assert.rejects(analyze(payload), (error) => error instanceof ApiError && error.code === 'MALFORMED_RESPONSE');
});

for (const [name, mutate] of [
  ['missing audio duration', (value) => { delete value.audio_validation.duration_seconds; }],
  ['wrong audio number type', (value) => { value.audio_validation.sample_rate_hz = '16000'; }],
  ['missing speech status', (value) => { delete value.speech_activity.status; }],
  ['missing pitch value', (value) => { delete value.prosody.median_f0_hz; }],
  ['non-array energy track', (value) => { value.prosody.energy_track = {}; }],
  ['malformed energy point', (value) => { value.prosody.energy_track = [{ time_seconds: 0, rms: 'loud', f0_hz: null }]; }],
  ['malformed speech segment', (value) => { value.speech_activity.segments = [null]; }],
  ['malformed capability entry', (value) => { value.capabilities.prosody = null; }],
  ['array instead of capability map', (value) => { value.capabilities = []; }],
  ['missing privacy fields', (value) => { value.privacy = {}; }],
  ['missing consent fields', (value) => { value.consent = {}; }],
  ['malformed pipeline entry', (value) => { value.pipeline = [null]; }],
  ['non-numeric processing time', (value) => { value.processing_ms = '42'; }],
]) {
  test(`rejects ${name} in a success response`, async () => {
    const payload = validAnalysis();
    mutate(payload);
    await assert.rejects(analyze(payload), (error) => error instanceof ApiError && error.code === 'MALFORMED_RESPONSE');
  });
}

test('rejects a success response with the wrong model name', async () => {
  const payload = validAnalysis();
  payload.model_plan.name = 'Other';
  await assert.rejects(analyze(payload), (error) => error instanceof ApiError && error.code === 'MALFORMED_RESPONSE');
});

test('preserves the explicit unexpected-model-state error', async () => {
  const payload = validAnalysis();
  payload.model_plan.inference_performed = true;
  await assert.rejects(analyze(payload), (error) => error instanceof ApiError && error.code === 'UNEXPECTED_MODEL_STATE');
});
