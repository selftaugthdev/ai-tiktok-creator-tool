"""Pexels photo search + download helper.

Downloads portrait photos to photos/pexels_cache/ and returns
the path relative to photos/ so the existing renderer works unchanged.
"""

import os
import re
from pathlib import Path

import requests

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
PEXELS_CACHE_DIR = Path("photos") / "pexels_cache"


def _api_key() -> str:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key or key == "your-pexels-api-key-here":
        raise EnvironmentError(
            "PEXELS_API_KEY is not set. Add it to your .env file."
        )
    return key


def _slug(query: str, photo_id: int) -> str:
    """Turn a query + Pexels photo ID into a safe filename."""
    safe = re.sub(r"[^a-z0-9]+", "_", query.lower())[:60].strip("_")
    return f"{safe}_{photo_id}.jpg"


def fetch_photo(query: str) -> str:
    """Search Pexels for *query*, download the best portrait result.

    Returns the path relative to photos/ (e.g. "pexels_cache/feet_hot_water_12345.jpg").
    Caches by query+id so the same search never downloads twice.
    """
    headers = {"Authorization": _api_key()}
    params = {
        "query": query,
        "orientation": "portrait",
        "size": "large",
        "per_page": 5,
    }

    resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    photos = resp.json().get("photos", [])

    if not photos:
        raise ValueError(f"No Pexels results for query: {query!r}")

    photo = photos[0]
    # 'large2x' gives ~1880px tall for portrait images — ideal for our 1920px canvas
    download_url = photo["src"].get("large2x") or photo["src"]["large"]
    photo_id = photo["id"]

    PEXELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    filename = _slug(query, photo_id)
    cache_path = PEXELS_CACHE_DIR / filename

    if not cache_path.exists():
        img_resp = requests.get(download_url, timeout=30)
        img_resp.raise_for_status()
        cache_path.write_bytes(img_resp.content)

    # Return path relative to photos/ so renderer's `PHOTOS_DIR / bg_rel` resolves correctly
    return str(Path("pexels_cache") / filename)
