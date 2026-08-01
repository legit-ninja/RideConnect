#!/usr/bin/env bash
# Pull the live Phantom Equestrian logo into branding/ for later brand work.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT/branding"
SITE_URL="${SITE_URL:-https://phantomequestrian.com/}"
mkdir -p "$OUT_DIR"

TMP_HTML="$(mktemp)"
trap 'rm -f "$TMP_HTML"' EXIT

echo "==> Fetching ${SITE_URL}"
CURL_OPTS=(-fsSL -A "RideConnectBrandBot/1.0")
# Cert may be expired until SANs are expanded on 192.168.3.3
if [[ "${CURL_INSECURE:-1}" == "1" ]]; then
  CURL_OPTS+=(-k)
fi
curl "${CURL_OPTS[@]}" "$SITE_URL" -o "$TMP_HTML"

python3 - "$TMP_HTML" "$OUT_DIR" "$SITE_URL" <<'PY'
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

html_path = Path(sys.argv[1])
out_dir = Path(sys.argv[2])
base = sys.argv[3]
html = html_path.read_text(encoding="utf-8", errors="replace")

candidates: list[str] = []

# Custom logo / site icon patterns common on WordPress themes
patterns = [
    r'(?:property|name)=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
    r'content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']og:image["\']',
    r'rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\'][^>]*href=["\']([^"\']+)["\']',
    r'href=["\']([^"\']+)["\'][^>]*rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\']',
    r'class=["\'][^"\']*custom-logo[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
    r'src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*custom-logo[^"\']*["\']',
    r'id=["\'][^"\']*logo[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
    r'src=["\']([^"\']*logo[^"\']*\.(?:png|svg|jpg|jpeg|webp)[^"\']*)["\']',
    r'url\(([^)]+\.(?:png|svg|jpg|jpeg|webp)[^)]*)\)',
]

for pat in patterns:
    for match in re.finditer(pat, html, re.I):
        candidates.append(match.group(1).strip(" '\""))

# Dedupe while preserving order
seen: set[str] = set()
urls: list[str] = []
for raw in candidates:
    if raw.startswith("data:"):
        continue
    abs_url = urllib.parse.urljoin(base, raw)
    if abs_url not in seen:
        seen.add(abs_url)
        urls.append(abs_url)

if not urls:
    raise SystemExit("No logo/favicon candidates found in HTML — inspect branding/page-source.html")

(out_dir / "page-source.html").write_text(html, encoding="utf-8")
(out_dir / "candidates.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")
print(f"Found {len(urls)} candidate(s); downloading up to 8…")

downloaded = 0
for i, url in enumerate(urls[:8]):
    path = urllib.parse.urlparse(url).path
    ext = Path(path).suffix.lower() or ".bin"
    if ext not in {".png", ".svg", ".jpg", ".jpeg", ".webp", ".ico", ".gif", ".bin"}:
        ext = ".bin"
    dest = out_dir / f"logo-candidate-{i+1}{ext}"
    try:
        ctx = None
        if os.environ.get("CURL_INSECURE", "1") == "1":
            import ssl

            ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={"User-Agent": "RideConnectBrandBot/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            dest.write_bytes(resp.read())
        print(f"  wrote {dest.name} <- {url}")
        downloaded += 1
    except Exception as exc:  # noqa: BLE001
        print(f"  skip {url}: {exc}")

if downloaded == 0:
    raise SystemExit("Candidates listed but none downloaded")

# WordPress sized thumbs often have -NNxNN before the extension; try full-size siblings.
for url in list(urls)[:5]:
    full = re.sub(r"-\d+x\d+(?=\.(?:png|jpe?g|webp|svg)$)", "", url, flags=re.I)
    if full == url:
        continue
    dest = out_dir / "logo.png"
    if dest.exists() and dest.stat().st_size > 50_000:
        break
    try:
        ctx = None
        if os.environ.get("CURL_INSECURE", "1") == "1":
            import ssl

            ctx = ssl._create_unverified_context()
        req = urllib.request.Request(full, headers={"User-Agent": "RideConnectBrandBot/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = resp.read()
        if len(data) > 1000:
            dest.write_bytes(data)
            print(f"  wrote {dest.name} (full size) <- {full}")
    except Exception as exc:  # noqa: BLE001
        print(f"  skip full-size {full}: {exc}")

print(f"Done — review files in {out_dir}")
PY

echo "==> Also trying common WordPress paths…"
for path in \
  wp-content/uploads/logo.png \
  wp-content/uploads/logo.svg \
  wp-content/themes/logo.png \
  favicon.ico
do
  url="${SITE_URL%/}/${path}"
  out="$OUT_DIR/wp-$(basename "$path")"
  if curl "${CURL_OPTS[@]}" -o "$out" "$url" 2>/dev/null; then
    echo "  wrote $(basename "$out") <- $url"
  else
    rm -f "$out"
  fi
done

echo "==> Branding assets in ${OUT_DIR}"
