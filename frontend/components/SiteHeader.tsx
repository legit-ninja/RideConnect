import Link from "next/link";

import { SiteHeaderClient } from "@/components/SiteHeaderClient";

import layoutStyles from "@/app/layout.module.css";

export function SiteHeader() {
  return (
    <header className={layoutStyles.header}>
      <Link href="/" className={layoutStyles.brand}>
        RideConnect
      </Link>
      <SiteHeaderClient />
    </header>
  );
}
