"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import {
  activityTypeLabel,
  bookingStatusLabel,
} from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import { ApiError, BookingRequest, User, fetchBookings, fetchCurrentUser } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function RiderBookingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [bookings, setBookings] = useState<BookingRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);

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
                    <td>{new Date(booking.requested_at).toLocaleDateString()}</td>
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
