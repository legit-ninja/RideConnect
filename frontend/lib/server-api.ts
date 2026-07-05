/** Base URL for server-side fetches (SSR, route handlers). */
export function getServerApiUrl(): string {
  return (
    process.env.API_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  );
}
