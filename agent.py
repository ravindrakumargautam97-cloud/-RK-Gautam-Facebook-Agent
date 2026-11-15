
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import textwrap
import random

OUT = Path("output")
OUT.mkdir(exist_ok=True)

now = datetime.now(ZoneInfo("Asia/Kolkata"))
today = now.strftime("%Y-%m-%d")

ideas = [
    ("GOOD MORNING", "Every sunrise brings new hope",
     "नई सुबह नई उम्मीद लेकर आती है। 🌅",
     (22, 76, 116)),
    ("MOTIVATION", "Never give up on your dreams",
     "मेहनत जारी रखो, सफलता जरूर मिलेगी। 💪",
     (80, 35, 105)),
    ("DAILY LIFE", "Small moments make life beautiful",
     "जिंदगी की छोटी खुशियाँ सबसे खास होती हैं। ❤️",
     (20, 100, 87)),
    ("COMEDY", "Salary came, EMI said hello!",
     "सैलरी आई और EMI ने स्वागत कर लिया! 😂",
     (130, 63, 43))
]

font_path = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)

def create_image(path, size, title, quote, bg):
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    w, h = size

    title_font = ImageFont.truetype(
        font_path, int(w * 0.045)
    )
    quote_font = ImageFont.truetype(
        font_path, int(w * 0.057)
    )
    brand_font = ImageFont.truetype(
        font_path, int(w * 0.035)
    )

    draw.rounded_rectangle(
        (35, 35, w-35, h-35),
        radius=35,
        outline=(255, 210, 110),
        width=5
    )

    draw.text(
        (w//2, int(h*0.25)), title,
        font=title_font, anchor="mm",
        fill=(255, 210, 110)
    )

    lines = textwrap.wrap(quote, width=23)
    line_height = int(w * 0.085)
    start_y = h//2 - len(lines)*line_height//2

    for j, line in enumerate(lines):
        draw.text(
            (w//2, start_y + j*line_height),
            line, font=quote_font,
            anchor="mm", fill="white"
        )

    draw.text(
        (w//2, int(h*0.82)),
        "RK GAUTAM | FOLLOW FOR MORE",
        font=brand_font, anchor="mm",
        fill=(255, 210, 110)
    )
    img.save(path)

random.seed(today)

for i, (topic, quote, caption, color) in enumerate(
    ideas, start=1
):
    suffix = random.choice([
        "Keep smiling",
        "Make today count",
        "Stay positive",
        "Enjoy every moment"
    ])

    full_quote = quote + " - " + suffix

    photo = OUT / f"post_{i}.png"
    poster = OUT / f"reel_{i}_cover.png"
    video = OUT / f"reel_{i}.mp4"

    create_image(
        photo, (1080, 1080),
        topic, full_quote, color
    )
    create_image(
        poster, (1080, 1920),
        topic, full_quote, color
    )

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", "25",
        "-i", str(poster),
        "-t", "12",
        "-vf",
        "fade=t=in:st=0:d=1,"
        "fade=t=out:st=11:d=1,"
        "format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(video)
    ], check=True, stdout=subprocess.DEVNULL)

    (OUT / f"caption_{i}.txt").write_text(
        f"{topic}\n\n{caption}\n\n"
        "#RKGautam #HindiReels "
        "#DigitalCreator\n",
        encoding="utf-8"
    )

print("SUCCESS: 4 Photos + 4 MP4 Reels created!")
