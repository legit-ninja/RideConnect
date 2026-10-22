"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ShopOrder, fetchShopOrders, formatCents } from "@/lib/api";
import { getToken } from "@/lib/auth";

import styles from "../shop.module.css";

export default function ShopOrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login?next=/shop/orders");
      return;
    }
    fetchShopOrders(token)
      .then((res) => setOrders(res.items))
      .catch(() => setError("Unable to load orders."));
  }, [router]);

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <div>
          <h1 className={styles.title}>Orders</h1>
          <p className={styles.subtitle}>Your shop purchase history.</p>
        </div>
        <Link href="/shop">Shop</Link>
      </div>
      {error ? <p className={styles.error}>{error}</p> : null}
      {orders.length === 0 && !error ? (
        <p className={styles.empty}>No orders yet.</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Order</th>
              <th>Status</th>
              <th>Total</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>
                  <Link href={`/shop/orders/${o.id}`}>{o.id.slice(0, 8)}…</Link>
                </td>
                <td>{o.status}</td>
                <td>{formatCents(o.total_cents, o.currency)}</td>
                <td>{new Date(o.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
