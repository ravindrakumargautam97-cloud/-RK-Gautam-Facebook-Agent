
import os
import random
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


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


def download_media(
    theme,
    media_type,
    destination,
    used_ids=None
):

    key = os.getenv("PIXABAY_API_KEY")

    if not key:
        raise RuntimeError("Pixabay API Key missing")

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

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    for query in queries:

        params = {
            "key": key,
            "q": query,
            "safesearch": "true",
            "per_page": 50,
            "order": "popular",
        }

        if media_type == "photo":
            params["image_type"] = "photo"
            params["min_width"] = 1080
        else:
            params["video_type"] = "film"

        try:
            response = requests.get(
                endpoint,
                params=params,
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

        hits = response.json().get("hits", [])

        rng.shuffle(hits)

        for item in hits:

            media_id = (
                f"{media_type}:{item['id']}"
            )

            if media_id in used_ids:
                continue

            if media_type == "photo":
                url = item.get("largeImageURL")
            else:
                videos = item.get("videos", {})
                url = videos.get(
                    "medium", {}
                ).get("url")

            if not url:
                continue

            temporary = destination.with_suffix(
                destination.suffix + ".part"
            )

            try:
                with requests.get(
                    url,
                    stream=True,
                    timeout=90
                ) as download:

                    download.raise_for_status()

                    with temporary.open("wb") as file:
                        for chunk in download.iter_content(
                            chunk_size=65536
                        ):
                            if chunk:
                                file.write(chunk)

                if temporary.stat().st_size == 0:
                    raise RuntimeError("Empty media file")

                temporary.replace(destination)

            except Exception:
                temporary.unlink(missing_ok=True)
                continue

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
