
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

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
HISTORY = Path("posting_history.json")


def load_history():
    if not HISTORY.exists():
        return {}

    with open(HISTORY, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    temp = HISTORY.with_suffix(".tmp")
    temp.write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp.replace(HISTORY)


def main():
    slot = os.getenv("POST_SLOT", "")
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if slot not in SLOTS:
        sys.exit(f"Invalid POST_SLOT: {slot}")

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%Y-%m-%d")

    post_id = f"{today}_{slot.replace(':', '-')}"

    kind, number = SLOTS[slot]
    media = OUTPUT / (
        f"post_{number}.png"
        if kind == "photo"
        else f"reel_{number}.mp4"
    )
    caption_file = OUTPUT / f"caption_{number}.txt"

    for path in (media, caption_file):
        if not path.is_file() or path.stat().st_size == 0:
            sys.exit(f"Missing or empty file: {path}")

    caption = caption_file.read_text(
        encoding="utf-8"
    ).strip()

    if not caption:
        sys.exit("Empty caption")

    history = load_history()

    if post_id in history:
        print(f"Already processed: {post_id}")
        print("Skipping duplicate post")
        return

    print(f"Date: {today}")
    print(f"Slot: {slot}")
    print(f"Content: {kind} {number}")
    print(f"File: {media}")

    if dry_run:
        print("DRY RUN - Nothing published")
        return

    if not os.getenv("FACEBOOK_PAGE_ID"):
        sys.exit("Missing FACEBOOK_PAGE_ID")

    if not os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"):
        sys.exit("Missing FACEBOOK_PAGE_ACCESS_TOKEN")

    os.environ["DRY_RUN"] = "false"
    from facebook_post import post_photo, post_reel

    if kind == "photo":
        post_photo(media, caption)
    else:
        post_reel(media, caption)

    history[post_id] = {
        "date": today,
        "slot": slot,
        "type": kind,
        "number": number,
        "status": "submitted",
    }

    save_history(history)

    print(f"History updated: {post_id}")
    print("Facebook API request completed")


if __name__ == "__main__":
    main()
