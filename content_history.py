
import os
import json
import base64
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import requests


BRANCH = "facebook-posting-history"
HISTORY_FILE = "content_history.json"
IST = ZoneInfo("Asia/Kolkata")

CATEGORIES = (
    "photos",
    "videos",
    "quotes",
    "music",
)


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


def empty_history():

    return {
        category: {}
        for category in CATEGORIES
    }


def load_history():

    response = requests.get(
        history_url(),
        headers=github_headers(),
        params={"ref": BRANCH},
        timeout=30
    )

    if response.status_code == 404:

        repo = os.environ["GH_REPOSITORY"]

        branch_response = requests.get(
            f"https://api.github.com/repos/{repo}/branches/{BRANCH}",
            headers=github_headers(),
            timeout=30
        )

        branch_response.raise_for_status()

        print("Starting new content history")

        return empty_history(), None

    response.raise_for_status()

    result = response.json()

    content = base64.b64decode(
        result["content"]
    ).decode("utf-8")

    history = json.loads(content)

    for category in CATEGORIES:

        if not isinstance(
            history.get(category), dict
        ):
            raise RuntimeError(
                f"Invalid history: {category}"
            )

    print("Content history loaded")

    return history, result["sha"]


def save_history(history, sha):

    content = json.dumps(
        history,
        ensure_ascii=False,
        indent=2
    ).encode("utf-8")

    payload = {
        "message": "Update daily content history",
        "content": base64.b64encode(
            content
        ).decode("ascii"),
        "branch": BRANCH,
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        history_url(),
        headers=github_headers(),
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    print("Content history saved successfully")


def get_used_ids(history, category):

    return set(
        history[category].keys()
    )


def is_used(history, category, content_id):

    return content_id in history[category]


def mark_used(
    history,
    category,
    content_id,
    theme,
    source=""
):

    if is_used(
        history, category, content_id
    ):
        raise RuntimeError(
            f"Duplicate content: {content_id}"
        )

    history[category][content_id] = {
        "theme": theme,
        "source": source,
        "used_at": datetime.now(
            IST
        ).isoformat(),
    }


def file_hash(path):

    digest = hashlib.sha256()

    with Path(path).open("rb") as file:

        for chunk in iter(
            lambda: file.read(65536), b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def print_summary(history):

    print("=" * 40)
    print("CONTENT HISTORY SUMMARY")
    print("=" * 40)

    for category in CATEGORIES:

        print(
            category,
            ":",
            len(history[category])
        )
