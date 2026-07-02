"use client";

import { Suspense } from "react";

import { AdminUserDetailContent } from "./AdminUserDetailContent";
import { AdminShell } from "@/components/admin/AdminShell";
import { LoadingState } from "@/components/admin/LoadingState";

export default function AdminUserDetailPage() {
  return (
    <Suspense
      fallback={
        <AdminShell title="User detail">
          <LoadingState label="Loading user" />
        </AdminShell>
      }
    >
      <AdminUserDetailContent />
    </Suspense>
  );
}
