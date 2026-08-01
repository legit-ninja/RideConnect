import { getToken } from "@/lib/auth";
import { postFunnelEvent } from "@/lib/api";

const ANON_KEY = "pe_anon_id";

export function buildAuthQuery(params: {
  src?: string | null;
  ref?: string | null;
  next?: string | null;
}): string {
  const search = new URLSearchParams();
  if (params.src) search.set("src", params.src);
  if (params.ref) search.set("ref", params.ref);
  if (params.next) search.set("next", params.next);
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function postAuthPath(params: {
  src?: string | null;
  ref?: string | null;
  next?: string | null;
  isAdmin?: boolean;
}): string {
  if (params.next) return params.next;
  if (params.src === "public_listing" && params.ref) return `/l/${params.ref}`;
  if (params.src === "invite" && params.ref) return `/i/${params.ref}`;
  return params.isAdmin ? "/admin" : "/dashboard";
}

function getAnonId(): string | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    let id = localStorage.getItem(ANON_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(ANON_KEY, id);
    }
    return id;
  } catch {
    return undefined;
  }
}

export async function trackFunnel(
  businessUnit: "rides" | "shop",
  stage: string,
  options?: {
    path?: string;
    src?: string | null;
    ref?: string | null;
    payload?: Record<string, unknown>;
  },
): Promise<void> {
  try {
    const token = getToken();
    await postFunnelEvent(
      {
        business_unit: businessUnit,
        stage,
        anon_id: getAnonId(),
        src: options?.src ?? undefined,
        ref: options?.ref ?? undefined,
        path: options?.path ?? (typeof window !== "undefined" ? window.location.pathname : undefined),
        payload: options?.payload,
      },
      token,
    );
  } catch {
    // Funnel ingest should never block UX.
  }
}
