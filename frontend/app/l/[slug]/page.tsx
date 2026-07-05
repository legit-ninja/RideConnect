import type { Metadata } from "next";
import Link from "next/link";

import { ListingImage } from "@/components/marketplace/ListingImage";
import { StarRating } from "@/components/marketplace/StarRating";
import { activityTypeLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import type { PublicListing } from "@/lib/api";
import { buildAuthQuery } from "@/lib/funnel";
import { getServerApiUrl } from "@/lib/server-api";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

async function loadListing(slug: string): Promise<PublicListing | null> {
  const response = await fetch(`${getServerApiUrl()}/public/listings/${slug}`, {
    next: { revalidate: 60 },
  });
  if (!response.ok) return null;
  return (await response.json()) as PublicListing;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const listing = await loadListing(slug);
  if (!listing) {
    return { title: "Listing not found — RideConnect" };
  }

  const activity = activityTypeLabel(listing.activity_type);
  const description = `${activity} with ${listing.animal_name} near ${listing.display_location}`;

  return {
    title: `${listing.animal_name} — RideConnect`,
    description,
    robots: listing.active ? { index: true, follow: true } : { index: false, follow: false },
    openGraph: {
      title: `${listing.animal_name} on RideConnect`,
      description,
      images: [`${SITE_URL}/api/og/${slug}`],
      url: `${SITE_URL}/l/${slug}`,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: listing.animal_name,
      description,
      images: [`${SITE_URL}/api/og/${slug}`],
    },
  };
}

function formatPrice(price: string | null): string {
  if (!price || Number(price) === 0) return "Contact for pricing";
  return `$${Number(price).toFixed(2)}`;
}

export default async function PublicListingPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const listing = await loadListing(slug);

  if (!listing) {
    return (
      <div className={styles.detailPage}>
        <h1>Listing not found</h1>
        <p>This ride may have been removed.</p>
        <Link href="/listings">Browse rides</Link>
      </div>
    );
  }

  const signupHref = `/register${buildAuthQuery({ src: "public_listing", ref: slug, next: `/l/${slug}` })}`;
  const primaryPhoto = listing.photo_urls[0];

  return (
    <div className={styles.publicListingPage}>
      {!listing.active ? (
        <div className={styles.banner} role="status">
          This listing is not currently accepting requests.
        </div>
      ) : null}

      <div className={styles.publicHero}>
        <ListingImage
          src={primaryPhoto}
          alt={listing.animal_name}
          className={styles.publicHeroImage}
        />
        {listing.photo_urls.length > 1 ? (
          <div className={styles.photoStrip}>
            {listing.photo_urls.slice(1, 5).map((url) => (
              <ListingImage key={url} src={url} alt="" className={styles.photoThumb} />
            ))}
          </div>
        ) : null}
      </div>

      <header className={styles.publicHeader}>
        <h1>{listing.animal_name}</h1>
        <div className={styles.chipRow}>
          <span className={styles.chip}>{activityTypeLabel(listing.activity_type)}</span>
          <span className={styles.chip}>{formatPrice(listing.price)}</span>
          {listing.breed ? <span className={styles.chip}>{listing.breed}</span> : null}
        </div>
      </header>

      <section className={styles.detailSection}>
        <h2>Approximate location</h2>
        <p>{listing.display_location}</p>
        <p className={styles.cardMeta}>
          Map shows an approximate area (within several miles) to protect owner privacy.
        </p>
      </section>

      {listing.review_count > 0 && listing.review_average !== null ? (
        <section className={styles.detailSection}>
          <h2>Reviews</h2>
          <StarRating value={listing.review_average} size="md" showValue />
          <p className={styles.cardMeta}>
            {listing.review_count} review
            {listing.review_count === 1 ? "" : "s"}
          </p>
        </section>
      ) : null}

      <section className={`${styles.detailSection} ${styles.ownerCard}`}>
        <h2>Owner</h2>
        <p>
          {listing.owner_first_name} {listing.owner_last_initial}.
          {listing.owner_verified ? (
            <span className={styles.verifiedBadge}> Verified owner</span>
          ) : null}
        </p>
        <p className={styles.cardMeta}>Member since {listing.owner_member_since}</p>
      </section>

      {listing.active ? (
        <section className={styles.publicCta}>
          <p>Sign up and verify your identity to request a ride on this listing.</p>
          <Link href={signupHref} className={styles.button}>
            Sign up to request a ride
          </Link>
          <p className={styles.cardMeta}>
            Already have an account?{" "}
            <Link href={`/login${buildAuthQuery({ src: "public_listing", ref: slug, next: `/l/${slug}` })}`}>
              Sign in
            </Link>
          </p>
        </section>
      ) : null}
    </div>
  );
}
