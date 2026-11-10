/** Frontend session lifecycle contract reserved for API integration. */
export type SessionStatus = 'created' | 'validating' | 'processing' | 'completed' | 'failed';
export interface SessionRequest { prompt: string; client_session_id?: string }
export interface SessionResponse {
  session_id: string;
  status: SessionStatus;
  created_at: string;
  audio: Record<string, unknown> | null;
  analysis: Record<string, unknown> | null;
}
