"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { UserMenu } from "@/components/UserMenu";
import { ApiError, User, fetchCurrentUser } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

import layoutStyles from "@/app/layout.module.css";

export function SiteHeaderClient() {
  // Always null on first render so SSR and client hydration match (getToken() is
  // unavailable on the server). Token verification runs after mount.
  const [mounted, setMounted] = useState(false);
  const [user, setUser] = useState<User | null | undefined>(null);

  useEffect(() => {
    setMounted(true);
    const token = getToken();
    if (!token) return;
    setUser(undefined);
    fetchCurrentUser(token)
      .then(setUser)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
        }
        setUser(null);
      });
  }, []);

  if (!mounted || user === undefined) {
    if (!mounted) {
      // Pre-mount: mirror SSR signed-out nav so hydration HTML matches.
      return (
        <nav className={layoutStyles.nav} aria-label="Main">
          <Link href="/login">Sign in</Link>
          <Link href="/register">Register</Link>
          <Link href="/listings">Browse</Link>
          <ThemeToggle />
        </nav>
      );
    }
    // Post-mount: token present, awaiting /auth/me — keep layout stable.
    return <nav className={layoutStyles.nav} aria-label="Main" />;
  }

  if (!user) {
    return (
      <nav className={layoutStyles.nav} aria-label="Main">
        <Link href="/login">Sign in</Link>
        <Link href="/register">Register</Link>
        <Link href="/listings">Browse</Link>
        <ThemeToggle />
      </nav>
    );
  }

  return (
    <nav className={layoutStyles.nav} aria-label="Main">
      <Link href="/listings">Browse</Link>
      <Link href="/dashboard">Dashboard</Link>
      <UserMenu user={user} />
    </nav>
  );
}
