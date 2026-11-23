
import base64
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

# ==========================================
# RK GAUTAM FACEBOOK DAILY POSTING AGENT
# ==========================================

SLOTS = {
    "08:00": ("photo", 1),
    "09:40": ("photo", 1),
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
IST = ZoneInfo("Asia/Kolkata")

# GitHub scheduled workflows may start late.
MAX_DELAY_MINUTES = 90


def now_ist():
    return datetime.now(IST)


def now_string():
    return now_ist().isoformat()


def github_headers():
    return {
        "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def history_url():
    repo = os.environ["GH_REPOSITORY"]
    return (
        f"https://api.github.com/repos/{repo}"
        f"/contents/{HISTORY_FILE}"
    )


# ==========================================
# POSTING HISTORY
# ==========================================

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
        raise RuntimeError(
            "Posting history must be a JSON object"
        )

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


def update_status(post_id, status, facebook_id=None):
    history, sha = read_history()

    if post_id not in history:
        raise RuntimeError(
            f"Missing reservation: {post_id}"
        )

    record = history[post_id]
    record["status"] = status
    record["updated_at"] = now_string()

    if facebook_id:
        record["facebook_id"] = str(facebook_id)

    write_history(
        history,
        sha,
        f"Facebook post {post_id}: {status}",
    )

    print(f"History updated: {status}")


# ==========================================
# VALIDATE POSTING TIME
# ==========================================

def validate_time(slot):
    current = now_ist()

    hour, minute = map(int, slot.split(":"))

    scheduled = current.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    delay = current - scheduled

    if delay < timedelta(0):
        raise RuntimeError(
            f"Posting slot {slot} has not started yet"
        )

    if delay > timedelta(minutes=MAX_DELAY_MINUTES):
        raise RuntimeError(
            f"Posting slot {slot} is too old"
        )

    return current


# ==========================================
# MAIN
# ==========================================

def main():
    slot = os.getenv("POST_SLOT", "").strip()

    dry_run = (
        os.getenv("DRY_RUN", "true").lower()
        == "true"
    )

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
        if not path.is_file():
            raise FileNotFoundError(path)

        if path.stat().st_size == 0:
            raise RuntimeError(f"Empty file: {path}")

    caption = caption_file.read_text(
        encoding="utf-8"
    ).strip()

    if not caption:
        raise RuntimeError("Caption is empty")

    current = now_ist()
    today = current.strftime("%Y-%m-%d")
    post_id = f"{today}_{slot.replace(':', '-')}"

    print("=" * 45)
    print("RK GAUTAM FACEBOOK AI AGENT")
    print("=" * 45)
    print("Post ID:", post_id)
    print("Slot:", slot)
    print("Type:", kind)
    print("File:", media)
    print("DRY RUN:", dry_run)

    # ======================================
    # DRY RUN
    # ======================================

    if dry_run:
        print("DRY RUN - No Facebook post")
        print("Posting history unchanged")
        return

    # ======================================
    # REQUIRED ENVIRONMENT VARIABLES
    # ======================================

    required = (
        "GH_TOKEN",
        "GH_REPOSITORY",
        "FACEBOOK_PAGE_ID",
        "FACEBOOK_PAGE_ACCESS_TOKEN",
    )

    for name in required:
        if not os.getenv(name):
            raise RuntimeError(
                f"Missing environment variable: {name}"
            )

    # Validate before making any changes.
    validate_time(slot)

    # ======================================
    # DUPLICATE PROTECTION
    # ======================================

    history, sha = read_history()

    if post_id in history:
        existing = history[post_id]

        print("Post already recorded")
        print(
            "Existing status:",
            existing.get("status", "unknown")
        )
        print("Skipping duplicate:", post_id)
        return

    # ======================================
    # RESERVE POST
    # ======================================

    history[post_id] = {
        "date": today,
        "slot": slot,
        "type": kind,
        "number": number,
        "status": "reserved",
        "github_run_id": os.getenv(
            "GITHUB_RUN_ID", ""
        ),
        "updated_at": now_string(),
    }

    write_history(
        history,
        sha,
        f"Reserve Facebook post {post_id}",
    )

    print("Reservation saved:", post_id)

    # ======================================
    # PUBLISH TO FACEBOOK
    # ======================================

    os.environ["DRY_RUN"] = "false"

    try:
        from facebook_post import (
            post_photo,
            post_reel,
        )

        if kind == "photo":
            result = post_photo(media, caption)
        else:
            result = post_reel(media, caption)

        if not isinstance(result, dict):
            raise RuntimeError(
                "Invalid Facebook publishing result"
            )

        facebook_id = result.get("facebook_id")

        if not facebook_id:
            raise RuntimeError(
                "Facebook ID missing from API result"
            )

    except Exception as error:
        print(
            "Facebook publishing failed "
            "or outcome is uncertain"
        )
        print("Error type:", type(error).__name__)
        print("Error:", error)

        try:
            update_status(
                post_id,
                "needs_review",
            )
        except Exception as history_error:
            print(
                "Could not save review status:",
                history_error,
            )

        raise

    # ======================================
    # SAVE FACEBOOK SUBMISSION
    # ======================================

    update_status(
        post_id,
        "submitted",
        facebook_id=facebook_id,
    )

    print("Facebook API submission accepted")
    print("Facebook ID:", facebook_id)
    print("Status: submitted")
    print(
        "Verify Facebook publishing status "
        "before marking as published"
    )


if __name__ == "__main__":
    main()
