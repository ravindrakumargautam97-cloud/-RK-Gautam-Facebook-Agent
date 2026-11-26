
import os
import re
import argparse

from daily_post import read_history


# ==========================================
# RK GAUTAM SAFE POST RECOVERY
# ==========================================

RECOVERY_STATUSES = {
    "reserved",
    "needs_review",
    "submitted",
}


def show_record(post_id, record):

    print("=" * 50)
    print("Post ID:", post_id)
    print("Date:", record.get("date", "Unknown"))
    print("Slot:", record.get("slot", "Unknown"))
    print("Type:", record.get("type", "Unknown"))
    print("Status:", record.get("status", "Unknown"))
    print("Facebook ID:", record.get("facebook_id", "Unavailable"))
    print("Updated:", record.get("updated_at", "Unknown"))

    run_id = str(record.get("github_run_id", ""))
    repo = os.environ["GH_REPOSITORY"]

    if run_id.isdigit():

        print(
            "Recovery backup:",
            f"https://github.com/{repo}/actions/runs/{run_id}"
        )

    else:

        print("Recovery backup: Run ID unavailable")

    status = record.get("status")

    if status == "submitted":

        print("ACTION: Verify the post on Facebook.")
        print("Do not publish again.")

    elif status in ("reserved", "needs_review"):

        print("ACTION: Check Facebook Page first.")
        print("Download the original workflow artifact.")
        print("Review the original publishing error.")
        print("Do not retry automatically.")

    elif status == "published":

        print("ACTION: No recovery required.")

    print("=" * 50)


def main():

    parser = argparse.ArgumentParser(
        description="Safe Facebook post recovery report"
    )

    parser.add_argument(
        "--post-id",
        help="Post ID, for example 2026-11-26_08-00"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("RK GAUTAM SAFE RECOVERY AGENT")
    print("=" * 50)

    history, sha = read_history()

    if args.post_id:

        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}",
            args.post_id
        ):

            raise RuntimeError("Invalid Post ID format")

        if args.post_id not in history:

            raise RuntimeError("Post ID not found")

        show_record(
            args.post_id,
            history[args.post_id]
        )

    else:

        count = 0

        for post_id, record in sorted(
            history.items(),
            reverse=True
        ):

            if record.get("status") in RECOVERY_STATUSES:

                show_record(post_id, record)
                count += 1

        print("Records requiring verification:", count)

    print("=" * 50)
    print("RECOVERY REPORT COMPLETED")
    print("No Facebook posting")
    print("Posting history unchanged")
    print("Content history unchanged")
    print("=" * 50)


if __name__ == "__main__":

    main()
