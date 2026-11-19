
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# IST hour/minute -> content
SLOTS = {
    "08:00": ("photo", 1),
    "10:00": ("reel", 1),
    "12:00": ("photo", 2),
    "14:00": ("reel", 2),
    "16:00": ("photo", 3),
    "18:00": ("reel", 3),
    "19:30": ("photo", 4),
    "21:00": ("reel", 4),
}

OUTPUT = Path("output")


def main():
    slot = os.getenv("POST_SLOT", "")
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if slot not in SLOTS:
        sys.exit(f"Invalid POST_SLOT: {slot}")

    kind, number = SLOTS[slot]

    filename = (
        f"post_{number}.png"
        if kind == "photo"
        else f"reel_{number}.mp4"
    )

    media = OUTPUT / filename
    caption_file = OUTPUT / f"caption_{number}.txt"

    for path in (media, caption_file):
        if not path.is_file() or path.stat().st_size == 0:
            sys.exit(f"Missing or empty file: {path}")

    caption = caption_file.read_text(
        encoding="utf-8"
    ).strip()

    if not caption:
        sys.exit("Caption is empty")

    print(f"Slot: {slot} IST")
    print(f"Content: {kind} {number}")
    print(f"File: {media}")

    if dry_run:
        print("DRY RUN - Nothing published")
        return

    if not os.getenv("FACEBOOK_PAGE_ID"):
        sys.exit("Missing FACEBOOK_PAGE_ID")

    if not os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"):
        sys.exit("Missing FACEBOOK_PAGE_ACCESS_TOKEN")

    # Import only after checking publishing mode.
    os.environ["DRY_RUN"] = "false"
    from facebook_post import post_photo, post_reel

    if kind == "photo":
        post_photo(media, caption)
    else:
        post_reel(media, caption)

    print("Facebook publishing API request completed")


if __name__ == "__main__":
    main()
