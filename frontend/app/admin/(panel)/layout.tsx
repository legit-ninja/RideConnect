"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { AdminStatsProvider } from "@/components/admin/AdminStatsContext";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import styles from "@/components/admin/admin.module.css";
import { clearToken } from "@/lib/auth";
import { useAdminAuth } from "@/lib/useAdminAuth";

export default function AdminPanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, token, loading, error } = useAdminAuth();

  function handleSignOut() {
    clearToken();
    router.push("/login");
  }

  if (loading) {
    return (
      <div className={styles.loadingShell}>
        <LoadingState variant="stats" label="Loading admin panel" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.loadingShell}>
        <InlineAlert variant="error">{error}</InlineAlert>
      </div>
    );
  }

  if (!user || !token) {
    return null;
  }

  return (
    <AdminStatsProvider token={token}>
      <div className={styles.adminTopBar}>
        <span>
          Signed in as <strong>{user.email}</strong>
        </span>
        <Link href="/dashboard">Dashboard</Link>
        <button
          type="button"
          onClick={handleSignOut}
          className={styles.signOutButton}
        >
          Sign out
        </button>
      </div>
      {children}
    </AdminStatsProvider>
  );
}
