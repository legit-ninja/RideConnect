"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, User, fetchCurrentUser } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

interface UseAdminAuthResult {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

export function useAdminAuth(): UseAdminAuthResult {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = getToken();
    if (!storedToken) {
      router.replace("/login");
      return;
    }

    fetchCurrentUser(storedToken)
      .then((currentUser) => {
        if (!currentUser.is_admin) {
          router.replace("/dashboard");
          return;
        }
        setUser(currentUser);
        setTokenState(storedToken);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
          router.replace("/login");
          return;
        }
        if (err instanceof ApiError && err.status === 403) {
          router.replace("/dashboard");
          return;
        }
        setError("Unable to verify admin access.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [router]);

  return { user, token, loading, error };
}
