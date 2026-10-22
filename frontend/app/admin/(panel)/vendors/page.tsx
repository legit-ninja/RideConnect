"use client";

import { useEffect, useState } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import styles from "@/components/admin/admin.module.css";
import {
  ApiError,
  VendorProfile,
  fetchAdminVendors,
  updateAdminVendor,
} from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

export default function AdminVendorsPage() {
  const { token } = useAdminAuth();
  const [vendors, setVendors] = useState<VendorProfile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  function load() {
    if (!token) return;
    fetchAdminVendors(token)
      .then(setVendors)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Unable to load vendors.");
      });
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function setStatus(id: string, status: "approved" | "suspended" | "pending") {
    if (!token) return;
    setBusyId(id);
    setError(null);
    try {
      await updateAdminVendor(token, id, status);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AdminShell title="Vendors" description="Approve or suspend shop vendor profiles.">
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {!token ? <LoadingState /> : null}
      {token && vendors.length === 0 ? <p>No vendor applications yet.</p> : null}
      {vendors.length > 0 ? (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {vendors.map((v) => (
              <tr key={v.id}>
                <td>
                  <div>{v.display_name}</div>
                  <div className={styles.muted}>{v.user_id}</div>
                </td>
                <td>{v.status}</td>
                <td>{new Date(v.created_at).toLocaleDateString()}</td>
                <td>
                  <button
                    type="button"
                    disabled={busyId === v.id || v.status === "approved"}
                    onClick={() => void setStatus(v.id, "approved")}
                  >
                    Approve
                  </button>{" "}
                  <button
                    type="button"
                    disabled={busyId === v.id || v.status === "suspended"}
                    onClick={() => void setStatus(v.id, "suspended")}
                  >
                    Suspend
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </AdminShell>
  );
}
