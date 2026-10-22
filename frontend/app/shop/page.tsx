"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import {
  ShopCategory,
  ShopProduct,
  Species,
  fetchShopCategories,
  fetchShopProducts,
  fetchSpecies,
  formatCents,
} from "@/lib/api";
import { trackFunnel } from "@/lib/funnel";

import styles from "./shop.module.css";

function ShopCatalog() {
  const searchParams = useSearchParams();
  const [categories, setCategories] = useState<ShopCategory[]>([]);
  const [species, setSpecies] = useState<Species[]>([]);
  const [products, setProducts] = useState<ShopProduct[]>([]);
  const [category, setCategory] = useState(searchParams.get("category") ?? "");
  const [speciesId, setSpeciesId] = useState("");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fromQuery = searchParams.get("category") ?? "";
    setCategory(fromQuery);
  }, [searchParams]);

  useEffect(() => {
    void trackFunnel("shop", "catalog_view", { path: "/shop" });
    Promise.all([fetchShopCategories(), fetchSpecies()])
      .then(([cats, sp]) => {
        setCategories(cats);
        setSpecies(sp.filter((s) => ["horse", "dog"].includes(s.name.toLowerCase()) || s.active_in_ui));
      })
      .catch(() => setError("Unable to load shop filters."));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchShopProducts({
      category: category || undefined,
      species_id: speciesId || undefined,
      q: q.trim() || undefined,
    })
      .then((res) => setProducts(res.items))
      .catch(() => setError("Unable to load products."))
      .finally(() => setLoading(false));
  }, [category, speciesId, q]);

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <div>
          <h1 className={styles.title}>Shop</h1>
          <p className={styles.subtitle}>
            Food and animal care supplies for horses, dogs, and more — shipped or local pickup.
          </p>
        </div>
        <div className={styles.navLinks}>
          <Link href="/shop/cart">Cart</Link>
          <Link href="/shop/orders">Orders</Link>
          <Link href="/shop/vendor">Vendor</Link>
        </div>
      </div>

      <div className={styles.filters}>
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
        <select value={speciesId} onChange={(e) => setSpeciesId(e.target.value)} aria-label="Animal type">
          <option value="">All animals</option>
          {species.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <input
          type="search"
          placeholder="Search products"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search"
        />
      </div>

      {error ? <p className={styles.error}>{error}</p> : null}
      {loading ? <p className={styles.empty}>Loading…</p> : null}
      {!loading && products.length === 0 ? (
        <p className={styles.empty}>No products yet. Check back soon.</p>
      ) : null}

      <div className={styles.grid}>
        {products.map((p) => (
          <Link key={p.id} href={`/shop/p/${p.id}`} className={styles.card}>
            <h2 className={styles.cardTitle}>{p.name}</h2>
            <p className={styles.cardMeta}>
              {p.category_name ?? "Supplies"}
              {p.species.length ? ` · ${p.species.map((s) => s.name).join(", ")}` : ""}
            </p>
            <p className={styles.price}>{formatCents(p.price_cents, p.currency)}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default function ShopHomePage() {
  return (
    <Suspense fallback={<div className={styles.page}><p className={styles.empty}>Loading…</p></div>}>
      <ShopCatalog />
    </Suspense>
  );
}
