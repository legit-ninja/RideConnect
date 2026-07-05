"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BookingsCalendar } from "@/components/marketplace/BookingsCalendar";
import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { ConfirmDialog } from "@/components/marketplace/ConfirmDialog";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { VerificationPill } from "@/components/marketplace/VerificationPill";
import {
  activityTypeLabel,
  bookingStatusLabel,
} from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  BookingRequest,
  User,
  fetchBookings,
  fetchCurrentUser,
  updateBookingStatus,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

type PendingAction = {
  booking: BookingRequest;
  status: "approved" | "declined" | "completed";
};

type InboxView = "list" | "calendar";

export default function OwnerBookingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [bookings, setBookings] = useState<BookingRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<InboxView>("list");

  function loadBookings(token: string) {
    fetchBookings(token, "owner")
      .then((response) => setBookings(response.items))
      .catch(() => setError("Unable to load booking requests."));
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
        if (!currentUser.is_owner && !currentUser.is_trainer) {
          router.replace("/dashboard");
          return;
        }
        loadBookings(token);
      })
      .catch(() => setError("Unable to load profile."));
  }, [router]);

  async function confirmAction() {
    if (!pending) return;
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await updateBookingStatus(token, pending.booking.id, pending.status);
      loadBookings(token);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
      setPending(null);
    }
  }

  if (!user || bookings === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={5} label="Loading bookings" />
      </div>
    );
  }

  const emptyInbox = bookings.length === 0;

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Booking inbox"
        description="Review and respond to ride requests for your listings."
      />
      <BlockedAction user={user} action="manage bookings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {user.verification_status === "verified" ? (
        emptyInbox ? (
          <EmptyState
            title="No booking requests"
            description="When riders request rides on your listings, they will appear here."
            action={{ label: "Manage listings", href: "/owner/listings" }}
          />
        ) : (
          <>
            <div className={styles.viewTabs} role="tablist" aria-label="Booking inbox view">
              <button
                type="button"
                role="tab"
                aria-selected={view === "list"}
                className={view === "list" ? styles.viewTabActive : styles.viewTab}
                onClick={() => setView("list")}
              >
                List
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={view === "calendar"}
                className={view === "calendar" ? styles.viewTabActive : styles.viewTab}
                onClick={() => setView("calendar")}
              >
                Calendar
              </button>
            </div>

            {view === "list" ? (
              <div className={styles.tableWrap}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Rider</th>
                      <th>Listing</th>
                      <th>Status</th>
                      <th>Scheduled</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.map((booking) => (
                      <tr key={booking.id}>
                        <td>
                          <div>{booking.rider_email}</div>
                          <VerificationPill status={booking.rider_verification_status} />
                        </td>
                        <td>
                          {booking.animal_name} — {activityTypeLabel(booking.activity_type)}
                          {booking.note ? (
                            <div className={styles.cardMeta}>Note: {booking.note}</div>
                          ) : null}
                        </td>
                        <td>{bookingStatusLabel(booking.status)}</td>
                        <td>
                          {booking.scheduled_at
                            ? new Date(booking.scheduled_at).toLocaleString()
                            : new Date(booking.requested_at).toLocaleDateString()}
                        </td>
                        <td>
                          {booking.status === "pending_owner" ||
                          booking.status === "pending_payment" ? (
                            <div className={styles.buttonGroup}>
                              <button
                                type="button"
                                className={styles.button}
                                disabled={busy}
                                onClick={() =>
                                  setPending({ booking, status: "approved" })
                                }
                              >
                                Approve
                              </button>
                              <button
                                type="button"
                                className={styles.buttonSecondary}
                                disabled={busy}
                                onClick={() =>
                                  setPending({ booking, status: "declined" })
                                }
                              >
                                Decline
                              </button>
                            </div>
                          ) : booking.status === "approved" ? (
                            <button
                              type="button"
                              className={styles.buttonSecondary}
                              disabled={busy}
                              onClick={() =>
                                setPending({ booking, status: "completed" })
                              }
                            >
                              Mark complete
                            </button>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <BookingsCalendar
                bookings={bookings}
                onApprove={(booking) => setPending({ booking, status: "approved" })}
                onDecline={(booking) => setPending({ booking, status: "declined" })}
                onComplete={(booking) => setPending({ booking, status: "completed" })}
              />
            )}
          </>
        )
      ) : null}

      <ConfirmDialog
        open={pending !== null}
        title={
          pending?.status === "approved"
            ? "Approve booking?"
            : pending?.status === "completed"
              ? "Mark booking complete?"
              : "Decline booking?"
        }
        description={
          pending
            ? pending.status === "completed"
              ? `Mark the ride with ${pending.booking.rider_email} for ${pending.booking.animal_name} as complete so both parties can leave reviews.`
              : `${pending.status === "approved" ? "Approve" : "Decline"} the ride request from ${pending.booking.rider_email} for ${pending.booking.animal_name}.`
            : ""
        }
        confirmLabel={
          pending?.status === "approved"
            ? "Approve"
            : pending?.status === "completed"
              ? "Mark complete"
              : "Decline"
        }
        destructive={pending?.status === "declined"}
        onConfirm={confirmAction}
        onCancel={() => setPending(null)}
      />

      <p>
        <Link href="/dashboard">Back to dashboard</Link>
      </p>
    </div>
  );
}
