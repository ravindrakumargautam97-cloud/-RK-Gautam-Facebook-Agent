
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


# ==========================================
# RK GAUTAM SMART AI AGENT
# ==========================================

OUTPUT = Path("output")
WORK = Path("work")

OUTPUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)

MEDIA_SOURCE = os.getenv(
    "MEDIA_SOURCE", "local"
).strip().lower()


# ==========================================
# DAILY POSTING SCHEDULE
# ==========================================

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


# ==========================================
# MEDIA CREDIT
# ==========================================

def generate_media_credit(media):

    provider = media.get(
        "provider", ""
    ).strip().lower()

    creator = media.get("creator", "")
    source = media.get("source", "")

    if provider == "pixabay":

        return (
            "\n\n"
            f"Background: {creator} / Pixabay"
            f"\n{source}"
        )

    if provider == "local":

        return (
            "\n\n"
            "Background: Local media collection"
        )

    raise RuntimeError(
        "Unknown media provider"
    )


# ==========================================
# MAIN SMART AGENT
# ==========================================

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

    if MEDIA_SOURCE not in (
        "local", "pixabay"
    ):

        raise RuntimeError(
            f"Invalid media source: {MEDIA_SOURCE}"
        )

    theme, kind, number = SLOTS[slot]

    print("=" * 45)
    print("RK GAUTAM SMART AI AGENT")
    print("=" * 45)

    print("Slot:", slot)
    print("Theme:", theme)
    print("Content:", kind)
    print("Media source:", MEDIA_SOURCE)
    print("Test mode:", test_mode)

    # ======================================
    # LOAD PERMANENT HISTORY
    # ======================================

    history, sha = load_history()

    print_summary(history)

    # ======================================
    # GENERATE UNIQUE QUOTE
    # ======================================

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

    print("Quote generated:", quote["id"])

    # ======================================
    # GENERATE PHOTO
    # ======================================

    if kind == "photo":

        print("Generating photo...")

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

        print("PHOTO GENERATION SUCCESS")

    # ======================================
    # GENERATE ANIMATED REEL
    # ======================================

    else:

        print("Generating reel...")

        media = download_media(
            theme,
            "video",
            WORK / "background.mp4",
            get_used_ids(history, "videos")
        )

        # Generate Hindi voiceover

        voice = WORK / "voice.mp3"

        await create_voice(
            " ".join(lines),
            voice
        )

        if (
            not voice.is_file()
            or voice.stat().st_size == 0
        ):

            raise RuntimeError(
                "Voice generation failed"
            )

        print("HINDI VOICE SUCCESS")

        # Calculate reel duration

        duration = max(
            20.0,
            get_duration(voice) + 2.5
        )

        print("Reel duration:", duration)

        # Generate original music

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

        print("BACKGROUND MUSIC SUCCESS")

        # Create final reel

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

        print("REEL GENERATION SUCCESS")

    # ======================================
    # GENERATE CAPTION
    # ======================================

    caption = quote["caption"].replace(
        quote["title"],
        title,
        1
    )

    caption += generate_media_credit(media)

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

    print("CAPTION GENERATION SUCCESS")

    # ======================================
    # VALIDATE GENERATED FILES
    # ======================================

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

        print(
            "Verified:",
            path,
            "Size:",
            path.stat().st_size,
            "bytes"
        )

    print("ALL GENERATED FILES VERIFIED")

    # ======================================
    # SAVE CONTENT HISTORY
    # ======================================

    if test_mode:

        print("TEST MODE: History unchanged")
        print("No Facebook posting")

    else:

        save_history(history, sha)

        print("CONTENT HISTORY SAVED")

    print_summary(history)

    # ======================================
    # FINAL REPORT
    # ======================================

    print("=" * 45)
    print("CONTENT GENERATED SUCCESSFULLY")
    print("=" * 45)

    print("Slot:", slot)
    print("Theme:", theme)
    print("Content type:", kind)
    print("Media source:", MEDIA_SOURCE)
    print("Provider:", media.get("provider"))
    print("File:", destination)
    print("Caption:", caption_file)
    print("Test mode:", test_mode)

    if MEDIA_SOURCE == "local":

        print("Pixabay API not used")

    print("=" * 45)


if __name__ == "__main__":

    asyncio.run(main())
