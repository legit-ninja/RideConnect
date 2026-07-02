"use client";

import { Suspense } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { LoadingState } from "@/components/admin/LoadingState";

import { AdminAuditContent } from "./AdminAuditContent";

export default function AdminAuditPage() {
  return (
    <Suspense
      fallback={
        <AdminShell title="Audit log" description="Admin moderation history">
          <LoadingState label="Loading audit log" />
        </AdminShell>
      }
    >
      <AdminAuditContent />
    </Suspense>
  );
}
