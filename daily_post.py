
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

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
BRANCH = "facebook-posting-history"
HISTORY_FILE = "posting_history.json"


def github_headers():
    token = os.environ["GH_TOKEN"]
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def history_url():
    repo = os.environ["GH_REPOSITORY"]
    return (
        f"https://api.github.com/repos/{repo}"
        f"/contents/{HISTORY_FILE}"
    )


def read_history():
    response = requests.get(
        history_url(),
        headers=github_headers(),
        params={"ref": BRANCH},
        timeout=30,
    )
    response.raise_for_status()

    result = response.json()
    content = base64.b64decode(
        result["content"]
    ).decode("utf-8")

    history = json.loads(content)

    if not isinstance(history, dict):
        raise RuntimeError("Invalid history format")

    return history, result["sha"]


def write_history(history, sha, message):
    content = json.dumps(
        history,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    response = requests.put(
        history_url(),
        headers=github_headers(),
        json={
            "message": message,
            "content": base64.b64encode(
                content
            ).decode("ascii"),
            "sha": sha,
            "branch": BRANCH,
        },
        timeout=30,
    )
    response.raise_for_status()


def main():
    slot = os.getenv("POST_SLOT", "")
    dry_run = (
        os.getenv("DRY_RUN", "true").lower()
        == "true"
    )

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
        sys.exit("Caption is empty")

    print("Post ID:", post_id)
    print("Content:", kind, number)

    if dry_run:
        print("DRY RUN - Nothing published")
        print("No posting history changed")
        return

    required = (
        "GH_TOKEN",
        "GH_REPOSITORY",
        "FACEBOOK_PAGE_ID",
        "FACEBOOK_PAGE_ACCESS_TOKEN",
    )

    for name in required:
        if not os.getenv(name):
            sys.exit(f"Missing environment variable: {name}")

    history, sha = read_history()

    if post_id in history:
        print("Already reserved or processed")
        print("Skipping duplicate:", post_id)
        return

    history[post_id] = {
        "date": today,
        "slot": slot,
        "type": kind,
        "number": number,
        "status": "reserved",
        "github_run_id": os.getenv(
            "GITHUB_RUN_ID", ""
        ),
        "updated_at": datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).isoformat(),
    }

    # Save reservation BEFORE calling Facebook.
    write_history(
        history,
        sha,
        f"Reserve Facebook post {post_id}",
    )

    print("Reservation saved:", post_id)

    os.environ["DRY_RUN"] = "false"
    from facebook_post import post_photo, post_reel

    try:
        if kind == "photo":
            post_photo(media, caption)
        else:
            post_reel(media, caption)
    except Exception:
        # The API may have accepted the post.
        # Do not automatically retry this slot.
        print(
            "Facebook result uncertain. "
            "Manual review required."
        )
        raise

    # Reload latest SHA before updating.
    history, sha = read_history()

    history[post_id]["status"] = "submitted"
    history[post_id]["updated_at"] = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).isoformat()

    write_history(
        history,
        sha,
        f"Mark Facebook post submitted {post_id}",
    )

    print("Facebook request completed:", post_id)


if __name__ == "__main__":
    main()
