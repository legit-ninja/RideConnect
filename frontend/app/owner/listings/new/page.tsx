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
        min_rider_skill: form.get("min_rider_skill")
          ? Number(form.get("min_rider_skill"))
          : undefined,
        max_rider_weight_lbs: form.get("max_rider_weight_lbs")
          ? Number(form.get("max_rider_weight_lbs"))
          : undefined,
        helmet_required: form.get("helmet_required") !== "off",
        tack_provided: String(form.get("tack_provided") || "either"),
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
            <label>
              Minimum rider skill (optional)
              <select name="min_rider_skill" defaultValue="">
                <option value="">No minimum</option>
                <option value="1">Beginner and up</option>
                <option value="2">Advanced beginner and up</option>
                <option value="3">Intermediate and up</option>
                <option value="4">Advanced intermediate and up</option>
                <option value="5">Professional only</option>
              </select>
            </label>
            <label>
              Rider weight limit (lb, optional)
              <input name="max_rider_weight_lbs" type="number" min={50} max={500} />
            </label>
            <label>
              <input name="helmet_required" type="checkbox" defaultChecked /> Helmet required
            </label>
            <label>
              Tack
              <select name="tack_provided" defaultValue="either">
                <option value="provided">Provided by owner</option>
                <option value="bring_own">Rider brings own</option>
                <option value="either">Either</option>
              </select>
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
