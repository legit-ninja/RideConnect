const TOKEN_KEY = "rideconnect_token";
const COOKIE_NAME =
  process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME ?? "pe_access_token";
const COOKIE_DOMAIN = process.env.NEXT_PUBLIC_AUTH_COOKIE_DOMAIN ?? "";

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const parts = document.cookie.split(";").map((p) => p.trim());
  for (const part of parts) {
    if (part.startsWith(`${name}=`)) {
      return decodeURIComponent(part.slice(name.length + 1));
    }
  }
  return null;
}

function writeCookie(token: string): void {
  if (typeof document === "undefined") return;
  const maxAge = 60 * 60; // match default JWT expiry
  const secure =
    typeof window !== "undefined" && window.location.protocol === "https:";
  let cookie = `${COOKIE_NAME}=${encodeURIComponent(token)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
  if (secure) cookie += "; Secure";
  if (COOKIE_DOMAIN) cookie += `; Domain=${COOKIE_DOMAIN}`;
  document.cookie = cookie;
}

function clearCookie(): void {
  if (typeof document === "undefined") return;
  let cookie = `${COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax`;
  if (COOKIE_DOMAIN) cookie += `; Domain=${COOKIE_DOMAIN}`;
  document.cookie = cookie;
}

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const fromCookie = readCookie(COOKIE_NAME);
  if (fromCookie) return fromCookie;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  writeCookie(token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  clearCookie();
}
