"use client";

import { AdminShell } from "@/components/admin/AdminShell";
import { EmptyState } from "@/components/admin/EmptyState";

export default function AdminReportsPage() {
  return (
    <AdminShell
      title="Reports"
      description="Trust and safety report queue (coming soon)"
    >
      <EmptyState
        title="Reports queue (coming soon)"
        description="Flagged accounts, user reports, and pattern alerts will appear here for manual review once the reports API ships."
        action={{ label: "Open verification queue", href: "/admin/verification" }}
      />
    </AdminShell>
  );
}
