import { Download, Info } from 'lucide-react';
import type { VoxEthosAnalysis } from '../../shared/types';

const capabilityLabels: Record<string, string> = {
  audio_validation: 'Audio validation', speech_activity: 'Signal activity estimate (heuristic)', prosody: 'Prosody features',
  turkish_asr: 'Turkish ASR', emotion_recognition: 'Emotion recognition', speaker_representation: 'Speaker representation',
  privacy_evaluation: 'Privacy evaluation', consent_management: 'Consent management', voxedge: 'VoxEdge model',
  expressive_voice_generation: 'Expressive voice generation',
};

function prettyStatus(value: string): string {
  return value.replace(/_/g, ' ').toLowerCase().replace(/(^|\s)\S/g, (letter: string) => letter.toUpperCase());
}

function downloadResult(result: VoxEthosAnalysis) {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `voxethos-analysis-${result.analysis_id}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function EnergyChart({ result }: { result: VoxEthosAnalysis }) {
  const points = result.prosody.energy_track;
  const coords = points.map((point, index) => {
    const x = points.length <= 1 ? 0 : (index / (points.length - 1)) * 100;
    const y = 96 - Math.min(1, Math.max(0, point.rms)) * 86;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(' ');
  return <div className="chart-wrap">
    {points.length ? <svg className="energy-chart" viewBox="0 0 100 100" role="img" aria-label="Measured RMS amplitude over the recording">
      <line x1="0" y1="10" x2="100" y2="10" /><line x1="0" y1="52" x2="100" y2="52" /><line x1="0" y1="96" x2="100" y2="96" />
      <polyline points={coords} />
    </svg> : <div className="chart-empty">No measurable feature frames were returned.</div>}
    <div className="chart-axis"><span>0 s</span><span>{result.audio_validation.duration_seconds.toFixed(2)} s</span></div>
    <p className="chart-caption">RMS amplitude · sampled from the uploaded waveform · not an emotion or quality score</p>
  </div>;
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return <div className="metric-card"><span className="metric-label">{label}</span><strong>{value}</strong><span className="metric-detail">{detail}</span></div>;
}

export function FeatureDashboard({ result }: { result: VoxEthosAnalysis }) {
  const audio = result.audio_validation;
  const prosody = result.prosody;
  const speech = result.speech_activity;
  const pitch = prosody.median_f0_hz === null ? '—' : `${prosody.median_f0_hz.toFixed(1)} Hz`;
  const pitchRange = prosody.p10_f0_hz === null || prosody.p90_f0_hz === null ? 'No stable pitch estimate' : `p10–p90: ${prosody.p10_f0_hz.toFixed(0)}–${prosody.p90_f0_hz.toFixed(0)} Hz`;

  return <section className="panel results-panel" aria-labelledby="results-title">
    <div className="results-heading">
      <div><p className="eyebrow">MEASURED SIGNAL OUTPUT</p><h2 id="results-title">Research analysis</h2><p className="section-description">Request {result.analysis_id} · {result.processing_ms} ms · {new Date(result.created_at).toLocaleString()}</p></div>
      <button className="secondary-button" type="button" onClick={() => downloadResult(result)}><Download size={16} /> Export JSON</button>
    </div>

    <div className="metric-grid">
      <Metric label="Recording duration" value={`${audio.duration_seconds.toFixed(2)} s`} detail={`${audio.sample_rate_hz.toLocaleString()} Hz · ${audio.channels} channel${audio.channels === 1 ? '' : 's'}`} />
      <Metric label="Median F0 estimate" value={pitch} detail={pitchRange} />
      <Metric label="Signal activity estimate" value={prettyStatus(speech.status)} detail={`${(speech.active_ratio * 100).toFixed(1)}% of measured frames passed energy/zero-crossing thresholds`} />
      <Metric label="Internal pause estimate" value={String(prosody.pause_count_estimate)} detail="Energy-threshold heuristic · not word timing" />
    </div>

    <div className="analysis-grid">
      <div className="subpanel"><div className="subpanel-heading"><div><h3>Signal envelope</h3><p>Observed RMS amplitude over time</p></div><span className="status-tag experimental">Experimental DSP</span></div><EnergyChart result={result} /></div>
      <div className="subpanel audio-facts">
        <div className="subpanel-heading"><div><h3>Input validation</h3><p>Technical measurements, not a classifier</p></div><span className="status-tag">{prettyStatus(audio.technical_quality_status)}</span></div>
        <dl>
          <div><dt>Container / encoding</dt><dd>{audio.container} · {audio.encoding}</dd></div>
          <div><dt>Frames</dt><dd>{audio.frame_count.toLocaleString()}</dd></div>
          <div><dt>Peak amplitude</dt><dd>{audio.peak_amplitude.toFixed(3)}</dd></div>
          <div><dt>RMS amplitude</dt><dd>{audio.rms_amplitude.toFixed(3)}</dd></div>
          <div><dt>Estimated activity duration</dt><dd>{speech.estimated_duration_seconds.toFixed(2)} s</dd></div>
        </dl>
      </div>
    </div>

    <div className="notice"><Info size={17} /><p><strong>Interpretation boundary.</strong> F0, RMS and activity are deterministic signal-processing estimates. They are not validated Turkish ASR, emotion, identity, anti-spoofing, or forensic findings. VoxEdge was not loaded and produced no prediction.</p></div>

    <div className="capability-section">
      <div className="subpanel-heading"><div><h3>Research capability status</h3><p>Implemented work is separated from planned and unfinished ML.</p></div><span className="status-tag planned">VoxEdge · planned</span></div>
      <div className="capability-grid">
        {Object.entries(result.capabilities).map(([key, capability]) => <article className="capability-card" key={key}>
          <div className="capability-title"><strong>{capabilityLabels[key] ?? key.replace(/_/g, ' ')}</strong><span className={`status-tag ${capability.status === 'NOT_IMPLEMENTED' || capability.status === 'PLANNED_NOT_LOADED' ? 'planned' : capability.status === 'EXPERIMENTAL_DSP' ? 'experimental' : ''}`}>{prettyStatus(capability.status)}</span></div>
          <p>{capability.description}</p>
        </article>)}
      </div>
    </div>

    <div className="footnote-grid">
      <p><strong>Consent:</strong> request-level acknowledgement only. It is not identity verification, persistent consent evidence, or proof of rights.</p>
      <p><strong>Privacy:</strong> the application does not save uploaded audio. Framework-level temporary upload buffering may still occur; formal privacy evaluation is not implemented.</p>
    </div>
  </section>;
}
