
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


# ==========================================
# RK GAUTAM FACEBOOK DAILY POSTING AGENT
# ==========================================

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

IST = ZoneInfo("Asia/Kolkata")


# ==========================================
# DATE AND TIME
# ==========================================

def now_ist():
    return datetime.now(IST).isoformat()


def today_ist():
    return datetime.now(IST).strftime("%Y-%m-%d")


# ==========================================
# GITHUB API
# ==========================================

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


# ==========================================
# READ POSTING HISTORY
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
            "Invalid posting history format"
        )

    return history, result["sha"]


# ==========================================
# SAVE POSTING HISTORY
# ==========================================

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


# ==========================================
# UPDATE POST STATUS
# ==========================================

def update_status(post_id, status):
    history, sha = read_history()

    if post_id not in history:
        raise RuntimeError(
            f"Reservation missing: {post_id}"
        )

    history[post_id]["status"] = status
    history[post_id]["updated_at"] = now_ist()

    write_history(
        history,
        sha,
        f"Facebook post {post_id}: {status}",
    )

    print(
        f"Posting history updated: {status}"
    )


# ==========================================
# MAIN POSTING AGENT
# ==========================================

def main():

    slot = os.getenv("POST_SLOT", "")

    dry_run = (
        os.getenv("DRY_RUN", "true").lower()
        == "true"
    )

    if slot not in SLOTS:
        sys.exit(
            f"Invalid POST_SLOT: {slot}"
        )

    today = today_ist()

    post_id = (
        f"{today}_{slot.replace(':', '-')}"
    )

    kind, number = SLOTS[slot]

    filename = (
        f"post_{number}.png"
        if kind == "photo"
        else f"reel_{number}.mp4"
    )

    media = OUTPUT / filename

    caption_file = (
        OUTPUT / f"caption_{number}.txt"
    )

    # ======================================
    # VERIFY FILES
    # ======================================

    for path in (media, caption_file):

        if not path.is_file():
            sys.exit(
                f"Missing file: {path}"
            )

        if path.stat().st_size == 0:
            sys.exit(
                f"Empty file: {path}"
            )

    caption = caption_file.read_text(
        encoding="utf-8"
    ).strip()

    if not caption:
        sys.exit("Caption is empty")

    print("=" * 40)
    print("RK GAUTAM FACEBOOK AI AGENT")
    print("=" * 40)

    print("Date:", today)
    print("Post ID:", post_id)
    print("Slot:", slot)
    print("Content:", kind, number)
    print("File:", media)

    # ======================================
    # SAFE DRY RUN
    # ======================================

    if dry_run:
        print("DRY RUN - Nothing published")
        print("No posting history changed")
        return

    # ======================================
    # CHECK REQUIRED CREDENTIALS
    # ======================================

    required = (
        "GH_TOKEN",
        "GH_REPOSITORY",
        "FACEBOOK_PAGE_ID",
        "FACEBOOK_PAGE_ACCESS_TOKEN",
    )

    for name in required:

        if not os.getenv(name):
            sys.exit(
                f"Missing environment variable: {name}"
            )

    # ======================================
    # CHECK DUPLICATE HISTORY
    # ======================================

    history, sha = read_history()

    if post_id in history:

        status = history[post_id].get(
            "status", "unknown"
        )

        print(
            "Already reserved or processed"
        )

        print(
            "Existing status:", status
        )

        print(
            "Skipping duplicate:", post_id
        )

        return

    # ======================================
    # RESERVE BEFORE FACEBOOK REQUEST
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
        "updated_at": now_ist(),
    }

    write_history(
        history,
        sha,
        f"Reserve Facebook post {post_id}",
    )

    print(
        "Reservation saved:", post_id
    )

    # ======================================
    # FACEBOOK PUBLISHING
    # ======================================

    os.environ["DRY_RUN"] = "false"

    from facebook_post import (
        post_photo,
        post_reel,
    )

    try:

        if kind == "photo":

            post_photo(
                media,
                caption,
            )

        else:

            post_reel(
                media,
                caption,
            )

    except Exception as error:

        print(
            "Facebook publishing failed "
            "or result uncertain."
        )

        print(
            "Error type:",
            type(error).__name__,
        )

        # ==================================
        # MARK NEEDS REVIEW
        # ==================================

        try:

            update_status(
                post_id,
                "needs_review",
            )

            print(
                "Status saved: needs_review"
            )

        except Exception as history_error:

            print(
                "Could not update "
                "posting history:",
                history_error,
            )

            print(
                "Original reservation "
                "requires manual review."
            )

        # Never automatically retry.
        raise

    # ======================================
    # MARK SUCCESSFUL API SUBMISSION
    # ======================================

    update_status(
        post_id,
        "submitted",
    )

    print(
        "Facebook API request completed"
    )

    print(
        "Post ID:", post_id
    )

    print(
        "Status: submitted"
    )


# ==========================================
# START AGENT
# ==========================================

if __name__ == "__main__":
    main()
