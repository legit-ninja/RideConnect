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
