"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ShopCategoryRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const category = params.category as string;

  useEffect(() => {
    router.replace(`/shop?category=${encodeURIComponent(category)}`);
  }, [category, router]);

  return null;
}
