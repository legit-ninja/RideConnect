import Link from "next/link";

import { ThemeToggle } from "@/components/ThemeToggle";

import layoutStyles from "@/app/layout.module.css";

export function SiteHeader() {
  return (
    <header className={layoutStyles.header}>
      <Link href="/" className={layoutStyles.brand}>
        RideConnect
      </Link>
      <nav className={layoutStyles.nav} aria-label="Main">
        <Link href="/login">Sign in</Link>
        <Link href="/register">Register</Link>
        <Link href="/listings">Browse</Link>
        <Link href="/dashboard">Dashboard</Link>
        <Link href="/admin">Admin</Link>
        <ThemeToggle />
      </nav>
    </header>
  );
}
