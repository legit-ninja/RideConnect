from pathlib import Path

from app.config import settings


def _upload_root() -> Path:
    root = Path(settings.upload_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def put_object(relative_key: str, data: bytes) -> str:
    path = _upload_root() / relative_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return relative_key


def get_public_url(storage_key: str) -> str:
    base = settings.public_upload_base_url.rstrip("/")
    return f"{base}/{storage_key}"
