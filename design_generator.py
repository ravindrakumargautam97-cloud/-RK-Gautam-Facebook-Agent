
import random
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageOps


FONT = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

IST = ZoneInfo("Asia/Kolkata")

COLORS = {
    "morning": ["#FFD700", "#FFE4B5", "#FFFACD"],
    "afternoon": ["#90EE90", "#87CEEB", "#FFFFFF"],
    "evening": ["#FFA500", "#FFB6C1", "#FFDAB9"],
    "night": ["#ADD8E6", "#E6E6FA", "#F0F8FF"],
}


def run(command):

    subprocess.run(command, check=True)


def get_duration(path):

    result = subprocess.check_output([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path)
    ], text=True)

    return float(result.strip())


def get_style(theme):

    today = datetime.now(IST).date().isoformat()

    seed = hashlib.sha256(
        f"{today}-{theme}".encode()
    ).hexdigest()

    rng = random.Random(seed)

    return {
        "color": rng.choice(COLORS[theme]),
        "opacity": rng.randint(125, 185),
        "radius": rng.choice([20, 35, 50]),
        "position": rng.choice([0.30, 0.34, 0.38]),
    }


def fit_font(draw, text, font_path, size, max_width):

    while size > 12:

        font = ImageFont.truetype(
            font_path, size
        )

        if draw.textlength(
            text, font=font
        ) <= max_width:
            return font

        size -= 2

    return ImageFont.truetype(font_path, 12)


def create_overlay(
    destination,
    size,
    theme,
    title,
    lines
):

    w, h = size

    style = get_style(theme)

    overlay = Image.new(
        "RGBA", size, (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(overlay)

    top = int(h * style["position"])

    draw.rounded_rectangle(
        (
            int(w * 0.05),
            top - int(h * 0.05),
            int(w * 0.95),
            top + int(h * 0.37)
        ),
        radius=style["radius"],
        fill=(0, 0, 0, style["opacity"])
    )

    title_font = fit_font(
        draw, title, FONT_BOLD,
        int(w * 0.065), int(w * 0.82)
    )

    draw.text(
        (w // 2, top),
        title,
        font=title_font,
        anchor="mm",
        fill=style["color"]
    )

    for i, line in enumerate(lines):

        font = fit_font(
            draw, line, FONT,
            int(w * 0.045), int(w * 0.82)
        )

        draw.text(
            (
                w // 2,
                top + int(h * (0.09 + i * 0.07))
            ),
            line,
            font=font,
            anchor="mm",
            fill="white",
            stroke_width=1,
            stroke_fill="black"
        )

    brand_font = ImageFont.truetype(
        FONT_BOLD, int(w * 0.032)
    )

    draw.text(
        (w // 2, int(h * 0.83)),
        "RK DIGITAL WORLD",
        font=brand_font,
        anchor="mm",
        fill="white",
        stroke_width=2,
        stroke_fill="black"
    )

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True, exist_ok=True
    )

    overlay.save(destination)

    return destination


def create_photo(
    background,
    destination,
    theme,
    title,
    lines
):

    size = (1080, 1080)

    destination = Path(destination)

    overlay_path = destination.with_name(
        destination.stem + "_overlay.png"
    )

    create_overlay(
        overlay_path,
        size,
        theme,
        title,
        lines
    )

    with Image.open(background) as source:

        image = ImageOps.fit(
            source.convert("RGB"),
            size,
            method=Image.Resampling.LANCZOS
        ).convert("RGBA")

    with Image.open(overlay_path) as overlay:

        final = Image.alpha_composite(
            image,
            overlay.convert("RGBA")
        )

        final.convert("RGB").save(destination)

    overlay_path.unlink(missing_ok=True)

    print("PHOTO CREATED:", destination)

    return destination


def create_reel(
    background_video,
    voice_file,
    music_file,
    destination,
    theme,
    title,
    lines
):

    destination = Path(destination)

    overlay = destination.with_name(
        destination.stem + "_overlay.png"
    )

    create_overlay(
        overlay,
        (1080, 1920),
        theme,
        title,
        lines
    )

    duration = max(
        20.0,
        get_duration(voice_file) + 2.5
    )

    fade_start = duration - 1

    filters = (
        "[0:v]scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1,fps=25[bg];"

        "[bg][1:v]overlay=0:0,"
        "fade=t=in:st=0:d=0.7,"
        f"fade=t=out:st={fade_start:.2f}:d=1,"
        "format=yuv420p[v];"

        "[2:a]volume=1.0[voice];"
        "[3:a]volume=0.12[music];"

        "[voice][music]"
        "amix=inputs=2:duration=longest:"
        "dropout_transition=0:normalize=0[a]"
    )

    run([
        "ffmpeg",
        "-y",

        "-stream_loop", "-1",
        "-i", str(background_video),

        "-loop", "1",
        "-framerate", "25",
        "-i", str(overlay),

        "-i", str(voice_file),

        "-stream_loop", "-1",
        "-i", str(music_file),

        "-filter_complex", filters,

        "-map", "[v]",
        "-map", "[a]",

        "-t", f"{duration:.2f}",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "24",

        "-c:a", "aac",
        "-b:a", "160k",

        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",

        str(destination)
    ])

    overlay.unlink(missing_ok=True)

    print("MOVING REEL CREATED:", destination)

    return destination
