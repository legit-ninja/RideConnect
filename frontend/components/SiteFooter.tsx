import Link from "next/link";

import styles from "./SiteFooter.module.css";

function CompassIcon() {
  return (
    <svg
      className={styles.brandMark}
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
    </svg>
  );
}

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.grid}>
          <div>
            <Link href="/" className={styles.brandRow}>
              <CompassIcon />
              RideConnect
            </Link>
            <p className={styles.tagline}>
              A trust-first marketplace connecting verified riders with animal owners
              for safe, unforgettable riding experiences.
            </p>
            <p className={styles.trustRow}>Verified riders and trusted owners</p>
          </div>

          <div>
            <h2 className={styles.columnTitle}>Explore</h2>
            <ul className={styles.linkList}>
              <li>
                <Link href="/listings">Browse listings</Link>
              </li>
              <li>
                <Link href="/#how-it-works">How it works</Link>
              </li>
              <li>
                <Link href="/register">Create account</Link>
              </li>
            </ul>
          </div>

          <div>
            <h2 className={styles.columnTitle}>For owners</h2>
            <ul className={styles.linkList}>
              <li>
                <Link href="/owner/listings">Manage listings</Link>
              </li>
              <li>
                <Link href="/owner/listings/new">Create listing</Link>
              </li>
              <li>
                <Link href="/#how-it-works">Safety and trust</Link>
              </li>
            </ul>
          </div>
        </div>

        <div className={styles.bottom}>
          <p>&copy; {year} RideConnect. All rights reserved.</p>
          <p>Built with trust at the core</p>
        </div>
      </div>
    </footer>
  );
}
