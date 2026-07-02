import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Script from "next/script";

import { SiteHeader } from "@/components/SiteHeader";
import { ThemeProvider } from "@/components/ThemeProvider";
import { THEME_INIT_SCRIPT } from "@/lib/theme";

import layoutStyles from "./layout.module.css";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RideConnect",
  description: "Trust-first marketplace for verified riding experiences",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <Script id="theme-init" strategy="beforeInteractive">
          {THEME_INIT_SCRIPT}
        </Script>
      </head>
      <body>
        <ThemeProvider>
          <SiteHeader />
          <main className={layoutStyles.main}>{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
