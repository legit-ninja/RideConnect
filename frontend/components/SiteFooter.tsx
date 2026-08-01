import Image from "next/image";
import Link from "next/link";

import { siteConfig } from "@/lib/site";

import styles from "./SiteFooter.module.css";

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.grid}>
          <div>
            <Link href="/" className={styles.brandRow}>
              <Image
                src={siteConfig.logo}
                alt=""
                width={29}
                height={32}
                className={styles.brandMark}
              />
              {siteConfig.name}
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
          <p>&copy; {year} {siteConfig.name}. All rights reserved.</p>
          <p>Built with trust at the core</p>
        </div>
      </div>
    </footer>
  );
}
