"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { VerificationBanner } from "@/components/marketplace/VerificationBanner";
import { VerificationPill } from "@/components/marketplace/VerificationPill";
import styles from "@/components/marketplace/marketplace.module.css";
import stylesAuth from "../auth.module.css";
import { ApiError, User, fetchCurrentUser } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    fetchCurrentUser(token)
      .then(setUser)
      .catch((err: unknown) => {
        clearToken();
        if (err instanceof ApiError && err.status === 401) {
          router.replace("/login");
          return;
        }
        setError("Unable to load your profile.");
      });
  }, [router]);

  function handleSignOut() {
    clearToken();
    router.push("/login");
  }

  if (error) {
    return (
      <div className={styles.listingsPage}>
        <InlineAlert variant="error">{error}</InlineAlert>
      </div>
    );
  }

  if (!user) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={3} label="Loading dashboard" />
      </div>
    );
  }

  const isVerified = user.verification_status === "verified";
  const roles = [user.is_rider && "Rider", user.is_owner && "Owner"].filter(Boolean);

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Dashboard"
        description={`Signed in as ${user.email}`}
        actions={<VerificationPill status={user.verification_status} />}
      />

      <VerificationBanner user={user} />

      {user.is_minor ? (
        <InlineAlert variant="warning">
          Minor accounts need a verified guardian linked before ride activity. Ask your
          guardian to complete verification and link your account.
        </InlineAlert>
      ) : null}

      <div className={styles.hubSection}>
        <h2 className={styles.hubSectionTitle}>Your roles</h2>
        <p>{roles.length > 0 ? roles.join(" · ") : "No roles set"}</p>
      </div>

      <div className={styles.hubSection}>
        <h2 className={styles.hubSectionTitle}>Next steps</h2>
        <div className={styles.hubLinks}>
          {!isVerified ? (
            <>
              <Link href="/listings" className={styles.buttonSecondary}>
                Browse rides (read-only)
              </Link>
              <span className={styles.cardMeta}>
                Complete identity verification to request rides or host listings.
              </span>
            </>
          ) : null}

          {isVerified && user.is_rider ? (
            <>
              <Link href="/listings" className={styles.button}>
                Find a ride
              </Link>
              <Link href="/rider/bookings" className={styles.buttonSecondary}>
                My bookings
              </Link>
            </>
          ) : null}

          {isVerified && user.is_owner ? (
            <>
              <Link href="/owner/listings" className={styles.button}>
                Manage listings
              </Link>
              <Link href="/owner/friends" className={styles.buttonSecondary}>
                Verified friends
              </Link>
              <Link href="/owner/bookings" className={styles.buttonSecondary}>
                Booking inbox
              </Link>
              <Link href="/owner/animals" className={styles.buttonSecondary}>
                My animals
              </Link>
            </>
          ) : null}

          {user.is_admin ? (
            <Link href="/admin" className={styles.buttonSecondary}>
              Admin panel
            </Link>
          ) : null}
        </div>
      </div>

      <button className={stylesAuth.button} type="button" onClick={handleSignOut}>
        Sign out
      </button>
    </div>
  );
}
