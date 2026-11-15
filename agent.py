
import asyncio
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT = Path("output")
OUT.mkdir(exist_ok=True)

ASSETS = Path("assets")
FONT = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

IDEAS = [
    ("GOOD MORNING", "morning", "peaceful", [
        "नई सुबह नया उजाला लाई है,",
        "पहाड़ों ने फिर मुस्कान सजाई है,",
        "हर कदम पर उम्मीद साथ रहे,",
        "आज की सुबह खुशियाँ लाई है।"
    ]),
    ("MOTIVATION", "motivation", "motivational", [
        "रास्ते कठिन हों तो चलते रहो,",
        "अपने सपनों के लिए बढ़ते रहो,",
        "मंजिल भी एक दिन पास आएगी,",
        "बस खुद पर भरोसा करते रहो।"
    ]),
    ("EMOTIONAL", "emotional", "emotional", [
        "कुछ यादें दिल में रह जाती हैं,",
        "कुछ बातें आँखें कह जाती हैं,",
        "वक्त चाहे कितना भी बदल जाए,",
        "अपनों की याद साथ निभाती है।"
    ]),
    ("TRAVEL", "travel", "travel", [
        "चलो फिर नए रास्ते अपनाएँ,",
        "पहाड़ों से कुछ बातें कर आएँ,",
        "सफर में जो पल मिल जाएँ,",
        "उन्हें यादों में सदा सजाएँ।"
    ])
]


def run(command):
    subprocess.run(command, check=True)


def make_poster(background, destination, size, title, lines):
    with Image.open(background) as source:
        img = ImageOps.fit(
            source.convert("RGB"),
            size,
            method=Image.Resampling.LANCZOS
        )

    img = img.convert("RGBA")
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = size

    draw.rounded_rectangle(
        (int(w * .045), int(h * .28),
         int(w * .955), int(h * .75)),
        radius=32,
        fill=(0, 0, 0, 165)
    )

    title_font = ImageFont.truetype(FONT_BOLD, int(w * .046))
    hindi_font = ImageFont.truetype(FONT, int(w * .046))
    brand_font = ImageFont.truetype(FONT_BOLD, int(w * .032))

    draw.text(
        (w // 2, int(h * .33)),
        title,
        font=title_font,
        anchor="mm",
        fill="#FFDB85"
    )

    for idx, line in enumerate(lines):
        draw.text(
            (w // 2, int(h * (.43 + idx * .072))),
            line,
            font=hindi_font,
            anchor="mm",
            fill="white",
            stroke_width=1,
            stroke_fill="#151515"
        )

    draw.text(
        (w // 2, int(h * .85)),
        "RK GAUTAM | FOLLOW FOR MORE",
        font=brand_font,
        anchor="mm",
        fill="white",
        stroke_width=2,
        stroke_fill="black"
    )

    Image.alpha_composite(img, overlay).convert("RGB").save(
        destination, quality=91
    )


async def create_voice(text, path):
    voice = edge_tts.Communicate(
        text,
        "hi-IN-MadhurNeural",
        rate="-8%"
    )
    await voice.save(str(path))


def get_duration(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ], text=True)

    return float(result.strip())


async def main():
    for i, (title, bg_name, music_name, lines) in enumerate(
        IDEAS, start=1
    ):
        background = ASSETS / "backgrounds" / f"{bg_name}.jpg"
        music = ASSETS / "music" / f"{music_name}.mp3"

        if not background.is_file():
            raise FileNotFoundError(f"Missing: {background}")

        if not music.is_file():
            raise FileNotFoundError(f"Missing: {music}")

        photo = OUT / f"post_{i}.png"
        cover = OUT / f"reel_{i}_cover.png"
        voice_file = OUT / f"voice_{i}.mp3"
        video = OUT / f"reel_{i}.mp4"

        make_poster(
            background, photo,
            (1080, 1080), title, lines
        )

        make_poster(
            background, cover,
            (1080, 1920), title, lines
        )

        await create_voice(" ".join(lines), voice_file)

        length = max(20.0, get_duration(voice_file) + 2.5)
        fade_start = length - 1

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", "25",
            "-i", str(cover),
            "-i", str(voice_file),
            "-stream_loop", "-1",
            "-i", str(music),
            "-filter_complex",
            "[1:a]volume=1.0[voice];"
            "[2:a]volume=0.10[music];"
            "[voice][music]"
            "amix=inputs=2:duration=longest:"
            "dropout_transition=0[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-t", f"{length:.2f}",
            "-vf",
            f"fade=t=in:st=0:d=0.7,"
            f"fade=t=out:st={fade_start:.2f}:d=1,"
            "format=yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "160k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-shortest",
            str(video)
        ])

        caption = (
            f"{title}\n\n"
            + "\n".join(lines)
            + "\n\n#RKGautam #HindiReels #DigitalCreator\n"
        )

        (OUT / f"caption_{i}.txt").write_text(
            caption, encoding="utf-8"
        )

        print(f"Created {photo} and {video}")

    print("SUCCESS: 4 Photos + 4 Voice Reels!")


if __name__ == "__main__":
    asyncio.run(main())
