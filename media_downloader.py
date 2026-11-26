
import os
import json
import time
import random
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageOps


# ==========================================
# RK GAUTAM SMART MEDIA DOWNLOADER
# ==========================================

BACKGROUND_DIR = Path("assets/backgrounds")

CACHE_DIR = Path(".pixabay-cache")
CACHE_SECONDS = 24 * 60 * 60

MAX_PHOTO_BYTES = 20 * 1024 * 1024
MAX_VIDEO_BYTES = 100 * 1024 * 1024

MEDIA_SOURCE = os.getenv(
    "MEDIA_SOURCE", "local"
).strip().lower()

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

LOCAL_THEMES = {
    "morning": "morning.jpg",
    "afternoon": "travel.jpg",
    "evening": "motivation.jpg",
    "night": "emotional.jpg",
}


# ==========================================
# DATE AND FILE HELPERS
# ==========================================

def today_ist():

    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date().isoformat()


def get_file_hash(path):

    digest = hashlib.sha256()

    with Path(path).open("rb") as file:

        for chunk in iter(
            lambda: file.read(65536), b""
        ):

            digest.update(chunk)

    return digest.hexdigest()


# ==========================================
# LOCAL BACKGROUND SELECTION
# ==========================================

def select_local_background(theme):

    theme_folder = BACKGROUND_DIR / theme

    supported = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    candidates = []

    if theme_folder.is_dir():

        candidates = sorted(
            path
            for path in theme_folder.iterdir()
            if path.is_file()
            and path.suffix.lower() in supported
        )

    if not candidates:

        preferred = (
            BACKGROUND_DIR / LOCAL_THEMES[theme]
        )

        if preferred.is_file():

            candidates = [preferred]

    if not candidates:

        candidates = sorted(
            path
            for path in BACKGROUND_DIR.glob("*")
            if path.is_file()
            and path.suffix.lower() in supported
        )

    if not candidates:

        raise RuntimeError(
            "No local background images found"
        )

    seed = hashlib.sha256(
        f"{today_ist()}-{theme}".encode()
    ).hexdigest()

    rng = random.Random(seed)

    return rng.choice(candidates)


# ==========================================
# CREATE LOCAL PHOTO
# ==========================================

def create_local_photo(source, destination):

    with Image.open(source) as image:

        image = ImageOps.exif_transpose(image)

        image = image.convert("RGB")

        image = ImageOps.fit(
            image,
            (1080, 1080),
            method=Image.Resampling.LANCZOS
        )

        image.save(
            destination,
            format="JPEG",
            quality=95
        )


# ==========================================
# CREATE ANIMATED BACKGROUND VIDEO
# ==========================================

def create_local_video(source, destination):

    prepared = destination.with_name(
        destination.stem + "_source.jpg"
    )

    try:

        with Image.open(source) as image:

            image = ImageOps.exif_transpose(image)

            image = image.convert("RGB")

            image = ImageOps.fit(
                image,
                (2160, 3840),
                method=Image.Resampling.LANCZOS
            )

            image.save(
                prepared,
                format="JPEG",
                quality=95
            )

        video_filter = (
            "zoompan="
            "z='min(zoom+0.00025,1.20)':"
            "x='iw/2-iw/zoom/2':"
            "y='ih/2-ih/zoom/2':"
            "d=750:"
            "s=1080x1920:"
            "fps=25"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i", str(prepared),
            "-vf", video_filter,
            "-t", "30",
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(destination),
        ]

        subprocess.run(
            command,
            check=True,
            timeout=300
        )

    finally:

        prepared.unlink(missing_ok=True)


# ==========================================
# LOCAL MEDIA MODE
# ==========================================

def local_media(
    theme,
    media_type,
    destination,
    used_ids=None
):

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    source = select_local_background(theme)

    source_hash = get_file_hash(source)

    used_ids = set(used_ids or [])

    # Local backgrounds may be reused.
    # Each daily use receives a separate history ID.

    base_id = (
        f"local:{media_type}:"
        f"{today_ist()}:{theme}:"
        f"{source_hash[:16]}"
    )

    media_id = base_id

    attempt = 1

    while media_id in used_ids:

        media_id = f"{base_id}:{attempt}"

        attempt += 1

    if media_type == "photo":

        create_local_photo(
            source,
            destination
        )

    else:

        create_local_video(
            source,
            destination
        )

    if (
        not destination.is_file()
        or destination.stat().st_size == 0
    ):

        raise RuntimeError(
            "Local media generation failed"
        )

    print("=" * 40)
    print("LOCAL MEDIA SUCCESS")
    print("=" * 40)

    print("Media source: LOCAL")
    print("Theme:", theme)
    print("Media type:", media_type)
    print("Background:", source)
    print("Media ID:", media_id)
    print("Output:", destination)
    print("Pixabay API not used")

    return {
        "id": media_id,
        "path": str(destination),
        "creator": "Local background collection",
        "source": str(source),
        "provider": "Local",
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

    try:

        response = requests.get(
            endpoint,
            params={
                **params,
                "key": key,
            },
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
# PIXABAY MEDIA MODE
# ==========================================

def pixabay_media(
    theme,
    media_type,
    destination,
    used_ids=None
):

    approved = os.getenv(
        "PIXABAY_APPROVED", "false"
    ).lower() == "true"

    if not approved:

        raise RuntimeError(
            "Pixabay permission is pending"
        )

    key = os.getenv("PIXABAY_API_KEY")

    if not key:

        raise RuntimeError(
            "Pixabay API Key missing"
        )

    used_ids = set(used_ids or [])

    seed = hashlib.sha256(
        f"{today_ist()}-{theme}-{media_type}".encode()
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

                continue

            if media_type == "photo":

                url = item.get("largeImageURL")

            else:

                medium = item.get(
                    "videos", {}
                ).get("medium", {})

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
                            "Invalid media type"
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

                    raise RuntimeError(
                        "Empty media file"
                    )

                temporary.replace(destination)

            except (
                requests.RequestException,
                RuntimeError,
                ValueError,
                OSError
            ):

                temporary.unlink(missing_ok=True)

                print("Media skipped:", media_id)

                continue

            print("PIXABAY MEDIA SUCCESS")
            print("Theme:", theme)
            print("Media ID:", media_id)
            print("Downloaded:", destination)

            return {
                "id": media_id,
                "path": str(destination),
                "creator": item.get("user", ""),
                "source": item.get("pageURL", ""),
                "provider": "Pixabay",
            }

    raise RuntimeError(
        f"No unused media found: {theme}/{media_type}"
    )


# ==========================================
# MAIN MEDIA SELECTOR
# ==========================================

def download_media(
    theme,
    media_type,
    destination,
    used_ids=None
):

    if theme not in THEMES:

        raise ValueError("Invalid theme")

    if media_type not in ("photo", "video"):

        raise ValueError("Invalid media type")

    print("Selected media source:", MEDIA_SOURCE)

    if MEDIA_SOURCE == "local":

        return local_media(
            theme,
            media_type,
            destination,
            used_ids
        )

    if MEDIA_SOURCE == "pixabay":

        return pixabay_media(
            theme,
            media_type,
            destination,
            used_ids
        )

    raise RuntimeError(
        f"Unsupported media source: {MEDIA_SOURCE}"
    )
