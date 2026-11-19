
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from daily_post import read_history, write_history

def main():
    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%Y-%m-%d")

    test_id = f"TEST_{today}_08-00"

    history, sha = read_history()

    if test_id in history:
        print("Duplicate protection working!")
        print("Already reserved:", test_id)
        return

    history[test_id] = {
        "date": today,
        "slot": "08:00",
        "type": "test",
        "status": "reserved",
        "test_only": True,
    }

    write_history(
        history,
        sha,
        f"Test Facebook reservation {test_id}",
    )

    print("TEST RESERVATION SAVED:", test_id)
    print("No Facebook post published")


if __name__ == "__main__":
    main()
