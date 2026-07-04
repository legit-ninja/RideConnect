"use client";

import { useState } from "react";

const PLACEHOLDER_SRC = "/images/seed/horses/default.svg";

interface ListingImageProps {
  src?: string | null;
  alt: string;
  className?: string;
}

export function ListingImage({ src, alt, className }: ListingImageProps) {
  const [errored, setErrored] = useState(false);
  const resolvedSrc = src && !errored ? src : PLACEHOLDER_SRC;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={resolvedSrc}
      alt={alt}
      className={className}
      onError={() => setErrored(true)}
    />
  );
}
