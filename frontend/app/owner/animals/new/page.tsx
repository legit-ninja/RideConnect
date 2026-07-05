"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  parseRidingStylesFromForm,
  RidingStylesFields,
  validateHorseRidingStyles,
} from "@/components/marketplace/RidingStylesFields";
import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  Species,
  User,
  createOwnerAnimal,
  fetchCurrentUser,
  fetchSpecies,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function NewAnimalPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [species, setSpecies] = useState<Species[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [speciesId, setSpeciesId] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token).then(setUser);
    fetchSpecies().then((items) => {
      setSpecies(items);
      if (items[0]) {
        setSpeciesId(items[0].id);
      }
    });
  }, [router]);

  const selectedSpeciesName =
    species.find((item) => item.id === speciesId)?.name ?? species[0]?.name ?? "";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token || !species[0]) return;
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const riding_styles = parseRidingStylesFromForm(form, selectedSpeciesName);
    if (selectedSpeciesName === "horse") {
      const validationError = validateHorseRidingStyles(riding_styles);
      if (validationError) {
        setError(validationError);
        setBusy(false);
        return;
      }
    }
    try {
      await createOwnerAnimal(token, {
        species_id: String(form.get("species_id")),
        name: String(form.get("name")),
        breed: String(form.get("breed") || "") || null,
        age: form.get("age") ? Number(form.get("age")) : null,
        description: String(form.get("description") || "") || null,
        lat: Number(form.get("lat")),
        lng: Number(form.get("lng")),
        address: String(form.get("address")),
        photo_urls: [],
        riding_styles,
      });
      router.push("/owner/animals");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Failed to create animal.");
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
      <h1>Add animal</h1>
      <BlockedAction user={user} action="add animals" />
      {user.verification_status === "verified" ? (
        <form onSubmit={handleSubmit}>
          <label>
            Species
            <select
              name="species_id"
              required
              value={speciesId}
              onChange={(event) => setSpeciesId(event.target.value)}
            >
              {species.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <RidingStylesFields speciesName={selectedSpeciesName} />
          <label>
            Name
            <input name="name" required />
          </label>
          <label>
            Breed
            <input name="breed" />
          </label>
          <label>
            Age
            <input name="age" type="number" min={0} />
          </label>
          <label>
            Description
            <textarea name="description" rows={3} />
          </label>
          <label>
            Address
            <input name="address" required defaultValue="Boone, NC 28607" />
          </label>
          <label>
            Latitude
            <input name="lat" type="number" step="any" required defaultValue={36.2168} />
          </label>
          <label>
            Longitude
            <input name="lng" type="number" step="any" required defaultValue={-81.6746} />
          </label>
          {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
          <button className={styles.button} type="submit" disabled={busy}>
            {busy ? "Saving…" : "Create animal"}
          </button>
        </form>
      ) : null}
      <Link href="/owner/animals">Cancel</Link>
    </div>
  );
}
