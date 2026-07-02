"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { activityTypeLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  ListingDetail,
  User,
  createBooking,
  fetchCurrentUser,
  fetchListing,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function ListingDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [listing, setListing] = useState<ListingDetail | null>(null);
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchListing(id)
      .then(setListing)
      .catch(() => {
        setError("Listing not found.");
      });
  }, [id]);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setUser(null);
      return;
    }
    fetchCurrentUser(token)
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !listing) return;
    setBusy(true);
    setSubmitError(null);
    const form = new FormData(event.currentTarget);
    const scheduledAt = String(form.get("scheduled_at") || "");
    const note = String(form.get("note") || "");
    try {
      await createBooking(token, {
        listing_id: listing.id,
        scheduled_at: scheduledAt || undefined,
        note: note || undefined,
      });
      setSuccess(true);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setSubmitError(err.message);
      } else {
        setSubmitError("Unable to submit booking request.");
      }
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return (
      <div className={styles.detailPage}>
        <EmptyState
          title="Listing not found"
          description="This ride may have been removed or is no longer active."
          action={{ label: "Back to browse", href: "/listings" }}
        />
      </div>
    );
  }

  if (!listing) {
    return (
      <div className={styles.detailPage}>
        <LoadingState variant="cards" count={1} label="Loading listing" />
      </div>
    );
  }

  const photo = listing.photo_urls[0];
  const photoCount = listing.photo_urls.length;
  const price = Number(listing.price);
  const isFriendOnly = listing.friend_only_allowed;

  function renderBookingSection() {
    if (success) {
      return (
        <InlineAlert variant="success">
          Booking request submitted.{" "}
          <Link href="/rider/bookings">View my bookings</Link>
        </InlineAlert>
      );
    }

    if (user === undefined) {
      return <LoadingState variant="table" count={2} label="Loading account" />;
    }

    if (user === null) {
      return (
        <div className={styles.detailSection}>
          <p>Sign in to request a ride on this listing.</p>
          <Link href={`/login?next=/listings/${id}`} className={styles.button}>
            Sign in
          </Link>
        </div>
      );
    }

    if (!user.is_rider) {
      return (
        <InlineAlert variant="warning">
          Your account is not set up as a rider. Update your profile or register as a rider.
        </InlineAlert>
      );
    }

    if (user.is_minor) {
      return (
        <InlineAlert variant="warning">
          Minor accounts require a verified guardian before ride activity.
        </InlineAlert>
      );
    }

    if (user.verification_status !== "verified") {
      return <BlockedAction user={user} action="request rides" />;
    }

    if (isFriendOnly) {
      return (
        <div className={styles.detailSection}>
          <InlineAlert variant="info">
            This is a verified-friends-only ride. The owner must send you a friend invite and
            you must accept before you can request this ride.
          </InlineAlert>
          <form onSubmit={handleSubmit}>
            <label>
              Preferred date (optional)
              <input name="scheduled_at" type="datetime-local" />
            </label>
            <label>
              Note to owner (optional)
              <textarea name="note" rows={3} maxLength={2000} />
            </label>
            {submitError ? <InlineAlert variant="error">{submitError}</InlineAlert> : null}
            <button className={styles.button} type="submit" disabled={busy}>
              {busy ? "Submitting…" : "Request ride"}
            </button>
          </form>
        </div>
      );
    }

    return (
      <div className={styles.detailSection}>
        <form onSubmit={handleSubmit}>
          <label>
            Preferred date (optional)
            <input name="scheduled_at" type="datetime-local" />
          </label>
          <label>
            Note to owner (optional)
            <textarea name="note" rows={3} maxLength={2000} />
          </label>
          {submitError ? <InlineAlert variant="error">{submitError}</InlineAlert> : null}
          <button className={styles.button} type="submit" disabled={busy}>
            {busy ? "Submitting…" : "Request ride"}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className={styles.detailPage}>
      <p>
        <Link href="/listings">← Back to browse</Link>
      </p>
      {photo ? (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={photo} alt={listing.animal_name} className={styles.detailImage} />
          {photoCount > 1 ? (
            <p className={styles.cardMeta}>+{photoCount - 1} more photo(s)</p>
          ) : null}
        </>
      ) : null}
      <h1>{listing.animal_name}</h1>
      <p>
        {activityTypeLabel(listing.activity_type)}
        {listing.breed ? ` · ${listing.breed}` : ""}
        {isFriendOnly ? (
          <>
            {" "}
            <span className={styles.badgeFriendsOnly}>Friends only</span>
          </>
        ) : null}
      </p>
      <p>
        <strong>
          {isFriendOnly && price === 0 ? "Friends only" : `$${price.toFixed(2)}`}
        </strong>
      </p>
      <div className={styles.detailSection}>
        <h2>Location</h2>
        <p>{listing.address}</p>
      </div>
      {listing.availability ? (
        <div className={styles.detailSection}>
          <h2>Availability</h2>
          <p>{listing.availability}</p>
        </div>
      ) : null}
      {listing.description ? (
        <div className={styles.detailSection}>
          <h2>About</h2>
          <p>{listing.description}</p>
        </div>
      ) : null}
      <div className={styles.detailSection}>
        <h2>Request a ride</h2>
        {renderBookingSection()}
        <p className={`${styles.cardMeta} ${styles.cardMetaSpaced}`}>
          All bookings and payments stay on RideConnect for your safety.
        </p>
      </div>
    </div>
  );
}
