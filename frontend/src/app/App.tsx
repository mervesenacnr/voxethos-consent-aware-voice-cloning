import { useEffect, useState } from 'react';
import { Activity, AudioLines, CheckCircle2, CircleHelp, CloudOff, ShieldCheck } from 'lucide-react';
import { UploadPanel } from '../features/research/UploadPanel';
import { FeatureDashboard } from '../features/research/FeatureDashboard';
import { apiClient, ApiError } from '../shared/services/apiClient';
import { platformConfig } from '../shared/config/platform';
import type { VoxEthosAnalysis } from '../shared/types';

const MAX_FILE_BYTES = 10 * 1024 * 1024;

type Connection = 'checking' | 'online' | 'offline';

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [consentAcknowledged, setConsentAcknowledged] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VoxEthosAnalysis | null>(null);
  const [connection, setConnection] = useState<Connection>('checking');

  useEffect(() => {
    let active = true;
    apiClient.health().then(() => { if (active) setConnection('online'); }).catch(() => { if (active) setConnection('offline'); });
    return () => { active = false; };
  }, []);

  const selectFile = (selected: File | null) => {
    setError(null);
    setResult(null);
    setConsentAcknowledged(false);
    if (!selected) { setFile(null); return; }
    if (!selected.name.toLowerCase().endsWith('.wav')) {
      setFile(null);
      setError('UNSUPPORTED_AUDIO · Choose a WAV file. The server will validate its actual encoding.');
      return;
    }
    if (selected.size > MAX_FILE_BYTES) {
      setFile(null);
      setError('AUDIO_TOO_LARGE · The prototype accepts uploads up to 10 MiB.');
      return;
    }
    setFile(selected);
  };

  const analyze = async () => {
    if (!file || !consentAcknowledged || busy) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const analysis = await apiClient.analyze(file, consentAcknowledged);
      setResult(analysis);
      setConnection('online');
    } catch (cause) {
      const apiError = cause instanceof ApiError ? cause : new ApiError('SERVER_ERROR', 'The request could not be completed.');
      setError(`${apiError.code} · ${apiError.message}`);
      if (apiError.code === 'SERVER_ERROR') setConnection('offline');
    } finally {
      setBusy(false);
    }
  };

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="#top" aria-label="VoxEthos home"><span className="brand-icon"><AudioLines size={20} /></span><span><strong>{platformConfig.platformName}</strong><small>CONSENT-AWARE SPEECH RESEARCH</small></span></a>
      <div className="connection" aria-live="polite"><span className={`connection-dot ${connection}`} />{connection === 'checking' ? 'Checking API' : connection === 'online' ? 'API connected' : 'API unavailable'}</div>
    </header>

    <main id="top" className="page-content">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">TURKISH SPEECH · RESEARCH PROTOTYPE</p>
          <h1>Listen to the signal.<br /><span>Be honest about the model.</span></h1>
          <p className="hero-text">A transparent starting point for Turkish speech research: validated PCM16 WAV input, measurable signal features, and a clear boundary between working software and unfinished ML.</p>
          <div className="hero-points"><span><CheckCircle2 size={16} /> Real waveform-derived features</span><span><ShieldCheck size={16} /> Per-request consent gate</span><span><CircleHelp size={16} /> No model score is fabricated</span></div>
        </div>
        <aside className="model-card"><div className="model-card-top"><span className="model-symbol"><Activity size={20} /></span><span className="status-tag planned">PLANNED</span></div><p className="eyebrow">FUTURE ML MODEL</p><h2>VoxEdge</h2><p>Planned model family for later, independently evaluated Turkish speech tasks.</p><div className="model-divider" /><strong>Not loaded · No inference · No prediction</strong></aside>
      </section>

      <UploadPanel file={file} consentAcknowledged={consentAcknowledged} busy={busy} error={error} onSelect={selectFile} onConsentChange={setConsentAcknowledged} onAnalyze={analyze} />
      {result ? <FeatureDashboard result={result} /> : <section className="empty-state"><div className="empty-icon">{connection === 'offline' ? <CloudOff size={21} /> : <Activity size={21} />}</div><div><strong>{connection === 'offline' ? 'Connect the local API to begin' : 'Your measured results will appear here'}</strong><p>Nothing is simulated. Upload a supported sample and acknowledge the request scope to run the analysis.</p></div></section>}

      <footer className="footer"><span>VoxEthos · {platformConfig.tagline}</span><span>Research prototype · No model predictions</span></footer>
    </main>
  </div>;
}
