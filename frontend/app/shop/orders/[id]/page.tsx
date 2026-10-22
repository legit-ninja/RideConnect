"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { ShopOrder, fetchShopOrder, formatCents } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { trackFunnel } from "@/lib/funnel";

import styles from "../../shop.module.css";

function OrderDetail() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const orderId = params.id as string;
  const [order, setOrder] = useState<ShopOrder | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace(`/login?next=/shop/orders/${orderId}`);
      return;
    }
    fetchShopOrder(token, orderId)
      .then((o) => {
        setOrder(o);
        if (searchParams.get("paid") === "1" || o.status === "paid") {
          void trackFunnel("shop", "payment_complete", {
            path: `/shop/orders/${orderId}`,
            payload: { order_id: orderId },
          });
        }
      })
      .catch(() => setError("Unable to load order."));
  }, [orderId, router, searchParams]);

  if (error) {
    return <p className={styles.error}>{error}</p>;
  }
  if (!order) {
    return <p className={styles.empty}>Loading…</p>;
  }

  return (
    <>
      <h1 className={styles.title}>Order {order.id.slice(0, 8)}…</h1>
      <p className={styles.cardMeta}>
        Status: {order.status} · {order.fulfillment_type}
      </p>
      {searchParams.get("paid") === "1" ? (
        <p className={styles.success}>Payment recorded. Thank you.</p>
      ) : null}
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Item</th>
            <th>Qty</th>
            <th>Price</th>
          </tr>
        </thead>
        <tbody>
          {order.items.map((item) => (
            <tr key={item.id}>
              <td>
                {item.product_name}
                <div className={styles.cardMeta}>{item.product_sku}</div>
              </td>
              <td>{item.qty}</td>
              <td>{formatCents(item.unit_price_cents * item.qty)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className={styles.price} style={{ marginTop: "1rem" }}>
        Total: {formatCents(order.total_cents, order.currency)}
      </p>
      {order.fulfillment_type === "ship" && order.ship_line1 ? (
        <p className={styles.subtitle}>
          Ship to: {order.ship_name}, {order.ship_line1}
          {order.ship_line2 ? `, ${order.ship_line2}` : ""}, {order.ship_city},{" "}
          {order.ship_state} {order.ship_postal}
        </p>
      ) : null}
    </>
  );
}

export default function ShopOrderDetailPage() {
  return (
    <div className={styles.page}>
      <div className={styles.navLinks} style={{ marginBottom: "1rem" }}>
        <Link href="/shop/orders">← Orders</Link>
      </div>
      <Suspense fallback={<p className={styles.empty}>Loading…</p>}>
        <OrderDetail />
      </Suspense>
    </div>
  );
}
