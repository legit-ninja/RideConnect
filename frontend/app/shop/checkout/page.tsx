"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  ApiError,
  FulfillmentType,
  ShopCart,
  fetchShopCart,
  formatCents,
  shopCheckout,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { trackFunnel } from "@/lib/funnel";

import styles from "../shop.module.css";

export default function ShopCheckoutPage() {
  const router = useRouter();
  const [cart, setCart] = useState<ShopCart | null>(null);
  const [fulfillment, setFulfillment] = useState<FulfillmentType>("ship");
  const [shipName, setShipName] = useState("");
  const [shipLine1, setShipLine1] = useState("");
  const [shipLine2, setShipLine2] = useState("");
  const [shipCity, setShipCity] = useState("");
  const [shipState, setShipState] = useState("");
  const [shipPostal, setShipPostal] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login?next=/shop/checkout");
      return;
    }
    fetchShopCart(token)
      .then((c) => {
        setCart(c);
        if (c.items.length === 0) {
          router.replace("/shop/cart");
        }
      })
      .catch(() => router.replace("/login?next=/shop/checkout"));
  }, [router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      void trackFunnel("shop", "checkout_start", { path: "/shop/checkout" });
      const result = await shopCheckout(token, {
        fulfillment_type: fulfillment,
        ship_name: fulfillment === "ship" ? shipName : undefined,
        ship_line1: fulfillment === "ship" ? shipLine1 : undefined,
        ship_line2: fulfillment === "ship" ? shipLine2 || undefined : undefined,
        ship_city: fulfillment === "ship" ? shipCity : undefined,
        ship_state: fulfillment === "ship" ? shipState : undefined,
        ship_postal: fulfillment === "ship" ? shipPostal : undefined,
        ship_country: "US",
      });
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
        return;
      }
      router.push(`/shop/orders/${result.order_id}?paid=1`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Checkout failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <div>
          <h1 className={styles.title}>Checkout</h1>
          <p className={styles.subtitle}>
            Identity verification is not required for shop purchases.
          </p>
        </div>
        <Link href="/shop/cart">Back to cart</Link>
      </div>

      {cart ? (
        <p className={styles.price}>Subtotal: {formatCents(cart.subtotal_cents)}</p>
      ) : null}

      <form className={styles.form} onSubmit={(e) => void handleSubmit(e)}>
        <label>
          Fulfillment
          <select
            value={fulfillment}
            onChange={(e) => setFulfillment(e.target.value as FulfillmentType)}
          >
            <option value="ship">Ship to address</option>
            <option value="pickup">Local pickup</option>
          </select>
        </label>

        {fulfillment === "ship" ? (
          <>
            <label>
              Full name
              <input required value={shipName} onChange={(e) => setShipName(e.target.value)} />
            </label>
            <label>
              Address line 1
              <input required value={shipLine1} onChange={(e) => setShipLine1(e.target.value)} />
            </label>
            <label>
              Address line 2
              <input value={shipLine2} onChange={(e) => setShipLine2(e.target.value)} />
            </label>
            <label>
              City
              <input required value={shipCity} onChange={(e) => setShipCity(e.target.value)} />
            </label>
            <label>
              State
              <input required value={shipState} onChange={(e) => setShipState(e.target.value)} />
            </label>
            <label>
              Postal code
              <input required value={shipPostal} onChange={(e) => setShipPostal(e.target.value)} />
            </label>
          </>
        ) : null}

        {error ? <p className={styles.error}>{error}</p> : null}
        <button className={styles.button} type="submit" disabled={busy}>
          {busy ? "Processing…" : "Place order"}
        </button>
      </form>
    </div>
  );
}
