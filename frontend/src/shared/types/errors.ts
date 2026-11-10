/** Structured API errors returned by the backend boundary. */
export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | unknown[] | null;
}
export interface ApiErrorResponse { error: ApiErrorDetail }
