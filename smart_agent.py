
import os
import asyncio
from pathlib import Path

from agent import create_voice

from media_downloader import download_media
from music_generator import generate_music
from quote_generator import generate_quote

from design_generator import (
    create_photo,
    create_reel,
    get_duration,
)

from content_history import (
    load_history,
    save_history,
    get_used_ids,
    mark_used,
    file_hash,
    print_summary,
)


OUTPUT = Path("output")
WORK = Path("work")

OUTPUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)


SLOTS = {
    "08:00": ("morning", "photo", 1),
    "09:40": ("morning", "photo", 1),
    "10:00": ("morning", "reel", 1),

    "12:00": ("afternoon", "photo", 2),
    "14:00": ("afternoon", "reel", 2),

    "16:00": ("evening", "photo", 3),
    "18:00": ("evening", "reel", 3),

    "19:30": ("night", "photo", 4),
    "21:00": ("night", "reel", 4),
}


async def main():

    slot = os.getenv(
        "POST_SLOT", "08:00"
    ).strip()

    test_mode = (
        os.getenv("TEST_MODE", "true").lower()
        == "true"
    )

    if slot not in SLOTS:
        raise RuntimeError(
            f"Invalid slot: {slot}"
        )

    theme, kind, number = SLOTS[slot]

    print("=" * 45)
    print("RK GAUTAM SMART AI AGENT")
    print("=" * 45)
    print("Slot:", slot)
    print("Theme:", theme)
    print("Content:", kind)
    print("Test mode:", test_mode)

    # Load permanent content history

    history, sha = load_history()

    print_summary(history)

    # Generate unused quote

    quote = generate_quote(
        theme,
        kind,
        get_used_ids(history, "quotes")
    )

    title = quote["title"]
    lines = quote["lines"]

    if kind == "reel":
        title = {
            "morning": "MORNING MOTIVATION",
            "afternoon": "KEEP GOING",
            "evening": "EVENING MOTIVATION",
            "night": "PEACEFUL NIGHT",
        }[theme]

    # Generate photo

    if kind == "photo":

        media = download_media(
            theme,
            "photo",
            WORK / "background.jpg",
            get_used_ids(history, "photos")
        )

        destination = (
            OUTPUT / f"post_{number}.png"
        )

        create_photo(
            media["path"],
            destination,
            theme,
            title,
            lines
        )

        mark_used(
            history,
            "photos",
            media["id"],
            theme,
            media["source"]
        )

    # Generate moving reel

    else:

        media = download_media(
            theme,
            "video",
            WORK / "background.mp4",
            get_used_ids(history, "videos")
        )

        voice = WORK / "voice.mp3"

        await create_voice(
            " ".join(lines),
            voice
        )

        duration = max(
            20.0,
            get_duration(voice) + 2.5
        )

        music = generate_music(
            theme,
            WORK / "music.wav",
            duration
        )

        music_id = file_hash(music)

        if music_id in get_used_ids(
            history, "music"
        ):
            raise RuntimeError(
                "Duplicate music detected"
            )

        destination = (
            OUTPUT / f"reel_{number}.mp4"
        )

        create_reel(
            media["path"],
            voice,
            music,
            destination,
            theme,
            title,
            lines
        )

        mark_used(
            history,
            "videos",
            media["id"],
            theme,
            media["source"]
        )

        mark_used(
            history,
            "music",
            music_id,
            theme
        )

    # Generate caption

    caption = quote["caption"].replace(
        quote["title"],
        title,
        1
    )

    caption += (
        "\n\n"
        f"Background: {media['creator']} / Pixabay"
        f"\n{media['source']}"
    )

    caption_file = (
        OUTPUT / f"caption_{number}.txt"
    )

    caption_file.write_text(
        caption,
        encoding="utf-8"
    )

    mark_used(
        history,
        "quotes",
        quote["id"],
        theme
    )

    # Validate generated files

    for path in (
        destination,
        caption_file
    ):

        if not path.is_file():
            raise RuntimeError(
                f"Missing file: {path}"
            )

        if path.stat().st_size == 0:
            raise RuntimeError(
                f"Empty file: {path}"
            )

    # Save content history

    if test_mode:

        print("TEST MODE: History unchanged")
        print("No Facebook posting")

    else:

        save_history(history, sha)

    print_summary(history)

    print("=" * 45)
    print("CONTENT GENERATED SUCCESSFULLY")
    print("File:", destination)
    print("Caption:", caption_file)
    print("=" * 45)


if __name__ == "__main__":

    asyncio.run(main())
