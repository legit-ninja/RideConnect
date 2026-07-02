"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  OwnerListing,
  User,
  fetchCurrentUser,
  fetchOwnerListings,
  updateOwnerListing,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function EditListingPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [user, setUser] = useState<User | null>(null);
  const [listing, setListing] = useState<OwnerListing | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    Promise.all([fetchCurrentUser(token), fetchOwnerListings(token)])
      .then(([currentUser, listings]) => {
        setUser(currentUser);
        setListing(listings.find((item) => item.id === id) ?? null);
      })
      .catch(() => setError("Unable to load listing."));
  }, [id, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      await updateOwnerListing(token, id, {
        price: Number(form.get("price")),
        availability: String(form.get("availability") || "") || undefined,
        active: form.get("active") === "on",
      });
      router.push("/owner/listings");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!user || listing === undefined) {
    return (
      <div className={styles.formPage}>
        <LoadingState variant="table" count={4} label="Loading listing" />
      </div>
    );
  }

  if (listing === null) {
    return (
      <div className={styles.formPage}>
        <EmptyState
          title="Listing not found"
          description="This listing may have been removed or you do not have access."
          action={{ label: "Back to listings", href: "/owner/listings" }}
        />
      </div>
    );
  }

  return (
    <div className={styles.formPage}>
      <h1>Edit listing</h1>
      <BlockedAction user={user} action="edit listings" />
      {user.verification_status === "verified" ? (
        <form onSubmit={handleSubmit}>
          <label>
            Price (USD)
            <input
              name="price"
              type="number"
              min={0}
              step="0.01"
              required
              defaultValue={Number(listing.price)}
            />
          </label>
          <label>
            Availability
            <textarea
              name="availability"
              rows={2}
              defaultValue={listing.availability ?? ""}
            />
          </label>
          <label>
            <input name="active" type="checkbox" defaultChecked={listing.active} /> Active
          </label>
          {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
          <button className={styles.button} type="submit" disabled={busy}>
            Save
          </button>
        </form>
      ) : null}
      <Link href="/owner/listings">Back</Link>
    </div>
  );
}
