"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  ApiError,
  ShopCart,
  fetchShopCart,
  formatCents,
  updateShopCartItem,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

import styles from "../shop.module.css";

export default function ShopCartPage() {
  const router = useRouter();
  const [cart, setCart] = useState<ShopCart | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    const token = getToken();
    if (!token) {
      router.replace("/login?next=/shop/cart");
      return;
    }
    fetchShopCart(token)
      .then(setCart)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Unable to load cart.");
      });
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function setQty(itemId: string, qty: number) {
    const token = getToken();
    if (!token) return;
    try {
      const updated = await updateShopCartItem(token, itemId, qty);
      setCart(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update cart.");
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <div>
          <h1 className={styles.title}>Cart</h1>
          <p className={styles.subtitle}>Review items before checkout.</p>
        </div>
        <div className={styles.navLinks}>
          <Link href="/shop">Continue shopping</Link>
        </div>
      </div>

      {error ? <p className={styles.error}>{error}</p> : null}
      {!cart ? <p className={styles.empty}>Loading…</p> : null}
      {cart && cart.items.length === 0 ? (
        <p className={styles.empty}>Your cart is empty.</p>
      ) : null}

      {cart && cart.items.length > 0 ? (
        <>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              {cart.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <Link href={`/shop/p/${item.product_id}`}>{item.product_name}</Link>
                    <div className={styles.cardMeta}>{item.product_sku}</div>
                  </td>
                  <td>
                    <input
                      className={styles.qtyInput}
                      type="number"
                      min={0}
                      max={item.stock_qty}
                      value={item.qty}
                      onChange={(e) => void setQty(item.id, Number(e.target.value))}
                    />
                  </td>
                  <td>{formatCents(item.line_total_cents)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className={styles.price} style={{ marginTop: "1rem" }}>
            Subtotal: {formatCents(cart.subtotal_cents)}
          </p>
          <div className={styles.actions}>
            <Link href="/shop/checkout" className={styles.button}>
              Checkout
            </Link>
          </div>
        </>
      ) : null}
    </div>
  );
}
