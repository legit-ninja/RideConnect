"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { ListingImage } from "@/components/marketplace/ListingImage";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  OwnerListing,
  User,
  fetchCurrentUser,
  fetchOwnerListings,
  publicListingUrl,
  updateOwnerListing,
  uploadListingPhoto,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function EditListingPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [user, setUser] = useState<User | null>(null);
  const [listing, setListing] = useState<OwnerListing | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

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

  async function handlePhotoUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const token = getToken();
    const file = event.target.files?.[0];
    if (!token || !file) return;
    setBusy(true);
    setError(null);
    try {
      await uploadListingPhoto(token, id, file);
      setSuccess("Photo uploaded.");
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  function copyShareLink() {
    if (!listing) return;
    const url = publicListingUrl(listing.slug);
    void navigator.clipboard.writeText(url);
    setCopied(true);
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

  const shareUrl = publicListingUrl(listing.slug);
  const facebookShare = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;

  return (
    <div className={styles.formPage}>
      <PageHeader
        title="Edit listing"
        description="Update pricing, availability, and photos for this ride."
      />
      <BlockedAction user={user} action="edit listings" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {success ? <InlineAlert variant="success">{success}</InlineAlert> : null}

      <div className={styles.shareBox}>
        <h2>Share listing</h2>
        <p className={styles.cardMeta}>{shareUrl}</p>
        <div className={styles.shareRow}>
          <button type="button" className={styles.buttonSecondary} onClick={copyShareLink}>
            {copied ? "Copied!" : "Copy link"}
          </button>
          <a
            href={facebookShare}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.buttonSecondary}
          >
            Share on Facebook
          </a>
        </div>
        <ListingImage
          src={`/api/og/${listing.slug}`}
          alt="Share card preview"
          className={styles.sharePreview}
        />
      </div>

      {user.verification_status === "verified" ? (
        <>
          <label>
            Upload photo
            <input type="file" accept="image/*" onChange={handlePhotoUpload} disabled={busy} />
          </label>

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
            <button className={styles.button} type="submit" disabled={busy}>
              Save
            </button>
          </form>
        </>
      ) : null}
      <Link href="/owner/listings">Back</Link>
    </div>
  );
}
