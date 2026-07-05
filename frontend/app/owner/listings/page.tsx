"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { activityTypeLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  OwnerListing,
  User,
  fetchCurrentUser,
  fetchOwnerListings,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function OwnerListingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [listings, setListings] = useState<OwnerListing[] | null>(null);
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
        if (!currentUser.is_owner && !currentUser.is_trainer) {
          router.replace("/dashboard");
          return null;
        }
        return fetchOwnerListings(token);
      })
      .then((data) => {
        if (data) setListings(data);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 403) {
          setError("Owner access or verification required.");
        } else {
          setError("Unable to load listings.");
        }
      });
  }, [router]);

  if (!user || listings === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={4} label="Loading listings" />
      </div>
    );
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader title="My listings" description="Rides and experiences you offer." />
      <BlockedAction user={user} action="manage listings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {user.verification_status === "verified" ? (
        <>
          <p>
            <Link href="/owner/listings/new" className={styles.button}>
              Create listing
            </Link>
          </p>
          {listings.length === 0 ? (
            <EmptyState
              title="No listings yet"
              description="Create a listing from one of your animals."
              action={{ label: "Create listing", href: "/owner/listings/new" }}
            />
          ) : (
            <ul>
              {listings.map((listing) => (
                <li key={listing.id}>
                  <Link href={`/owner/listings/${listing.id}`}>
                    {activityTypeLabel(listing.activity_type)} — $
                    {Number(listing.price).toFixed(2)}
                  </Link>
                  {listing.active ? "" : " (inactive)"}
                  {listing.friend_only_allowed ? " · Friends only" : ""}
                </li>
              ))}
            </ul>
          )}
        </>
      ) : null}
      <p>
        <Link href="/dashboard">Back to dashboard</Link>
      </p>
    </div>
  );
}
