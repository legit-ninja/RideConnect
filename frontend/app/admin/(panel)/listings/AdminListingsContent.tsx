"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { activityTypeLabel } from "@/components/admin/adminLabels";
import { AdminShell } from "@/components/admin/AdminShell";
import { ConfirmDialog } from "@/components/admin/ConfirmDialog";
import { EmptyState } from "@/components/admin/EmptyState";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { DataTable } from "@/components/admin/PlaceholderPage";
import { StatusBadge } from "@/components/admin/StatusBadge";
import styles from "@/components/admin/admin.module.css";
import {
  AdminListingSummary,
  ApiError,
  fetchAdminListings,
  updateAdminListingActive,
} from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

type ActiveFilter = "all" | "active" | "inactive";

type PendingToggle = {
  listing: AdminListingSummary;
  nextActive: boolean;
};

export function AdminListingsContent() {
  const searchParams = useSearchParams();
  const ownerId = searchParams.get("owner_id");
  const { token } = useAdminAuth();
  const [listings, setListings] = useState<AdminListingSummary[]>([]);
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>("all");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [pendingToggle, setPendingToggle] = useState<PendingToggle | null>(null);

  function loadListings() {
    if (!token) return;
    setLoading(true);
    const active =
      activeFilter === "all"
        ? undefined
        : activeFilter === "active";
    fetchAdminListings(token, { active, owner_id: ownerId ?? undefined })
      .then((response) => setListings(response.items))
      .catch(() => setError("Unable to load listings."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadListings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, activeFilter, ownerId]);

  async function confirmToggle() {
    if (!token || !pendingToggle) return;
    const { listing, nextActive } = pendingToggle;
    setBusyId(listing.id);
    setError(null);
    setSuccess(null);
    try {
      await updateAdminListingActive(token, listing.id, nextActive);
      setSuccess(
        nextActive
          ? "Listing reactivated. Action logged in audit trail."
          : "Listing hidden from marketplace. Action logged in audit trail.",
      );
      loadListings();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusyId(null);
      setPendingToggle(null);
    }
  }

  const filterChips: { value: ActiveFilter; label: string }[] = [
    { value: "all", label: "All" },
    { value: "active", label: "Active" },
    { value: "inactive", label: "Inactive" },
  ];

  return (
    <AdminShell
      title="Listings"
      description={
        ownerId
          ? "Listings for selected owner"
          : "Moderation for animal ride listings"
      }
    >
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {success ? <InlineAlert variant="success">{success}</InlineAlert> : null}

      <div className={styles.filterChips} role="group" aria-label="Filter listings">
        {filterChips.map((chip) => (
          <button
            key={chip.value}
            type="button"
            className={`${styles.chip} ${
              activeFilter === chip.value ? styles.chipActive : ""
            }`}
            onClick={() => setActiveFilter(chip.value)}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState label="Loading listings" />
      ) : listings.length === 0 ? (
        <EmptyState
          title="No listings found"
          description={
            ownerId
              ? "This owner has no listings matching the current filter."
              : activeFilter !== "all"
                ? "Try a different filter."
                : "No listings on the platform yet."
          }
          action={{ label: "Back to dashboard", href: "/admin" }}
        />
      ) : (
        <DataTable
          headers={[
            "Animal",
            "Owner",
            "Activity",
            "Price",
            "Availability",
            "Status",
            "Actions",
          ]}
        >
          {listings.map((listing) => (
            <tr key={listing.id}>
              <td>{listing.animal_name}</td>
              <td>{listing.owner_email}</td>
              <td>{activityTypeLabel(listing.activity_type)}</td>
              <td>${Number(listing.price).toFixed(2)}</td>
              <td>{listing.availability ?? "—"}</td>
              <td>
                <StatusBadge kind="listing" active={listing.active} />
              </td>
              <td>
                <button
                  type="button"
                  className={
                    listing.active ? styles.buttonDanger : styles.button
                  }
                  disabled={busyId === listing.id}
                  onClick={() =>
                    setPendingToggle({
                      listing,
                      nextActive: !listing.active,
                    })
                  }
                >
                  {listing.active ? "Deactivate" : "Reactivate"}
                </button>
              </td>
            </tr>
          ))}
        </DataTable>
      )}

      <ConfirmDialog
        open={pendingToggle !== null}
        title={
          pendingToggle?.nextActive
            ? "Reactivate listing?"
            : "Deactivate listing?"
        }
        description={
          pendingToggle
            ? pendingToggle.nextActive
              ? `"${pendingToggle.listing.animal_name}" will be visible on the marketplace again. This action is logged.`
              : `"${pendingToggle.listing.animal_name}" will be hidden from the marketplace. This action is logged.`
            : ""
        }
        confirmLabel={pendingToggle?.nextActive ? "Reactivate" : "Deactivate"}
        destructive={!pendingToggle?.nextActive}
        onConfirm={() => void confirmToggle()}
        onCancel={() => setPendingToggle(null)}
      />
    </AdminShell>
  );
}
