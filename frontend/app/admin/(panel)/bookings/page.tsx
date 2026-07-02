"use client";

import { useEffect, useState } from "react";

import { activityTypeLabel } from "@/components/admin/adminLabels";
import styles from "@/components/admin/admin.module.css";
import { AdminShell } from "@/components/admin/AdminShell";
import { EmptyState } from "@/components/admin/EmptyState";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { DataTable } from "@/components/admin/PlaceholderPage";
import { bookingStatusLabel } from "@/components/marketplace/marketplaceLabels";
import { ApiError, BookingRequest, fetchAdminBookings } from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

export default function AdminBookingsPage() {
  const { token } = useAdminAuth();
  const [bookings, setBookings] = useState<BookingRequest[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetchAdminBookings(token)
      .then((response) => {
        setBookings(response.items);
        setTotal(response.total);
      })
      .catch((err: unknown) => {
        setError(
          err instanceof ApiError ? err.message : "Unable to load bookings.",
        );
      })
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <AdminShell
      title="Bookings"
      description="Ride request oversight across the marketplace"
    >
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {loading ? (
        <LoadingState label="Loading bookings" />
      ) : bookings.length === 0 ? (
        <EmptyState
          title="No booking requests"
          description="Booking requests from riders will appear here for moderation preview."
          action={{ label: "Open verification queue", href: "/admin/verification" }}
        />
      ) : (
        <>
          <p className={styles.mutedText}>
            {total} booking request{total === 1 ? "" : "s"} total
          </p>
          <DataTable
            headers={["Rider", "Owner", "Listing", "Type", "Status", "Requested"]}
          >
            {bookings.map((booking) => (
              <tr key={booking.id}>
                <td>{booking.rider_email}</td>
                <td>{booking.owner_email}</td>
                <td>
                  {booking.animal_name} ({activityTypeLabel(booking.activity_type)})
                </td>
                <td>{booking.payment_type === "free" ? "Free" : "Paid"}</td>
                <td>{bookingStatusLabel(booking.status)}</td>
                <td>{new Date(booking.requested_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </DataTable>
        </>
      )}
    </AdminShell>
  );
}
