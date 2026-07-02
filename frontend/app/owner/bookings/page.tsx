"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
  status: "approved" | "declined";
};

export default function OwnerBookingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [bookings, setBookings] = useState<BookingRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [busy, setBusy] = useState(false);

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
        if (!currentUser.is_owner) {
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

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Booking inbox"
        description="Review and respond to ride requests for your listings."
      />
      <BlockedAction user={user} action="manage bookings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {user.verification_status === "verified" ? (
        bookings.length === 0 ? (
          <EmptyState
            title="No booking requests"
            description="When riders request rides on your listings, they will appear here."
            action={{ label: "Manage listings", href: "/owner/listings" }}
          />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Rider</th>
                  <th>Listing</th>
                  <th>Status</th>
                  <th>Requested</th>
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
                    <td>{new Date(booking.requested_at).toLocaleDateString()}</td>
                    <td>
                      {booking.status === "pending_owner" ||
                      booking.status === "pending_payment" ? (
                        <div className={styles.buttonGroup}>
                          <button
                            type="button"
                            className={styles.button}
                            onClick={() =>
                              setPending({ booking, status: "approved" })
                            }
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            className={styles.buttonSecondary}
                            onClick={() =>
                              setPending({ booking, status: "declined" })
                            }
                          >
                            Decline
                          </button>
                        </div>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : null}

      <ConfirmDialog
        open={pending !== null}
        title={pending?.status === "approved" ? "Approve booking?" : "Decline booking?"}
        description={
          pending
            ? `${pending.status === "approved" ? "Approve" : "Decline"} the ride request from ${pending.booking.rider_email} for ${pending.booking.animal_name}.`
            : ""
        }
        confirmLabel={pending?.status === "approved" ? "Approve" : "Decline"}
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
