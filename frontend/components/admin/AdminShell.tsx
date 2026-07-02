"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

import { useAdminStats } from "./AdminStatsContext";
import { QueueBadge } from "./QueueBadge";
import styles from "./admin.module.css";

interface NavItem {
  href: string;
  label: string;
  soon?: boolean;
  badgeKey?: "verification" | "listings";
}

const NAV_ITEMS: NavItem[] = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/verification", label: "Verification", badgeKey: "verification" },
  { href: "/admin/listings", label: "Listings", badgeKey: "listings" },
  { href: "/admin/audit", label: "Audit log" },
  { href: "/admin/bookings", label: "Bookings", soon: true },
  { href: "/admin/reports", label: "Reports", soon: true },
];

interface AdminShellProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function AdminShell({
  title,
  description,
  actions,
  children,
}: AdminShellProps) {
  const pathname = usePathname();
  const stats = useAdminStats();

  function isActive(href: string): boolean {
    if (href === "/admin") {
      return pathname === "/admin";
    }
    return pathname.startsWith(href);
  }

  function badgeCount(key: "verification" | "listings"): number {
    if (!stats) return 0;
    if (key === "verification") {
      return stats.unverified_users + stats.pending_users;
    }
    return Math.max(0, stats.total_listings - stats.active_listings);
  }

  return (
    <div className={styles.adminShell}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarTitle}>Admin</div>
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={[
              styles.navLink,
              isActive(item.href) ? styles.navLinkActive : "",
              item.soon ? styles.navLinkSoon : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <span className={styles.navLinkInner}>
              <span>
                {item.label}
                {item.soon ? " (soon)" : ""}
              </span>
              {item.badgeKey ? (
                <QueueBadge count={badgeCount(item.badgeKey)} />
              ) : null}
            </span>
          </Link>
        ))}
      </aside>
      <div className={styles.content}>
        <div className={styles.contentHeader}>
          <div>
            <h1>{title}</h1>
            {description ? <p>{description}</p> : null}
          </div>
          {actions}
        </div>
        {children}
      </div>
    </div>
  );
}
