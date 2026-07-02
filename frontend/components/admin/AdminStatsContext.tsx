"use client";

import { createContext, ReactNode, useContext, useEffect, useState } from "react";

import { AdminStats, fetchAdminStats } from "@/lib/api";

const AdminStatsContext = createContext<AdminStats | null>(null);

interface AdminStatsProviderProps {
  token: string | null;
  children: ReactNode;
}

export function AdminStatsProvider({ token, children }: AdminStatsProviderProps) {
  const [stats, setStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    if (!token) {
      setStats(null);
      return;
    }

    fetchAdminStats(token)
      .then(setStats)
      .catch(() => {
        setStats(null);
      });
  }, [token]);

  return (
    <AdminStatsContext.Provider value={stats}>
      {children}
    </AdminStatsContext.Provider>
  );
}

export function useAdminStats(): AdminStats | null {
  return useContext(AdminStatsContext);
}
