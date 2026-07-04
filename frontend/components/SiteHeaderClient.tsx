"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { UserMenu } from "@/components/UserMenu";
import { ApiError, User, fetchCurrentUser } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

import layoutStyles from "@/app/layout.module.css";

const NAV_LINKS = [
  { href: "/listings", label: "Browse" },
  { href: "/#how-it-works", label: "How it works" },
  { href: "/owner/listings", label: "For owners" },
];

function CompassIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

export function SiteHeaderClient() {
  const pathname = usePathname();
  const isHome = pathname === "/";
  const [mounted, setMounted] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<User | null | undefined>(null);

  const transparent = isHome && !scrolled;

  useEffect(() => {
    setMounted(true);
    function onScroll() {
      setScrolled(window.scrollY > 40);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!mounted) return;
    const token = getToken();
    if (!token) {
      setUser(null);
      return;
    }
    setUser(undefined);
    fetchCurrentUser(token)
      .then(setUser)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
        }
        setUser(null);
      });
  }, [mounted, pathname]);

  const headerClass = [
    layoutStyles.header,
    transparent ? layoutStyles.headerTransparentLight : layoutStyles.headerSolid,
  ].join(" ");

  const brandClass = [
    layoutStyles.brand,
    transparent ? layoutStyles.brandTransparent : "",
  ]
    .filter(Boolean)
    .join(" ");

  const markClass = [
    layoutStyles.brandMark,
    transparent ? layoutStyles.brandMarkTransparent : "",
  ]
    .filter(Boolean)
    .join(" ");

  function navLinkClass(): string {
    return [layoutStyles.navLink, transparent ? layoutStyles.navLinkTransparent : ""]
      .filter(Boolean)
      .join(" ");
  }

  function renderAuthActions(compact: boolean) {
    if (!mounted || user === undefined) {
      return compact ? null : <nav className={layoutStyles.nav} aria-label="Main" />;
    }

    if (user) {
      return (
        <div className={layoutStyles.navActions}>
          {!compact ? (
            <nav className={layoutStyles.navDesktop} aria-label="Main">
              {NAV_LINKS.map((link) => (
                <Link key={link.href} href={link.href} className={navLinkClass()}>
                  {link.label}
                </Link>
              ))}
            </nav>
          ) : null}
          <UserMenu user={user} />
        </div>
      );
    }

    return (
      <>
        {!compact ? (
          <nav className={layoutStyles.navDesktop} aria-label="Main">
            {NAV_LINKS.map((link) => (
              <Link key={link.href} href={link.href} className={navLinkClass()}>
                {link.label}
              </Link>
            ))}
          </nav>
        ) : null}
        <div className={layoutStyles.navActions}>
          <Link
            href="/login"
            className={[
              layoutStyles.authLink,
              layoutStyles.authLinkGhost,
              transparent ? layoutStyles.authLinkGhostTransparent : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className={[layoutStyles.authLink, layoutStyles.authLinkPrimary].join(" ")}
          >
            Join
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      <header className={headerClass}>
        <Link href="/" className={brandClass}>
          <CompassIcon className={markClass} />
          RideConnect
        </Link>

        {renderAuthActions(false)}

        <button
          type="button"
          className={layoutStyles.menuButton}
          aria-expanded={mobileOpen}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          onClick={() => setMobileOpen((open) => !open)}
        >
          {mobileOpen ? <CloseIcon /> : <MenuIcon />}
        </button>
      </header>

      {mobileOpen ? (
        <div
          className={[
            layoutStyles.mobilePanel,
            transparent ? layoutStyles.mobilePanelTransparent : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {NAV_LINKS.map((link) => (
            <Link key={link.href} href={link.href} className={navLinkClass()}>
              {link.label}
            </Link>
          ))}
          {!user && mounted ? (
            <>
              <Link href="/login" className={navLinkClass()}>
                Sign in
              </Link>
              <Link href="/register" className={layoutStyles.authLinkPrimary}>
                Create account
              </Link>
            </>
          ) : null}
          {user ? (
            <>
              <Link href="/dashboard" className={navLinkClass()}>
                Dashboard
              </Link>
              <Link href="/settings" className={navLinkClass()}>
                Settings
              </Link>
            </>
          ) : null}
          <ThemeToggle />
        </div>
      ) : null}
    </>
  );
}
