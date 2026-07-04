from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routers import (
    admin,
    auth,
    bookings,
    events,
    friend_invites,
    invite_tokens,
    listings,
    oauth,
    owner,
    public,
    reviews,
    species,
)
from app.seed import ensure_admin_user

app = FastAPI(
    title="RideConnect API",
    description="Trust-first marketplace for verified riding experiences",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret)

upload_path = Path(settings.upload_root)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(admin.router)
app.include_router(species.router)
app.include_router(listings.router)
app.include_router(public.router)
app.include_router(owner.router)
app.include_router(friend_invites.router)
app.include_router(invite_tokens.router)
app.include_router(bookings.router)
app.include_router(reviews.router)
app.include_router(events.router)


@app.on_event("startup")
def on_startup() -> None:
    ensure_admin_user()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
