# Copy to deploy/env.prod.sh or deploy/env.dev.sh before deploying.
# Plain KEY=VALUE format (no export). deploy.sh renders this into:
#   - <docroot>/app/.env   (Next.js — $ escaped for dotenv-expand)
#   - <docroot>/api/.env   (FastAPI / pydantic-settings)
# Do not commit files containing real secrets.
#
# Dev overrides (deploy/env.dev.sh):
#   NEXT_PUBLIC_API_URL=https://api.dev.phantomequestrian.com
#   NEXT_PUBLIC_SITE_URL=https://dev.phantomequestrian.com
#   API_INTERNAL_URL=http://127.0.0.1:8010
#   PORT=3010
#   API_PORT=8010
#   DATABASE_URL=...@127.0.0.1:5432/rideconnect
#   CORS_ORIGINS=https://dev.phantomequestrian.com,https://shop.dev.phantomequestrian.com
#   FRONTEND_BASE_URL=https://dev.phantomequestrian.com
#   NEXT_PUBLIC_SHOP_URL=https://shop.dev.phantomequestrian.com
#   NEXT_PUBLIC_AUTH_COOKIE_DOMAIN=.dev.phantomequestrian.com
#   PUBLIC_UPLOAD_BASE_URL=https://api.dev.phantomequestrian.com/uploads
#   *_REDIRECT_URI / FRONTEND_OAUTH_* → dev hosts
#   ENVIRONMENT=development
#
# Host Postgres on deploy server: ./scripts/server-db.sh dev|prod
# listens on 127.0.0.1:5432 (same idea as host MySQL for UU/SS).
# Prefer DB names: rideconnect (dev) and rideconnect_prod (prod).

# --- Next.js (web) ---
# Browser-facing API origin (must match Apache api vhost)
NEXT_PUBLIC_API_URL=https://api.phantomequestrian.com
# Public site branding (baked at Next build time — rebuild after change)
NEXT_PUBLIC_SITE_NAME=Phantom Equestrian
NEXT_PUBLIC_SITE_URL=https://phantomequestrian.com
NEXT_PUBLIC_SHOP_URL=https://shop.phantomequestrian.com
NEXT_PUBLIC_SITE_LOGO=/branding/mark.png
# JWT cookie Domain for apex + shop.* (dev: .dev.phantomequestrian.com)
NEXT_PUBLIC_AUTH_COOKIE_DOMAIN=.phantomequestrian.com
NEXT_PUBLIC_AUTH_COOKIE_NAME=pe_access_token
# SSR / server components call the API on localhost
API_INTERNAL_URL=http://127.0.0.1:8009
PORT=3009
NODE_ENV=production

# --- FastAPI ---
DATABASE_URL=postgresql://rideconnect:CHANGE_ME@127.0.0.1:5432/rideconnect_prod
JWT_SECRET=CHANGE_ME_LONG_RANDOM
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=https://phantomequestrian.com,https://www.phantomequestrian.com,https://shop.phantomequestrian.com
ADMIN_EMAIL=admin@phantomequestrian.com
ADMIN_PASSWORD=CHANGE_ME
LOCATION_JITTER_SECRET=CHANGE_ME
UPLOAD_ROOT=uploads
PUBLIC_UPLOAD_BASE_URL=https://api.phantomequestrian.com/uploads
FRONTEND_BASE_URL=https://phantomequestrian.com
PHOTO_MODERATION_ENABLED=false

# OAuth (fill when ready)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://api.phantomequestrian.com/auth/google/callback
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
FACEBOOK_REDIRECT_URI=https://api.phantomequestrian.com/auth/facebook/callback
FRONTEND_OAUTH_SUCCESS_URL=https://phantomequestrian.com/auth/callback
FRONTEND_OAUTH_ERROR_URL=https://phantomequestrian.com/auth/error

# Stripe (Checkout for shop; Connect later for multi-vendor)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_CONNECT_CLIENT_ID=
STRIPE_WEBHOOK_SECRET=
PLATFORM_COMMISSION_PERCENT=10

# Search defaults (Appalachian NC)
SEARCH_DEFAULT_LAT=36.2168
SEARCH_DEFAULT_LNG=-81.6746
SEARCH_DEFAULT_RADIUS_KM=80
WEATHER_TIMEZONE=America/New_York
WEATHER_CACHE_TTL_SECONDS=10800

# Never seed production
SEED_DEV_DATA=false
ENVIRONMENT=production

# --- API listen port (systemd also sets this; keep in sync) ---
API_PORT=8009
