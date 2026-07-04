import { ImageResponse } from "next/og";

import { activityTypeLabel } from "@/components/marketplace/marketplaceLabels";
import type { PublicListing } from "@/lib/api";

export const runtime = "edge";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function loadListing(slug: string): Promise<PublicListing | null> {
  const response = await fetch(`${API_URL}/public/listings/${slug}`, {
    next: { revalidate: 300 },
  });
  if (!response.ok) return null;
  return (await response.json()) as PublicListing;
}

export async function GET(
  _request: Request,
  context: { params: Promise<{ slug: string }> },
) {
  const { slug } = await context.params;
  const listing = await loadListing(slug);

  if (!listing) {
    return new ImageResponse(
      (
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#1a1a1a",
            color: "#fff",
            fontSize: 48,
          }}
        >
          RideConnect
        </div>
      ),
      { width: 1200, height: 630 },
    );
  }

  const activity = activityTypeLabel(listing.activity_type);
  const photo = listing.photo_urls[0];

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: "#0f1419",
          color: "#f5f5f5",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        {photo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={photo}
            alt=""
            style={{ width: 420, height: "100%", objectFit: "cover" }}
          />
        ) : (
          <div style={{ width: 420, height: "100%", background: "#2a3441" }} />
        )}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: 48,
            gap: 16,
          }}
        >
          <div style={{ fontSize: 52, fontWeight: 700 }}>{listing.animal_name}</div>
          <div style={{ fontSize: 28, color: "#c9d1d9" }}>
            {activity} · {listing.display_location}
          </div>
          {listing.owner_verified ? (
            <div
              style={{
                marginTop: 8,
                padding: "8px 16px",
                background: "#1f6f4a",
                borderRadius: 8,
                fontSize: 22,
                alignSelf: "flex-start",
              }}
            >
              Verified owner
            </div>
          ) : null}
          <div style={{ marginTop: "auto", fontSize: 24, color: "#8b949e" }}>
            RideConnect
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      headers: {
        "Cache-Control": "public, max-age=3600, stale-while-revalidate=86400",
      },
    },
  );
}
