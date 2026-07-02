"use client";

import { Suspense } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { LoadingState } from "@/components/admin/LoadingState";
import { AdminListingsContent } from "./AdminListingsContent";

export default function AdminListingsPage() {
  return (
    <Suspense
      fallback={
        <AdminShell title="Listings" description="Moderation for animal ride listings">
          <LoadingState label="Loading listings" />
        </AdminShell>
      }
    >
      <AdminListingsContent />
    </Suspense>
  );
}
