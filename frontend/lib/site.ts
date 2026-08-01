export const siteConfig = {
  name: process.env.NEXT_PUBLIC_SITE_NAME ?? "Phantom Equestrian",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  shopUrl: process.env.NEXT_PUBLIC_SHOP_URL ?? process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  logo: process.env.NEXT_PUBLIC_SITE_LOGO ?? "/branding/mark.png",
};
