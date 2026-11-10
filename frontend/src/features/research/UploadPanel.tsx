import { useRef } from 'react';
import type { DragEvent } from 'react';
import { Activity, CheckCircle2, FileAudio, Loader2, ShieldCheck, Upload } from 'lucide-react';

interface UploadPanelProps {
  file: File | null;
  consentAcknowledged: boolean;
  busy: boolean;
  error: string | null;
  onSelect: (file: File | null) => void;
  onConsentChange: (checked: boolean) => void;
  onAnalyze: () => void;
}

function formatBytes(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadPanel({ file, consentAcknowledged, busy, error, onSelect, onConsentChange, onAnalyze }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (!busy) onSelect(event.dataTransfer.files.item(0));
  };

  return <section className="panel upload-panel" aria-labelledby="upload-title">
    <div className="section-heading">
      <div className="section-icon"><Upload size={18} /></div>
      <div>
        <p className="eyebrow">CONSENT-GATED INPUT</p>
        <h2 id="upload-title">Analyze a speech recording</h2>
        <p className="section-description">Upload a PCM16 WAV recording. Measurements are signal-level only; language is not verified and no model prediction is generated.</p>
      </div>
    </div>

    <div className={`dropzone ${file ? 'has-file' : ''} ${busy ? 'is-busy' : ''}`}
      onDragOver={(event) => event.preventDefault()}
      onDrop={handleDrop}
      onClick={() => !busy && inputRef.current?.click()}
      onKeyDown={(event) => { if (!busy && (event.key === 'Enter' || event.key === ' ')) inputRef.current?.click(); }}
      role="button" tabIndex={0} aria-label="Choose or drop a PCM16 WAV file">
      <input ref={inputRef} type="file" accept=".wav,audio/wav,audio/x-wav" hidden disabled={busy}
        onChange={(event) => onSelect(event.currentTarget.files?.item(0) ?? null)} />
      <div className="drop-icon">{busy ? <Loader2 className="spin" size={24} /> : file ? <FileAudio size={24} /> : <Upload size={24} />}</div>
      {file ? <>
        <strong className="file-name">{file.name}</strong>
        <span className="drop-hint">{formatBytes(file.size)} · selected locally</span>
        <button className="text-button" type="button" disabled={busy} onClick={(event) => { event.stopPropagation(); onSelect(null); }}>Remove file</button>
      </> : <>
        <strong>{busy ? 'Analyzing audio…' : 'Drop a WAV file here'}</strong>
        <span className="drop-hint">or click to browse · maximum 10 MiB</span>
        <span className="format-pill">PCM16 · mono or stereo · 8–96 kHz</span>
      </>}
    </div>

    <label className="consent-check">
      <input type="checkbox" checked={consentAcknowledged} disabled={busy} onChange={(event) => onConsentChange(event.currentTarget.checked)} />
      <span><ShieldCheck size={17} /><span>I am authorized to submit this recording for a single analysis request. I understand the prototype does not verify every speaker’s consent or identity.</span></span>
    </label>

    {error && <div className="error-banner" role="alert"><Activity size={16} /><span>{error}</span></div>}

    <div className="upload-actions">
      <p className="privacy-note"><CheckCircle2 size={15} /> The application does not persist audio after the request. Temporary upload buffering may occur.</p>
      <button className="primary-button" type="button" disabled={!file || !consentAcknowledged || busy} onClick={onAnalyze}>
        {busy ? <><Loader2 className="spin" size={17} /> Processing…</> : <><Activity size={17} /> Run signal analysis</>}
      </button>
    </div>
  </section>;
}
