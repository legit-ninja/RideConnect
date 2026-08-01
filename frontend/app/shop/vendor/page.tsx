"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  ApiError,
  ShopCategory,
  ShopOrder,
  ShopProduct,
  Species,
  createVendorProduct,
  fetchShopCategories,
  fetchSpecies,
  fetchVendorOrders,
  fetchVendorProducts,
  formatCents,
  fulfillVendorOrder,
  updateVendorProduct,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { trackFunnel } from "@/lib/funnel";

import styles from "../shop.module.css";

export default function ShopVendorPage() {
  const router = useRouter();
  const [products, setProducts] = useState<ShopProduct[]>([]);
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [categories, setCategories] = useState<ShopCategory[]>([]);
  const [species, setSpecies] = useState<Species[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [priceDollars, setPriceDollars] = useState("19.99");
  const [stockQty, setStockQty] = useState("10");
  const [categoryId, setCategoryId] = useState("");
  const [speciesId, setSpeciesId] = useState("");
  const [busy, setBusy] = useState(false);

  function reload(token: string) {
    return Promise.all([
      fetchVendorProducts(token),
      fetchVendorOrders(token),
      fetchShopCategories(),
      fetchSpecies(),
    ]).then(([prod, ord, cats, sp]) => {
      setProducts(prod.items);
      setOrders(ord.items);
      setCategories(cats);
      setSpecies(sp);
      if (!categoryId && cats[0]) setCategoryId(cats[0].id);
    });
  }

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login?next=/shop/vendor");
      return;
    }
    reload(token).catch((err: unknown) => {
      setError(
        err instanceof ApiError
          ? err.message
          : "Vendor access required (approved vendor or admin).",
      );
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const price_cents = Math.round(Number(priceDollars) * 100);
      await createVendorProduct(token, {
        category_id: categoryId,
        sku,
        name,
        description: description || undefined,
        price_cents,
        stock_qty: Number(stockQty),
        species_ids: speciesId ? [speciesId] : [],
      });
      setSku("");
      setName("");
      setDescription("");
      setMessage("Product created.");
      await reload(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create product.");
    } finally {
      setBusy(false);
    }
  }

  async function adjustStock(product: ShopProduct, delta: number) {
    const token = getToken();
    if (!token) return;
    try {
      await updateVendorProduct(token, product.id, {
        stock_qty: Math.max(0, product.stock_qty + delta),
      });
      await reload(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Stock update failed.");
    }
  }

  async function markFulfilled(order: ShopOrder) {
    const token = getToken();
    if (!token) return;
    const next =
      order.fulfillment_type === "pickup" ? "picked_up" : "shipped";
    try {
      await fulfillVendorOrder(token, order.id, next);
      void trackFunnel("shop", "order_fulfilled", {
        path: "/shop/vendor",
        payload: { order_id: order.id, status: next },
      });
      await reload(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Fulfillment update failed.");
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <div>
          <h1 className={styles.title}>Vendor inventory</h1>
          <p className={styles.subtitle}>
            Manage first-party catalog SKUs and fulfill orders.
          </p>
        </div>
        <Link href="/shop">Shop</Link>
      </div>

      {error ? <p className={styles.error}>{error}</p> : null}
      {message ? <p className={styles.success}>{message}</p> : null}

      <h2 className={styles.cardTitle}>Add product</h2>
      <form className={styles.form} onSubmit={(e) => void handleCreate(e)}>
        <label>
          SKU
          <input required value={sku} onChange={(e) => setSku(e.target.value)} />
        </label>
        <label>
          Name
          <input required value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Description
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
        </label>
        <label>
          Category
          <select required value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Animal type (optional)
          <select value={speciesId} onChange={(e) => setSpeciesId(e.target.value)}>
            <option value="">None</option>
            {species.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Price (USD)
          <input
            required
            type="number"
            min={0}
            step="0.01"
            value={priceDollars}
            onChange={(e) => setPriceDollars(e.target.value)}
          />
        </label>
        <label>
          Stock
          <input
            required
            type="number"
            min={0}
            value={stockQty}
            onChange={(e) => setStockQty(e.target.value)}
          />
        </label>
        <button className={styles.button} type="submit" disabled={busy}>
          {busy ? "Saving…" : "Create product"}
        </button>
      </form>

      <h2 className={styles.cardTitle} style={{ marginTop: "2rem" }}>
        Products
      </h2>
      {products.length === 0 ? (
        <p className={styles.empty}>No products yet.</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Name</th>
              <th>SKU</th>
              <th>Price</th>
              <th>Stock</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td>
                  <Link href={`/shop/p/${p.id}`}>{p.name}</Link>
                  {!p.active ? <span className={styles.cardMeta}> (inactive)</span> : null}
                </td>
                <td>{p.sku}</td>
                <td>{formatCents(p.price_cents)}</td>
                <td>{p.stock_qty}</td>
                <td>
                  <button
                    type="button"
                    className={styles.buttonSecondary}
                    onClick={() => void adjustStock(p, 1)}
                  >
                    +1
                  </button>{" "}
                  <button
                    type="button"
                    className={styles.buttonSecondary}
                    onClick={() => void adjustStock(p, -1)}
                  >
                    −1
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2 className={styles.cardTitle} style={{ marginTop: "2rem" }}>
        Orders to fulfill
      </h2>
      {orders.length === 0 ? (
        <p className={styles.empty}>No orders.</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Order</th>
              <th>Status</th>
              <th>Total</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>{o.id.slice(0, 8)}…</td>
                <td>
                  {o.status} / {o.fulfillment_type}
                </td>
                <td>{formatCents(o.total_cents)}</td>
                <td>
                  {o.status === "paid" || o.status === "fulfilling" ? (
                    <button
                      type="button"
                      className={styles.button}
                      onClick={() => void markFulfilled(o)}
                    >
                      Mark {o.fulfillment_type === "pickup" ? "picked up" : "shipped"}
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
