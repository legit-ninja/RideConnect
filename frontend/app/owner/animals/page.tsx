"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import { Animal, ApiError, User, fetchCurrentUser, fetchOwnerAnimals } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function OwnerAnimalsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [animals, setAnimals] = useState<Animal[] | null>(null);
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
        return fetchOwnerAnimals(token);
      })
      .then((data) => {
        if (data) setAnimals(data);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 403) {
          setError("Owner access or verification required.");
        } else {
          setError("Unable to load animals.");
        }
      });
  }, [router]);

  if (!user || animals === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={4} label="Loading animals" />
      </div>
    );
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader title="My animals" description="Animals you host on RideConnect." />
      <BlockedAction user={user} action="manage animals" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {user.verification_status === "verified" ? (
        <>
          <p>
            <Link href="/owner/animals/new" className={styles.button}>
              Add animal
            </Link>
          </p>
          {animals.length === 0 ? (
            <EmptyState
              title="No animals yet"
              description="Add your first animal to create ride listings."
              action={{ label: "Add animal", href: "/owner/animals/new" }}
            />
          ) : (
            <ul>
              {animals.map((animal) => (
                <li key={animal.id}>
                  <Link href={`/owner/animals/${animal.id}`}>{animal.name}</Link> —{" "}
                  {animal.address}
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
