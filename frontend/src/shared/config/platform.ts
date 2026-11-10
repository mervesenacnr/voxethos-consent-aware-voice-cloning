/** Product identity and local API endpoint. */
export const platformConfig = Object.freeze({
  platformName: 'VoxEthos',
  tagline: 'Turkish speech research, transparent by design',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
});
