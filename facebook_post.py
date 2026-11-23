
import os
import sys
import time
from pathlib import Path

import requests

# ==========================================
# RK GAUTAM FACEBOOK PUBLISHING AGENT
# ==========================================

API_VERSION = "v27.0"
GRAPH_URL = f"https://graph.facebook.com/{API_VERSION}"

PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

OUTPUT = Path("output")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


# ==========================================
# FACEBOOK API ERROR HANDLING
# ==========================================

def check_response(response):
    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(
            f"Facebook returned HTTP {response.status_code}"
        )

    if not response.ok or "error" in result:
        error = result.get("error", {})
        if not isinstance(error, dict):
            error = {"message": str(error)}

        code = error.get("code", "unknown")
        message = error.get("message", "Unknown error")

        raise RuntimeError(
            f"Facebook API error {code}: {message}"
        )

    return result


def credentials():
    if not PAGE_ID or not PAGE_TOKEN:
        raise RuntimeError(
            "Missing Facebook Page credentials"
        )


# ==========================================
# PHOTO PUBLISHING
# ==========================================

def post_photo(photo_path, caption):
    photo_path = Path(photo_path)

    if not photo_path.is_file():
        raise FileNotFoundError(photo_path)

    if DRY_RUN:
        print(f"[DRY RUN] Photo: {photo_path}")
        return {"status": "dry_run"}

    credentials()

    url = f"{GRAPH_URL}/{PAGE_ID}/photos"

    with photo_path.open("rb") as photo:
        response = requests.post(
            url,
            data={
                "access_token": PAGE_TOKEN,
                "caption": caption,
                "published": "true",
            },
            files={"source": photo},
            timeout=180,
        )

    result = check_response(response)

    photo_id = result.get("id")

    if not photo_id:
        raise RuntimeError(
            "Facebook did not return a photo ID"
        )

    print(f"Photo submitted: {photo_id}")

    return {
        "status": "submitted",
        "type": "photo",
        "facebook_id": photo_id,
    }


# ==========================================
# REEL PUBLISHING
# ==========================================

def post_reel(video_path, caption):
    video_path = Path(video_path)

    if not video_path.is_file():
        raise FileNotFoundError(video_path)

    if DRY_RUN:
        print(f"[DRY RUN] Reel: {video_path}")
        return {"status": "dry_run"}

    credentials()

    # STEP 1: START UPLOAD

    start = requests.post(
        f"{GRAPH_URL}/{PAGE_ID}/video_reels",
        data={
            "access_token": PAGE_TOKEN,
            "upload_phase": "start",
        },
        timeout=60,
    )

    info = check_response(start)

    video_id = info.get("video_id")
    upload_url = info.get("upload_url")

    if not video_id or not upload_url:
        raise RuntimeError(
            "Facebook did not return video upload details"
        )

    print(f"Reel upload started: {video_id}")

    # STEP 2: UPLOAD VIDEO

    file_size = video_path.stat().st_size

    with video_path.open("rb") as video:
        upload = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {PAGE_TOKEN}",
                "offset": "0",
                "file_size": str(file_size),
                "Content-Type": "application/octet-stream",
            },
            data=video,
            timeout=600,
        )

    check_response(upload)

    print("Reel upload completed")

    # STEP 3: REQUEST PUBLISHING

    finish = requests.post(
        f"{GRAPH_URL}/{PAGE_ID}/video_reels",
        data={
            "access_token": PAGE_TOKEN,
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption,
        },
        timeout=120,
    )

    result = check_response(finish)

    if result.get("success") is not True:
        raise RuntimeError(
            "Reel publishing was not confirmed by API"
        )

    print(f"Reel publishing accepted: {video_id}")

    return {
        "status": "submitted",
        "type": "reel",
        "facebook_id": video_id,
    }


# ==========================================
# MANUAL SCRIPT EXECUTION
# ==========================================

def main():
    if not DRY_RUN:
        credentials()

    errors = []

    for i in range(1, 5):
        photo = OUTPUT / f"post_{i}.png"
        reel = OUTPUT / f"reel_{i}.mp4"
        caption_file = OUTPUT / f"caption_{i}.txt"

        if not caption_file.is_file():
            errors.append(
                f"Missing caption: {caption_file}"
            )
            continue

        caption = caption_file.read_text(
            encoding="utf-8"
        ).strip()

        if not caption:
            errors.append(
                f"Empty caption: {caption_file}"
            )
            continue

        for kind, path, publish in (
            ("photo", photo, post_photo),
            ("reel", reel, post_reel),
        ):
            try:
                result = publish(path, caption)
                print(f"{kind} {i}: {result['status']}")
            except Exception as exc:
                errors.append(
                    f"{kind} {i}: {type(exc).__name__}: {exc}"
                )

            time.sleep(2)

    if errors:
        for error in errors:
            print("ERROR:", error)
        sys.exit(1)

    print("All content processed successfully")


if __name__ == "__main__":
    main()
