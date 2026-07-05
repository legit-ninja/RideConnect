# RideConnect design system

Semantic tokens, theme modes, and visual conventions for the RideConnect frontend.

## Stack

- Next.js App Router + TypeScript
- CSS modules (`admin.module.css`, `marketplace.module.css`, `auth.module.css`)
- Shared utilities in `frontend/app/utilities.css` (hero overlay, card hover, section eyebrow)
- **No Tailwind / shadcn** — all colors via CSS custom properties in `frontend/app/globals.css`

## Theme modes

| Preference | `data-theme` on `<html>` | Behavior |
|------------|--------------------------|----------|
| Light | `light` | Warm stone palette, gold accent, Cormorant headings |
| Dark | `dark` | Deep forest palette, lighter gold accent |
| System | `light` or `dark` | Follows OS `prefers-color-scheme`; updates live when OS changes |
| High contrast | `high-contrast` | Black/white with high-visibility accents (accessibility) |

Toggle: **Site header** → Theme radiogroup (Light / Dark / System / High contrast).

Persistence: `localStorage` key `rideconnect-theme`.

FOUC prevention: inline script in `app/layout.tsx` runs before first paint.

## Token reference

Hex values are defined **only** in [`frontend/app/globals.css`](../frontend/app/globals.css). Component CSS must use `var(--token-name)`.

### Color (light mode defaults)

| Token | Purpose |
|-------|---------|
| `--background` / `--foreground` | Page surface and text |
| `--muted` / `--muted-foreground` | Subtle backgrounds and de-emphasized text |
| `--border` / `--border-subtle` | Dividers, table borders |
| `--primary` / `--primary-foreground` / `--primary-hover` | Primary buttons, active nav (gold accent) |
| `--accent` / `--accent-foreground` | Deep forest contrast sections, hero backgrounds |
| `--destructive` / `--destructive-foreground` | Danger actions, errors |
| `--success-bg` / `--success-fg` | Verified badges, success alerts |
| `--warning-bg` / `--warning-fg` | Unverified badges, warnings |
| `--info-bg` / `--info-fg` | Pending badges, info alerts |
| `--error-bg` / `--error-fg` | Rejected badges, error alerts |
| `--accent-bg` / `--accent-fg` | Friends-only badges |
| `--card` / `--card-border` | Cards, dialogs |
| `--input-border` | Form fields |
| `--focus-ring` | Keyboard focus outline |
| `--hover-bg` / `--table-header-bg` / `--table-row-hover` | Interactive surfaces |

### Spacing

| Token | Value |
|-------|-------|
| `--space-1` … `--space-6` | 4, 8, 12, 16, 24, 32 px |
| `--page-padding-x` / `--page-padding-y` | 24 px |
| `--section-gap` | 24 px between major sections |
| `--content-max-admin` | 1200 px |
| `--content-max-marketplace` | 960 px |

### Typography

Inspired by [Equestrian Stockholm](https://equestrianstockholm.com/) — light sans body, editorial serif headings, wide-tracked uppercase nav and CTAs. Uses Google Font substitutes (no Adobe Typekit):

| Role | Substitute for | Loaded via |
|------|----------------|------------|
| Body / UI | Proxima Nova → **Montserrat** (300, 500, 600) | `next/font/google` in `layout.tsx` |
| Headings | Operetta 12 → **Cormorant Garamond** (400, 600) | `next/font/google` in `layout.tsx` |

| Token | Value |
|-------|-------|
| `--font-sans` | Montserrat + system fallback |
| `--font-heading` | Cormorant Garamond + Georgia fallback |
| `--font-body-weight` | 300 |
| `--font-heading-weight` | 400 |
| `--letter-spacing-body` | 0.03em |
| `--letter-spacing-heading` | 0.03em |
| `--letter-spacing-nav` | 0.08em (uppercase nav, eyebrows) |
| `--letter-spacing-button` | 0.2em (uppercase CTAs) |
| `--letter-spacing-product-title` | 0.08em (listing card titles) |
| `--text-xs` … `--text-4xl` | 12, 14, 16, 18, 22, 28, 36, 48 px |
| Body default size | 18px (`--text-lg`) |

Utilities in `utilities.css`: `.textEyebrow`, `.textProductTitle`, `.fontHeading`, `.sectionEyebrow`.

### Radius

| Token | Value |
|-------|-------|
| `--radius-sm` | 6 px |
| `--radius-md` | 8 px |
| `--radius-full` | pill badges |

## Module boundaries

| Module | Used by |
|--------|---------|
| `globals.css` | All pages — tokens only |
| `admin.module.css` | `/admin/*` components |
| `marketplace.module.css` | Marketplace pages and components |
| `auth.module.css` | `/login`, `/register` |
| `layout.module.css` | Site header and main shell |
| `utilities.css` | Global layout utilities (hero overlay, card hover) |
| `SiteFooter.module.css` | Site footer |
| `ThemeToggle.module.css` | Header theme control |

Do **not** cross-import admin components into marketplace pages (or vice versa). Share **tokens**, not components.

## Manual test matrix

Dev workflow: `make dev-api` + `cd frontend && npm run dev`.

For each route, verify in **all four** theme preferences:

| Route | Check |
|-------|-------|
| `/login` | Form fields, primary button, focus ring |
| `/` | Landing typography, links |
| `/dashboard` | Hub sections, verification banner |
| `/listings`, `/listings/[id]` | Cards, filters, booking flow |
| `/owner/friends`, `/owner/bookings` | Tables, badges, actions |
| `/rider/bookings` | Status badges with text labels |
| `/admin`, `/admin/users`, `/admin/verification`, `/admin/bookings` | Sidebar, tables, stat cards |

**Per theme:**

- [ ] Preference persists after hard refresh
- [ ] No flash of wrong theme on load
- [ ] Status badges readable (color + text label)
- [ ] Tab focus shows visible ring on links, buttons, inputs
- [ ] High contrast: strong borders, no low-contrast gray body text

**System mode test:** Set preference to System, then change OS appearance (or Chrome DevTools → Rendering → emulate `prefers-color-scheme`). Page should update without reload.

## Agent guidance

- `.cursor/rules/rideconnect-theming.mdc` — token and theme rules
- `.cursor/rules/rideconnect-a11y.mdc` — accessibility checklist
- `.cursor/skills/ui-ux-design/rideconnect-design-tokens.md` — full token table for agents
