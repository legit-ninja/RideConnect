import Link from "next/link";

import { ListingSummary } from "@/lib/api";

import { ListingImage } from "./ListingImage";
import { StarRating } from "./StarRating";
import { activityTypeLabel, ridingStyleLabel } from "./marketplaceLabels";
import styles from "./marketplace.module.css";

function formatPrice(price: string, friendOnly: boolean): string {
  const amount = Number(price);
  if (friendOnly && amount === 0) {
    return "Friends only";
  }
  return `$${amount.toFixed(2)}`;
}

interface ListingCardProps {
  listing: ListingSummary;
  rating?: number | null;
}

export function ListingCard({ listing, rating }: ListingCardProps) {
  const photo = listing.photo_urls[0];

  return (
    <Link href={`/l/${listing.slug}`} className={`${styles.card} cardHover`}>
      <ListingImage src={photo} alt={listing.animal_name} className={styles.cardImage} />
      <div className={styles.cardBody}>
        <div className={styles.cardTitle}>{listing.animal_name}</div>
        {listing.friend_only_allowed ? (
          <span className={styles.badgeFriendsOnly}>Friends only</span>
        ) : null}
        <div className={styles.cardMeta}>
          {activityTypeLabel(listing.activity_type)} · {listing.display_location}
        </div>
        {listing.riding_styles.length > 0 ? (
          <div className={styles.chipRow}>
            {listing.riding_styles.map((style) => (
              <span key={style} className={styles.chip}>
                {ridingStyleLabel(style)}
              </span>
            ))}
          </div>
        ) : null}
        {rating != null && rating > 0 ? (
          <StarRating value={rating} showValue />
        ) : null}
        {listing.availability ? (
          <div className={styles.cardMeta}>{listing.availability}</div>
        ) : null}
        <div className={styles.cardPrice}>
          {formatPrice(listing.price, listing.friend_only_allowed)}
        </div>
      </div>
    </Link>
  );
}
