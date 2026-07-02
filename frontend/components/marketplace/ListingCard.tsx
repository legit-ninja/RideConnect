import Link from "next/link";

import { ListingSummary } from "@/lib/api";

import { activityTypeLabel } from "./marketplaceLabels";
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
}

export function ListingCard({ listing }: ListingCardProps) {
  const photo = listing.photo_urls[0];

  return (
    <Link href={`/listings/${listing.id}`} className={styles.card}>
      {photo ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={photo} alt={listing.animal_name} className={styles.cardImage} />
      ) : (
        <div className={styles.cardImage} />
      )}
      <div className={styles.cardBody}>
        <div className={styles.cardTitle}>{listing.animal_name}</div>
        {listing.friend_only_allowed ? (
          <span className={styles.badgeFriendsOnly}>Friends only</span>
        ) : null}
        <div className={styles.cardMeta}>
          {activityTypeLabel(listing.activity_type)} · {listing.address}
        </div>
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
