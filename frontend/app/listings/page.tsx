"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { ListingCard } from "@/components/marketplace/ListingCard";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ActivityType,
  ListingSummary,
  RidingStyle,
  Species,
  fetchListings,
  fetchSpecies,
} from "@/lib/api";
import { RIDING_STYLE_OPTIONS, ridingStyleLabel } from "@/components/marketplace/marketplaceLabels";

const ACTIVITY_OPTIONS: { value: ActivityType | ""; label: string }[] = [
  { value: "", label: "All activities" },
  { value: "trail_ride", label: "Trail ride" },
  { value: "lesson", label: "Lesson" },
  { value: "lease", label: "Lease" },
  { value: "day_rental", label: "Day rental" },
];

const PRICE_BANDS: { label: string; min?: number; max?: number }[] = [
  { label: "Any price" },
  { label: "Under $50", max: 49.99 },
  { label: "$50–$100", min: 50, max: 100 },
  { label: "Over $100", min: 100.01 },
];

export default function ListingsPage() {
  const [listings, setListings] = useState<ListingSummary[]>([]);
  const [species, setSpecies] = useState<Species[]>([]);
  const [activityType, setActivityType] = useState<ActivityType | "">("");
  const [speciesId, setSpeciesId] = useState("");
  const [priceBand, setPriceBand] = useState(0);
  const [ridingStyle, setRidingStyle] = useState<RidingStyle | "">("");
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSpecies()
      .then((items) => {
        setSpecies(items);
        if (items[0]) {
          setSpeciesId(items[0].id);
        }
      })
      .catch(() => {
        setError("Unable to load species.");
      });
  }, []);

  useEffect(() => {
    if (!speciesId) return;
    setLoading(true);
    const band = PRICE_BANDS[priceBand];
    fetchListings({
      activity_type: activityType || undefined,
      species_id: speciesId || undefined,
      min_price: band?.min,
      max_price: band?.max,
      riding_style: ridingStyle || undefined,
    })
      .then(setListings)
      .catch(() => {
        setError("Unable to load listings.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [activityType, speciesId, priceBand, ridingStyle]);

  function clearFilters() {
    setActivityType("");
    setPriceBand(0);
    setRidingStyle("");
  }

  const hasFilters =
    activityType !== "" ||
    priceBand !== 0 ||
    ridingStyle !== "" ||
    searchQuery.trim() !== "";

  const visibleListings = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return listings;
    return listings.filter(
      (listing) =>
        listing.animal_name.toLowerCase().includes(query) ||
        listing.display_location.toLowerCase().includes(query),
    );
  }, [listings, searchQuery]);

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Browse rides"
        description="Verified riding experiences in the Appalachian NC region."
      />

      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      <div className={styles.searchRow}>
        <input
          type="search"
          className={styles.searchInput}
          placeholder="Search by name or location…"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          aria-label="Search listings"
        />
      </div>

      <div className={styles.filters}>
        <select
          value={speciesId}
          onChange={(event) => setSpeciesId(event.target.value)}
          aria-label="Species"
        >
          {species.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <select
          value={ridingStyle}
          onChange={(event) => setRidingStyle(event.target.value as RidingStyle | "")}
          aria-label="Riding style"
        >
          <option value="">All styles</option>
          {RIDING_STYLE_OPTIONS.map((style) => (
            <option key={style} value={style}>
              {ridingStyleLabel(style)}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.filterChips} role="group" aria-label="Activity type">
        {ACTIVITY_OPTIONS.map((option) => (
          <button
            key={option.value || "all"}
            type="button"
            className={
              activityType === option.value
                ? `${styles.chip} ${styles.chipActive}`
                : styles.chip
            }
            onClick={() => setActivityType(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className={styles.filterChips} role="group" aria-label="Price range">
        {PRICE_BANDS.map((band, index) => (
          <button
            key={band.label}
            type="button"
            className={
              priceBand === index
                ? `${styles.chip} ${styles.chipActive}`
                : styles.chip
            }
            onClick={() => setPriceBand(index)}
          >
            {band.label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState label="Loading listings" />
      ) : visibleListings.length === 0 ? (
        <EmptyState
          title="No listings found"
          description="Try adjusting your filters or run make seed to load dev data."
          action={
            hasFilters
              ? { label: "Clear filters", href: "#" }
              : undefined
          }
        >
          {hasFilters ? (
            <button
              type="button"
              className={styles.buttonSecondary}
              onClick={() => {
                clearFilters();
                setSearchQuery("");
              }}
            >
              Clear filters
            </button>
          ) : null}
        </EmptyState>
      ) : (
        <div className={styles.grid}>
          {visibleListings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      )}
    </div>
  );
}
