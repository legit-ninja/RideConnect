import { NextRequest, NextResponse } from "next/server";

/** On shop.* hosts, send bare `/` to the shop catalog. */
export function middleware(request: NextRequest) {
  const host = request.headers.get("host") ?? "";
  const isShopHost =
    host.startsWith("shop.") || host.startsWith("shop.dev.");
  if (isShopHost && request.nextUrl.pathname === "/") {
    const url = request.nextUrl.clone();
    url.pathname = "/shop";
    return NextResponse.rewrite(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/"],
};
