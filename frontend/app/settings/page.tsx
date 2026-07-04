"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getToken } from "@/lib/auth";

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login?next=/settings");
    }
  }, [router]);

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Settings"
        description="Account settings are coming soon. For now, you can update your appearance preference below."
      />

      <div className={styles.hubSection}>
        <h2 className={styles.hubSectionTitle}>Appearance</h2>
        <ThemeToggle />
      </div>
    </div>
  );
}
