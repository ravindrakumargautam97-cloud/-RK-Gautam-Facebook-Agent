import uuid
import content_history as ch


def main():

    print("=" * 45)
    print("PERMANENT DUPLICATE PROTECTION TEST")
    print("=" * 45)

    # Separate test file - production history is safe
    ch.HISTORY_FILE = "test_content_history.json"

    history, sha = ch.load_history()

    test_id = uuid.uuid4().hex

    categories = [
        "photos",
        "videos",
        "quotes",
        "music",
    ]

    # Save test records
    for category in categories:

        content_id = f"TEST_{category}_{test_id}"

        ch.mark_used(
            history,
            category,
            content_id,
            "test",
            "test_only"
        )

        print(f"Record created: {category}")

    ch.save_history(history, sha)

    # Reload permanent history from GitHub
    saved_history, _ = ch.load_history()

    for category in categories:

        content_id = f"TEST_{category}_{test_id}"

        assert ch.is_used(
            saved_history,
            category,
            content_id
        ), f"History missing: {category}"

        print(f"Permanent history verified: {category}")

        try:

            ch.mark_used(
                saved_history,
                category,
                content_id,
                "test"
            )

        except RuntimeError as error:

            if not str(error).startswith(
                "Duplicate content:"
            ):
                raise

            print(f"Duplicate blocked: {category}")

        else:

            raise RuntimeError(
                f"Duplicate protection failed: {category}"
            )

    print("=" * 45)
    print("ALL DUPLICATE PROTECTION TESTS PASSED")
    print("Production history unchanged")
    print("No Facebook posting")
    print("=" * 45)


if __name__ == "__main__":
    main()
