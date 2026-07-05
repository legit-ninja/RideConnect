"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { ListingImage } from "@/components/marketplace/ListingImage";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { activityTypeLabel, ridingStyleLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  AvailabilitySlot,
  ListingDetail,
  User,
  createBooking,
  fetchCurrentUser,
  fetchListing,
  fetchListingOpenSlots,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

const INQUIRY_NOTE_MIN_LENGTH = 10;

function formatSlotRange(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  return `${startDate.toLocaleDateString()} · ${startDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })} – ${endDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
}

export default function ListingDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;
  const slotIdFromQuery = searchParams.get("slot");
  const [listing, setListing] = useState<ListingDetail | null>(null);
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [openSlots, setOpenSlots] = useState<AvailabilitySlot[] | null>(null);
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(slotIdFromQuery);
  const [showContactForm, setShowContactForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const token = getToken();
    fetchListing(id, token)
      .then(setListing)
      .catch(() => {
        setError("Listing not found.");
      });
  }, [id]);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setOpenSlots(null);
      return;
    }
    fetchCurrentUser(token)
      .then((currentUser) => {
        setUser(currentUser);
        if (currentUser.is_rider && currentUser.verification_status === "verified") {
          return fetchListingOpenSlots(token, id).then(setOpenSlots);
        }
        setOpenSlots(null);
        return undefined;
      })
      .catch(() => {
        setUser(null);
        setOpenSlots(null);
      });
  }, [id]);

  useEffect(() => {
    if (slotIdFromQuery) {
      setSelectedSlotId(slotIdFromQuery);
      setShowContactForm(false);
    }
  }, [slotIdFromQuery]);

  async function handleSlotBooking(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !listing || !selectedSlotId) return;
    setBusy(true);
    setSubmitError(null);
    const note = String(new FormData(event.currentTarget).get("note") || "");
    try {
      await createBooking(token, {
        listing_id: listing.id,
        availability_slot_id: selectedSlotId,
        note: note || undefined,
      });
      setSuccess(true);
    } catch (err: unknown) {
      setSubmitError(err instanceof ApiError ? err.message : "Unable to submit booking request.");
    } finally {
      setBusy(false);
    }
  }

  async function handleContactSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !listing) return;
    const note = String(new FormData(event.currentTarget).get("note") || "").trim();
    if (note.length < INQUIRY_NOTE_MIN_LENGTH) {
      setSubmitError(`Please enter at least ${INQUIRY_NOTE_MIN_LENGTH} characters.`);
      return;
    }
    setBusy(true);
    setSubmitError(null);
    try {
      await createBooking(token, {
        listing_id: listing.id,
        note,
      });
      setSuccess(true);
    } catch (err: unknown) {
      setSubmitError(err instanceof ApiError ? err.message : "Unable to send message.");
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
  const hasOpenSlots = openSlots !== null && openSlots.length > 0;

  function renderBookingSection() {
    if (success) {
      return (
        <InlineAlert variant="success">
          Your request was submitted on RideConnect.{" "}
          <Link href="/rider/bookings">View my bookings</Link>
        </InlineAlert>
      );
    }

    if (user === undefined || (user?.is_rider && openSlots === null && user.verification_status === "verified")) {
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

    const friendNotice = isFriendOnly ? (
      <InlineAlert variant="info">
        This is a verified-friends-only ride. The host must send you a friend invite and you
        must accept before you can request this ride.
      </InlineAlert>
    ) : null;

    if (showContactForm || !hasOpenSlots) {
      return (
        <div className={styles.detailSection}>
          {friendNotice}
          {!hasOpenSlots ? (
            <InlineAlert variant="info">
              No times available right now — send a message and the host will get back to you on
              the platform.{" "}
              <Link href="/calendar">Browse the calendar</Link> for other listings.
            </InlineAlert>
          ) : (
            <p className={styles.cardMeta}>
              Ask a question before booking, or{" "}
              <button
                type="button"
                className={styles.buttonSecondary}
                onClick={() => setShowContactForm(false)}
              >
                return to available times
              </button>
              .
            </p>
          )}
          <form onSubmit={handleContactSubmit}>
            <label>
              Message to host (required)
              <textarea
                name="note"
                rows={4}
                maxLength={2000}
                required
                minLength={INQUIRY_NOTE_MIN_LENGTH}
                placeholder="Introduce yourself and what you are looking for…"
              />
            </label>
            {submitError ? <InlineAlert variant="error">{submitError}</InlineAlert> : null}
            <button className={styles.button} type="submit" disabled={busy}>
              {busy ? "Sending…" : "Contact host"}
            </button>
          </form>
        </div>
      );
    }

    return (
      <div className={styles.detailSection}>
        {friendNotice}
        {slotIdFromQuery ? (
          <InlineAlert variant="info">
            You selected a time from the calendar. Confirm below to request that slot.
          </InlineAlert>
        ) : null}
        <form onSubmit={handleSlotBooking}>
          <fieldset className={styles.slotList}>
            <legend>Choose an available time</legend>
            {openSlots?.map((slot) => (
              <label key={slot.id} className={styles.slotRow}>
                <input
                  type="radio"
                  name="availability_slot_id"
                  value={slot.id}
                  checked={selectedSlotId === slot.id}
                  onChange={() => setSelectedSlotId(slot.id)}
                  required
                />
                {formatSlotRange(slot.start_at, slot.end_at)}
              </label>
            ))}
          </fieldset>
          <label>
            Note to host (optional)
            <textarea name="note" rows={3} maxLength={2000} />
          </label>
          {submitError ? <InlineAlert variant="error">{submitError}</InlineAlert> : null}
          <button className={styles.button} type="submit" disabled={busy || !selectedSlotId}>
            {busy ? "Submitting…" : "Request ride"}
          </button>
        </form>
        <p className={styles.cardMeta}>
          <button
            type="button"
            className={styles.buttonSecondary}
            onClick={() => setShowContactForm(true)}
          >
            Ask a question first
          </button>
        </p>
      </div>
    );
  }

  return (
    <div className={styles.detailPage}>
      <p>
        <Link href="/listings">← Back to browse</Link>
      </p>
      <ListingImage src={photo} alt={listing.animal_name} className={styles.detailImage} />
      {photoCount > 1 ? (
        <p className={styles.cardMeta}>+{photoCount - 1} more photo(s)</p>
      ) : null}
      <h1>{listing.animal_name}</h1>
      {listing.riding_styles.length > 0 ? (
        <div className={styles.chipRow}>
          {listing.riding_styles.map((style) => (
            <span key={style} className={styles.chip}>
              {ridingStyleLabel(style)}
            </span>
          ))}
        </div>
      ) : null}
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
        <p>{listing.display_location}</p>
      </div>
      {listing.availability ? (
        <div className={styles.detailSection}>
          <h2>Availability notes</h2>
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
