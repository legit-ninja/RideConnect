"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { BookingThreadPanel } from "@/components/marketplace/BookingThreadPanel";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import {
  activityTypeLabel,
  bookingStatusLabel,
} from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import { ApiError, BookingRequest, User, createBookingReview, fetchBookings, fetchCurrentUser } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function RiderBookingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [bookings, setBookings] = useState<BookingRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewBusy, setReviewBusy] = useState<string | null>(null);
  const [expandedThreadId, setExpandedThreadId] = useState<string | null>(null);

  async function submitReview(bookingId: string, form: HTMLFormElement) {
    const token = getToken();
    if (!token) return;
    const data = new FormData(form);
    const rating = Number(data.get("rating"));
    const body = String(data.get("body") || "");
    setReviewBusy(bookingId);
    setError(null);
    try {
      await createBookingReview(token, bookingId, { rating, body: body || undefined });
      form.reset();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Review failed.");
    } finally {
      setReviewBusy(null);
    }
  }

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token)
      .then((currentUser) => {
        setUser(currentUser);
        if (!currentUser.is_rider) {
          router.replace("/dashboard");
          return null;
        }
        return fetchBookings(token, "rider");
      })
      .then((response) => {
        if (response) setBookings(response.items);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 403) {
          setError("Rider access or verification required.");
        } else {
          setError("Unable to load bookings.");
        }
      });
  }, [router]);

  if (!user || bookings === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={5} label="Loading bookings" />
      </div>
    );
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="My bookings"
        description="Ride requests you have submitted on RideConnect."
      />
      <BlockedAction user={user} action="view bookings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {user.verification_status === "verified" ? (
        bookings.length === 0 ? (
          <EmptyState
            title="No bookings yet"
            description="Browse listings and request a ride to get started."
            action={{ label: "Find a ride", href: "/listings" }}
          />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Listing</th>
                  <th>Owner</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Scheduled</th>
                  <th>Requested</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((booking) => (
                  <tr key={booking.id}>
                    <td>
                      <Link href={`/listings/${booking.listing_id}`}>
                        {booking.animal_name}
                      </Link>
                      <div className={styles.cardMeta}>
                        {activityTypeLabel(booking.activity_type)}
                      </div>
                    </td>
                    <td>{booking.owner_email}</td>
                    <td>{booking.payment_type === "free" ? "Free (friend)" : "Paid"}</td>
                    <td>{bookingStatusLabel(booking.status)}</td>
                    <td>
                      {booking.scheduled_at
                        ? new Date(booking.scheduled_at).toLocaleString()
                        : "—"}
                    </td>
                    <td>
                      {new Date(booking.requested_at).toLocaleDateString()}
                      {booking.thread_id ? (
                        <div className={styles.cardMetaSpaced}>
                          <button
                            type="button"
                            className={styles.buttonSecondary}
                            onClick={() =>
                              setExpandedThreadId((current) =>
                                current === booking.thread_id ? null : booking.thread_id ?? null,
                              )
                            }
                          >
                            {expandedThreadId === booking.thread_id
                              ? "Hide messages"
                              : "View messages"}
                          </button>
                          {expandedThreadId === booking.thread_id ? (
                            <BookingThreadPanel threadId={booking.thread_id} />
                          ) : null}
                        </div>
                      ) : null}
                      {booking.status === "completed" ? (
                        <form
                          className={styles.formPage}
                          style={{ marginTop: "0.5rem" }}
                          onSubmit={(event) => {
                            event.preventDefault();
                            void submitReview(booking.id, event.currentTarget);
                          }}
                        >
                          <label>
                            Rating
                            <select name="rating" required defaultValue="5">
                              {[5, 4, 3, 2, 1].map((value) => (
                                <option key={value} value={value}>
                                  {value} stars
                                </option>
                              ))}
                            </select>
                          </label>
                          <label>
                            Review (optional)
                            <textarea name="body" rows={2} />
                          </label>
                          <button
                            type="submit"
                            className={styles.buttonSecondary}
                            disabled={reviewBusy === booking.id}
                          >
                            {reviewBusy === booking.id ? "Saving…" : "Leave review"}
                          </button>
                        </form>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : null}

      <p>
        <Link href="/dashboard">Back to dashboard</Link>
      </p>
    </div>
  );
}
