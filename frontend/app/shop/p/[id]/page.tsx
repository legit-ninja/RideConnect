"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  ApiError,
  ShopProduct,
  addToShopCart,
  fetchShopProduct,
  formatCents,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { trackFunnel } from "@/lib/funnel";

import styles from "../../shop.module.css";

export default function ShopProductPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;
  const [product, setProduct] = useState<ShopProduct | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchShopProduct(productId)
      .then((p) => {
        setProduct(p);
        void trackFunnel("shop", "product_view", {
          path: `/shop/p/${productId}`,
          payload: { product_id: productId },
        });
      })
      .catch(() => setError("Product not found."));
  }, [productId]);

  async function handleAdd() {
    const token = getToken();
    if (!token) {
      router.push(`/login?next=/shop/p/${productId}`);
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await addToShopCart(token, productId, 1);
      void trackFunnel("shop", "add_to_cart", {
        path: `/shop/p/${productId}`,
        payload: { product_id: productId },
      });
      setMessage("Added to cart.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add to cart.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !product) {
    return (
      <div className={styles.page}>
        <p className={styles.error}>{error}</p>
        <Link href="/shop">Back to shop</Link>
      </div>
    );
  }

  if (!product) {
    return (
      <div className={styles.page}>
        <p className={styles.empty}>Loading…</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.navLinks} style={{ marginBottom: "1rem" }}>
        <Link href="/shop">← Shop</Link>
        <Link href="/shop/cart">Cart</Link>
      </div>
      <div className={styles.detail}>
        <div>
          <h1 className={styles.title}>{product.name}</h1>
          <p className={styles.cardMeta}>
            {product.category_name} · SKU {product.sku}
            {product.species.length
              ? ` · ${product.species.map((s) => s.name).join(", ")}`
              : ""}
          </p>
          <p className={styles.price} style={{ fontSize: "1.4rem", marginTop: "1rem" }}>
            {formatCents(product.price_cents, product.currency)}
          </p>
          <p className={styles.subtitle} style={{ marginTop: "1rem" }}>
            {product.description || "No description yet."}
          </p>
          <p className={styles.cardMeta}>
            {product.stock_qty > 0 ? `${product.stock_qty} in stock` : "Out of stock"}
          </p>
          <div className={styles.actions}>
            <button
              type="button"
              className={styles.button}
              disabled={busy || product.stock_qty < 1}
              onClick={() => void handleAdd()}
            >
              {busy ? "Adding…" : "Add to cart"}
            </button>
            <Link href="/shop/cart" className={styles.buttonSecondary}>
              View cart
            </Link>
          </div>
          {message ? <p className={styles.success}>{message}</p> : null}
          {error ? <p className={styles.error}>{error}</p> : null}
        </div>
      </div>
    </div>
  );
}
