"use client";

import { useEffect, useState } from "react";

import { fetchShopConfig } from "@/lib/api";
import { shouldShowStripeTestModeBanner } from "@/lib/stripeTestMode.mjs";

import styles from "./shop.module.css";

export default function ShopLayout({ children }: { children: React.ReactNode }) {
  const [showTestBanner, setShowTestBanner] = useState(false);

  useEffect(() => {
    fetchShopConfig()
      .then((config) => setShowTestBanner(shouldShowStripeTestModeBanner(config)))
      .catch(() => setShowTestBanner(false));
  }, []);

  return (
    <>
      {showTestBanner ? (
        <div className={styles.testModeBanner} role="status">
          Test mode — no real payments
        </div>
      ) : null}
      {children}
    </>
  );
}
