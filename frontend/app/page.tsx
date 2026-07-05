import Link from "next/link";

import { ListingCard } from "@/components/marketplace/ListingCard";
import type { ListingSummary } from "@/lib/api";
import { getServerApiUrl } from "@/lib/server-api";

import styles from "./page.module.css";

const STEPS = [
  {
    icon: "👤",
    title: "Create your profile",
    description:
      "Set your riding experience and get verified. Owners trust riders who are transparent about their background.",
  },
  {
    icon: "🧭",
    title: "Browse verified listings",
    description:
      "Explore riding experiences from trusted owners. Filter by activity, species, and price in your region.",
  },
  {
    icon: "🛡",
    title: "Connect and ride",
    description:
      "Request a booking, coordinate with the owner in-app, and enjoy a safe, vetted riding experience.",
  },
];

const VALUES = [
  {
    icon: "🛡",
    title: "Trust first",
    description:
      "Every rider is verified. Every owner is vetted. Safety is not optional on RideConnect.",
  },
  {
    icon: "★",
    title: "Quality experiences",
    description:
      "Curated listings from passionate animal owners who care about their animals and riders.",
  },
  {
    icon: "🤝",
    title: "Community driven",
    description:
      "Built on friend invites and verified connections — not anonymous strangers.",
  },
];

async function loadFeaturedListings(): Promise<ListingSummary[]> {
  try {
    const response = await fetch(`${getServerApiUrl()}/listings`, { next: { revalidate: 60 } });
    if (!response.ok) return [];
    const listings = (await response.json()) as ListingSummary[];
    return listings.slice(0, 6);
  } catch {
    return [];
  }
}

export default async function Home() {
  const listings = await loadFeaturedListings();

  return (
    <div className={styles.home}>
      <section className={styles.hero}>
        <div className={styles.heroBackground} aria-hidden="true">
          <img
            src="/images/hero/galloping-horse.png"
            alt=""
            className={styles.heroImage}
          />
        </div>
        <div className={`${styles.heroOverlay} heroOverlay`} aria-hidden="true" />
        <div className={`${styles.heroContent} scrollFadeIn`}>
          <span className={styles.heroBadge}>Trust-first riding marketplace</span>
          <h1 className={`${styles.heroTitle} textBalance`}>
            Where riders and owners connect with confidence
          </h1>
          <p className={styles.heroSubtitle}>
            Discover verified riding experiences from trusted animal owners. Every listing is
            vetted, every rider is identity-checked.
          </p>
          <div className={styles.heroActions}>
            <Link href="/listings" className={styles.primaryButton}>
              Browse listings
            </Link>
            <Link href="/register" className={styles.secondaryButton}>
              Join as rider
            </Link>
          </div>
        </div>
      </section>

      <section id="how-it-works" className={styles.section}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeader}>
            <span className="sectionEyebrow">How it works</span>
            <h2 className={styles.sectionTitle}>A simpler way to ride</h2>
          </div>
          <div className={styles.stepsGrid}>
            {STEPS.map((step, index) => (
              <article key={step.title} className={`${styles.stepCard} scrollFadeIn`}>
                <span className={styles.stepNumber}>{index + 1}</span>
                <div className={styles.stepIcon} aria-hidden="true">
                  {step.icon}
                </div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={`${styles.section} ${styles.featuredSection}`}>
        <div className={styles.sectionInner}>
          <div className={styles.featuredHeader}>
            <div>
              <span className="sectionEyebrow">Featured</span>
              <h2 className={styles.sectionTitle}>Curated experiences</h2>
            </div>
            <Link href="/listings" className={styles.viewAllLink}>
              View all →
            </Link>
          </div>
          {listings.length > 0 ? (
            <div className={styles.featuredGrid}>
              {listings.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>
          ) : (
            <p className={styles.emptyFeatured}>
              Listings will appear here once owners publish rides. Try{" "}
              <Link href="/listings">browsing all listings</Link> or run{" "}
              <code>make seed</code> in development.
            </p>
          )}
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeader}>
            <span className="sectionEyebrow">Why RideConnect</span>
            <h2 className={styles.sectionTitle}>Built on trust</h2>
          </div>
          <div className={styles.valuesGrid}>
            {VALUES.map((value) => (
              <article key={value.title} className={styles.valueCard}>
                <div className={styles.valueIcon} aria-hidden="true">
                  {value.icon}
                </div>
                <h3>{value.title}</h3>
                <p>{value.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.ctaSection}>
        <div className={styles.ctaPanel}>
          <div className={styles.ctaBackground} aria-hidden="true" />
          <div className={styles.ctaContent}>
            <h2>Ready to ride?</h2>
            <p>
              Join RideConnect today and connect with verified owners for your next riding
              experience.
            </p>
            <div className={styles.ctaActions}>
              <Link href="/register" className={styles.primaryButton}>
                Create account
              </Link>
              <Link href="/listings" className={`${styles.secondaryButton} ${styles.ctaSecondary}`}>
                Browse listings
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
