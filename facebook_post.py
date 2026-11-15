
import os
import sys
from pathlib import Path

import requests

PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")

API_VERSION = "v27.0"


def post_photo(photo_path, caption):
    url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/photos"

    with open(photo_path, "rb") as photo:
        response = requests.post(
            url,
            data={
                "access_token": PAGE_TOKEN,
                "caption": caption,
            },
            files={"source": photo},
            timeout=120,
        )

    response.raise_for_status()
    print(f"Photo posted: {photo_path}")


def main():
    if not PAGE_ID or not PAGE_TOKEN:
        sys.exit("Missing Facebook Page ID or Access Token")

    output = Path("output")

    for i in range(1, 5):
        photo = output / f"post_{i}.png"
        caption_file = output / f"caption_{i}.txt"

        if not photo.exists() or not caption_file.exists():
            print(f"Skipping missing files for post {i}")
            continue

        caption = caption_file.read_text(encoding="utf-8")
        post_photo(photo, caption)


if __name__ == "__main__":
    main()
