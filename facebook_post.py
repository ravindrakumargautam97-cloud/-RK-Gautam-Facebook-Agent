
import os
import sys
import time
from pathlib import Path

import requests

PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
API_VERSION = "v27.0"

OUTPUT = Path("output")
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"


def check_response(response):
    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(
            f"Facebook returned HTTP {response.status_code}"
        )

    if not response.ok or "error" in result:
        error = result.get("error", {})
        raise RuntimeError(
            f"Facebook API error: {error.get('message', result)}"
        )

    return result


def post_photo(photo_path, caption):
    if DRY_RUN:
        print(f"[TEST] Photo ready: {photo_path}")
        return

    url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/photos"

    with open(photo_path, "rb") as photo:
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
    print(f"Photo published: {result.get('id')}")


def post_reel(video_path, caption):
    if DRY_RUN:
        print(f"[TEST] Reel ready: {video_path}")
        return

    # Step 1: Start Reel upload
    start = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/video_reels",
        data={
            "access_token": PAGE_TOKEN,
            "upload_phase": "start",
        },
        timeout=60,
    )

    info = check_response(start)
    video_id = info["video_id"]
    upload_url = info["upload_url"]

    # Step 2: Upload MP4 file
    file_size = video_path.stat().st_size

    with open(video_path, "rb") as video:
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

    # Step 3: Finish and publish Reel
    finish = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/video_reels",
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
    print(f"Reel publish requested: {video_id}")
    print(result)


def main():
    if not DRY_RUN and (not PAGE_ID or not PAGE_TOKEN):
        sys.exit("Missing Facebook Page credentials")

    errors = []

    for i in range(1, 5):
        photo = OUTPUT / f"post_{i}.png"
        reel = OUTPUT / f"reel_{i}.mp4"
        caption_file = OUTPUT / f"caption_{i}.txt"

        if not caption_file.exists():
            errors.append(f"Missing caption: {caption_file}")
            continue

        caption = caption_file.read_text(encoding="utf-8")

        if photo.exists():
            try:
                post_photo(photo, caption)
            except Exception as exc:
                errors.append(f"Photo {i}: {exc}")
        else:
            errors.append(f"Missing photo: {photo}")

        if reel.exists():
            try:
                post_reel(reel, caption)
            except Exception as exc:
                errors.append(f"Reel {i}: {exc}")
        else:
            errors.append(f"Missing reel: {reel}")

        time.sleep(2)

    if errors:
        for error in errors:
            print("ERROR:", error)
        sys.exit(1)

    print("All 4 photos and 4 reels processed!")


if __name__ == "__main__":
    main()
