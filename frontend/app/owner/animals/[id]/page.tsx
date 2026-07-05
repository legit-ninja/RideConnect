"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
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
  Animal,
  ApiError,
  Species,
  User,
  fetchCurrentUser,
  fetchOwnerAnimals,
  fetchSpecies,
  updateOwnerAnimal,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function EditAnimalPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [user, setUser] = useState<User | null>(null);
  const [animal, setAnimal] = useState<Animal | null | undefined>(undefined);
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
    Promise.all([fetchCurrentUser(token), fetchSpecies(), fetchOwnerAnimals(token)])
      .then(([currentUser, speciesList, animals]) => {
        setUser(currentUser);
        setSpecies(speciesList);
        const found = animals.find((item) => item.id === id) ?? null;
        setAnimal(found);
        if (found) {
          setSpeciesId(found.species_id);
        }
      })
      .catch(() => setError("Unable to load animal."));
  }, [id, router]);

  const selectedSpeciesName =
    species.find((item) => item.id === speciesId)?.name ?? "";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
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
      await updateOwnerAnimal(token, id, {
        species_id: String(form.get("species_id")),
        name: String(form.get("name")),
        breed: String(form.get("breed") || "") || null,
        description: String(form.get("description") || "") || null,
        address: String(form.get("address")),
        riding_styles,
      });
      router.push("/owner/animals");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!user || animal === undefined) {
    return (
      <div className={styles.formPage}>
        <LoadingState variant="table" count={4} label="Loading animal" />
      </div>
    );
  }

  if (animal === null) {
    return (
      <div className={styles.formPage}>
        <EmptyState
          title="Animal not found"
          description="This animal may have been removed or you do not have access."
          action={{ label: "Back to animals", href: "/owner/animals" }}
        />
      </div>
    );
  }

  return (
    <div className={styles.formPage}>
      <h1>Edit {animal.name}</h1>
      <BlockedAction user={user} action="edit animals" />
      {user.verification_status === "verified" ? (
        <form onSubmit={handleSubmit}>
          <label>
            Species
            <select
              name="species_id"
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
          <RidingStylesFields
            speciesName={selectedSpeciesName}
            defaultStyles={animal.riding_styles}
          />
          <label>
            Name
            <input name="name" required defaultValue={animal.name} />
          </label>
          <label>
            Breed
            <input name="breed" defaultValue={animal.breed ?? ""} />
          </label>
          <label>
            Description
            <textarea name="description" rows={3} defaultValue={animal.description ?? ""} />
          </label>
          <label>
            Address
            <input name="address" required defaultValue={animal.address} />
          </label>
          {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
          <button className={styles.button} type="submit" disabled={busy}>
            Save
          </button>
        </form>
      ) : null}
      <Link href="/owner/animals">Back</Link>
    </div>
  );
}
