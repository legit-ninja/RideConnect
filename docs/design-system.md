# RideConnect design system

Semantic tokens, theme modes, and visual conventions for the RideConnect frontend.

## Stack

- Next.js App Router + TypeScript
- CSS modules (`admin.module.css`, `marketplace.module.css`, `auth.module.css`)
- **No Tailwind / shadcn** — all colors via CSS custom properties in `frontend/app/globals.css`

## Theme modes

| Preference | `data-theme` on `<html>` | Behavior |
|------------|--------------------------|----------|
| Light | `light` | Warm stone palette, forest green accent |
| Dark | `dark` | Dark stone palette, lighter green accent |
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
| `--primary` / `--primary-foreground` / `--primary-hover` | Primary buttons, active nav |
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

| Token | Value |
|-------|-------|
| `--font-sans` | Geist Sans + system fallback |
| `--text-xs` … `--text-2xl` | 12, 14, 16, 18, 28 px |

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
