import os
import json
import time
import random
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


CACHE_DIR = Path(".pixabay-cache")
CACHE_SECONDS = 24 * 60 * 60

MAX_PHOTO_BYTES = 20 * 1024 * 1024
MAX_VIDEO_BYTES = 100 * 1024 * 1024

THEMES = {
    "morning": [
        "sunrise mountains",
        "morning nature",
        "golden sunrise",
        "morning forest",
    ],
    "afternoon": [
        "sunny landscape",
        "green mountains",
        "blue sky nature",
        "sunny waterfall",
    ],
    "evening": [
        "sunset mountains",
        "evening landscape",
        "golden sunset",
        "sunset lake",
    ],
    "night": [
        "moon stars night",
        "night mountains",
        "starry sky",
        "moonlight lake",
    ],
}


# ==========================================
# PIXABAY API CACHE
# ==========================================

def cached_search(endpoint, params, key):

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    cache_id = hashlib.sha256(
        json.dumps(
            [endpoint, params],
            sort_keys=True
        ).encode()
    ).hexdigest()

    cache_file = CACHE_DIR / f"{cache_id}.json"

    if cache_file.exists():

        try:
            cached = json.loads(
                cache_file.read_text(
                    encoding="utf-8"
                )
            )

            age = time.time() - cached["timestamp"]

            if 0 <= age < CACHE_SECONDS:

                print("Pixabay CACHE HIT")

                return cached["response"]

        except (ValueError, KeyError, OSError):
            pass

    print("Pixabay CACHE MISS")

    request_params = {
        **params,
        "key": key,
    }

    try:

        response = requests.get(
            endpoint,
            params=request_params,
            timeout=30
        )

    except requests.RequestException:

        raise RuntimeError(
            "Pixabay connection failed"
        ) from None

    if response.status_code != 200:

        raise RuntimeError(
            f"Pixabay HTTP {response.status_code}"
        )

    try:
        data = response.json()

    except ValueError:

        raise RuntimeError(
            "Invalid Pixabay response"
        ) from None

    temporary = cache_file.with_suffix(".tmp")

    temporary.write_text(
        json.dumps({
            "timestamp": time.time(),
            "response": data,
        }, ensure_ascii=False),
        encoding="utf-8"
    )

    temporary.replace(cache_file)

    print("API response cached for 24 hours")

    return data


# ==========================================
# MEDIA DOWNLOADER
# ==========================================

def download_media(
    theme,
    media_type,
    destination,
    used_ids=None
):

    key = os.getenv("PIXABAY_API_KEY")

    if not key:
        raise RuntimeError("Pixabay API Key missing")

    if theme not in THEMES:
        raise ValueError("Invalid theme")

    if media_type not in ("photo", "video"):
        raise ValueError("Invalid media type")

    used_ids = set(used_ids or [])

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date().isoformat()

    seed = hashlib.sha256(
        f"{today}-{theme}-{media_type}".encode()
    ).hexdigest()

    rng = random.Random(seed)

    queries = THEMES[theme].copy()
    rng.shuffle(queries)

    endpoint = (
        "https://pixabay.com/api/"
        if media_type == "photo"
        else "https://pixabay.com/api/videos/"
    )

    max_bytes = (
        MAX_PHOTO_BYTES
        if media_type == "photo"
        else MAX_VIDEO_BYTES
    )

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    for query in queries:

        params = {
            "q": query,
            "safesearch": "true",
            "per_page": 50,
            "order": "popular",
            "category": "nature",
        }

        if media_type == "photo":

            params["image_type"] = "photo"
            params["min_width"] = 1080

        else:

            params["video_type"] = "film"

        data = cached_search(
            endpoint,
            params,
            key
        )

        hits = list(data.get("hits", []))

        rng.shuffle(hits)

        for item in hits:

            media_id = f"{media_type}:{item['id']}"

            if media_id in used_ids:

                print("Duplicate skipped:", media_id)
                continue

            if media_type == "photo":

                url = item.get("largeImageURL")

            else:

                videos = item.get("videos", {})

                medium = videos.get("medium", {})

                if medium.get("size", 0) > max_bytes:
                    continue

                url = medium.get("url")

            if not url:
                continue

            temporary = destination.with_suffix(
                destination.suffix + ".part"
            )

            try:

                with requests.get(
                    url,
                    stream=True,
                    timeout=(15, 90)
                ) as download:

                    download.raise_for_status()

                    expected_type = (
                        "image/"
                        if media_type == "photo"
                        else "video/"
                    )

                    content_type = download.headers.get(
                        "Content-Type", ""
                    ).lower()

                    if not content_type.startswith(
                        expected_type
                    ):

                        raise RuntimeError(
                            "Invalid media type received"
                        )

                    length = int(
                        download.headers.get(
                            "Content-Length", 0
                        )
                    )

                    if length > max_bytes:
                        raise RuntimeError(
                            "Media exceeds size limit"
                        )

                    downloaded_bytes = 0

                    with temporary.open("wb") as file:

                        for chunk in download.iter_content(
                            chunk_size=65536
                        ):

                            if not chunk:
                                continue

                            downloaded_bytes += len(chunk)

                            if downloaded_bytes > max_bytes:
                                raise RuntimeError(
                                    "Download size limit reached"
                                )

                            file.write(chunk)

                if temporary.stat().st_size == 0:
                    raise RuntimeError("Empty media file")

                temporary.replace(destination)

            except (
                requests.RequestException,
                RuntimeError,
                ValueError,
                OSError
            ):

                temporary.unlink(missing_ok=True)

                print("Media download skipped:", media_id)

                continue

            print("=" * 40)
            print("MEDIA DOWNLOAD SUCCESS")
            print("=" * 40)

            print("Theme:", theme)
            print("Media type:", media_type)
            print("Media ID:", media_id)
            print("Creator:", item.get("user", ""))
            print("Source:", item.get("pageURL", ""))
            print("Downloaded:", destination)

            return {
                "id": media_id,
                "path": str(destination),
                "creator": item.get("user", ""),
                "source": item.get("pageURL", ""),
            }

    raise RuntimeError(
        f"No unused media found: {theme}/{media_type}"
    )
