"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ActivityType,
  Animal,
  ApiError,
  User,
  createOwnerListing,
  fetchCurrentUser,
  fetchOwnerAnimals,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function NewListingPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token)
      .then(setUser)
      .then(() => fetchOwnerAnimals(token!))
      .then(setAnimals)
      .catch(() => setError("Unable to load animals."));
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      await createOwnerListing(token, {
        animal_id: String(form.get("animal_id")),
        activity_type: String(form.get("activity_type")) as ActivityType,
        price: Number(form.get("price")),
        availability: String(form.get("availability") || "") || undefined,
        friend_only_allowed: form.get("friend_only_allowed") === "on",
      });
      router.push("/owner/listings");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Failed to create listing.");
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return (
      <div className={styles.formPage}>
        <LoadingState variant="table" count={3} label="Loading" />
      </div>
    );
  }

  return (
    <div className={styles.formPage}>
      <PageHeader
        title="Create listing"
        description="Publish a verified riding experience for riders in your region."
      />
      <BlockedAction user={user} action="create listings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {user.verification_status === "verified" ? (
        animals.length === 0 ? (
          <EmptyState
            title="Add an animal first"
            description="You need at least one animal before creating a listing."
            action={{ label: "Add animal", href: "/owner/animals/new" }}
          />
        ) : (
          <form onSubmit={handleSubmit}>
            <label>
              Animal
              <select name="animal_id" required>
                {animals.map((animal) => (
                  <option key={animal.id} value={animal.id}>
                    {animal.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Activity
              <select name="activity_type" required defaultValue="trail_ride">
                <option value="trail_ride">Trail ride</option>
                <option value="lesson">Lesson</option>
                <option value="lease">Lease</option>
                <option value="day_rental">Day rental</option>
              </select>
            </label>
            <label>
              Price (USD)
              <input name="price" type="number" min={0} step="0.01" required />
            </label>
            <label>
              Availability
              <textarea name="availability" rows={2} placeholder="e.g. Weekends only" />
            </label>
            <label>
              <input name="friend_only_allowed" type="checkbox" /> Friend-only (free ride path)
            </label>
            {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
            <button className={styles.button} type="submit" disabled={busy}>
              Create listing
            </button>
          </form>
        )
      ) : null}
      <Link href="/owner/listings">Cancel</Link>
    </div>
  );
}
