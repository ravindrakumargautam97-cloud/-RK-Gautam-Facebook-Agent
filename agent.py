
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageOps


# ==========================================
# RK GAUTAM DAILY AI AGENT
# ==========================================

OUT = Path("output")
OUT.mkdir(parents=True, exist_ok=True)

ASSETS = Path("assets")

FONT = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ==========================================
# CONTENT CATEGORIES
# ==========================================

IDEAS = [
    (
        "GOOD MORNING",
        "morning",
        "peaceful",
        [
            "नई सुबह नया उजाला लाई है,",
            "पहाड़ों ने फिर मुस्कान सजाई है,",
            "हर कदम पर उम्मीद साथ रहे,",
            "आज की सुबह खुशियाँ लाई है।"
        ]
    ),
    (
        "MOTIVATION",
        "motivation",
        "motivational",
        [
            "रास्ते कठिन हों तो चलते रहो,",
            "अपने सपनों के लिए बढ़ते रहो,",
            "मंजिल भी एक दिन पास आएगी,",
            "बस खुद पर भरोसा करते रहो।"
        ]
    ),
    (
        "EMOTIONAL",
        "emotional",
        "emotional",
        [
            "कुछ यादें दिल में रह जाती हैं,",
            "कुछ बातें आँखें कह जाती हैं,",
            "वक्त चाहे कितना भी बदल जाए,",
            "अपनों की याद साथ निभाती है।"
        ]
    ),
    (
        "TRAVEL",
        "travel",
        "travel",
        [
            "चलो फिर नए रास्ते अपनाएँ,",
            "पहाड़ों से कुछ बातें कर आएँ,",
            "सफर में जो पल मिल जाएँ,",
            "उन्हें यादों में सदा सजाएँ।"
        ]
    )
]


# ==========================================
# DAILY HINDI QUOTE BANK
# ==========================================

QUOTE_BANK = {
    "GOOD MORNING": [
        [
            "नई सुबह नया संदेश लाई है,",
            "उम्मीदों की किरण मुस्कुराई है,",
            "हर दिन कुछ अच्छा करते चलो,",
            "जिंदगी फिर खुशियाँ लाई है।"
        ],
        [
            "सूरज की किरणें आई हैं,",
            "नई उम्मीदें साथ लाई हैं,",
            "मुस्कुराकर दिन की शुरुआत करो,",
            "खुशियों ने बाहें फैलाई हैं।"
        ],
        [
            "आज का दिन नया अवसर है,",
            "हर कोशिश में एक नया सफर है,",
            "मेहनत से सपने सच होंगे,",
            "विश्वास ही सबसे बड़ी ताकत है।"
        ],
        [
            "हर सुबह नई उम्मीद जगाती है,",
            "हर किरण नया रास्ता दिखाती है,",
            "दिल में विश्वास बनाए रखो,",
            "जिंदगी खुशियाँ लेकर आती है।"
        ],
        [
            "सुबह की हवा कुछ कहती है,",
            "नई ऊर्जा मन में भरती है,",
            "आज फिर कुछ अच्छा करना है,",
            "यही सोच आगे बढ़ाती है।"
        ]
    ],

    "MOTIVATION": [
        [
            "मुश्किल रास्तों से मत डरना,",
            "हर चुनौती का सामना करना,",
            "जो मेहनत से आगे बढ़ता है,",
            "उसे मंजिल जरूर मिलती है।"
        ],
        [
            "हार से कभी घबराना नहीं,",
            "सपनों को कभी भुलाना नहीं,",
            "आज की मेहनत रंग लाएगी,",
            "बस कोशिश करना छोड़ना नहीं।"
        ],
        [
            "अपने लक्ष्य पर नजर रखना,",
            "हर दिन खुद को बेहतर करना,",
            "सफलता मेहनत से मिलती है,",
            "बस आगे बढ़ते रहना।"
        ],
        [
            "सपनों को सच करना है,",
            "तो मेहनत से रिश्ता रखना है,",
            "आज मुश्किल जरूर होगी,",
            "कल सफलता का दिन होगा।"
        ],
        [
            "जो गिरकर फिर उठ जाता है,",
            "वही इतिहास बनाता है,",
            "हिम्मत कभी मत हारना,",
            "वक्त सबको मौका देता है।"
        ]
    ],

    "EMOTIONAL": [
        [
            "कुछ रिश्ते दिल में बस जाते हैं,",
            "कुछ लोग यादों में रह जाते हैं,",
            "दूर होकर भी अपने लगते हैं,",
            "और हर पल याद आते हैं।"
        ],
        [
            "वक्त बदलता रहता है,",
            "दिल सब कुछ सहता रहता है,",
            "कुछ यादें कभी नहीं मिटतीं,",
            "इंसान उन्हें संजोए रखता है।"
        ],
        [
            "हर मुस्कान के पीछे कहानी है,",
            "हर आँख में कुछ निशानी है,",
            "जिंदगी का यही सफर है,",
            "कुछ खुशी और कुछ परेशानी है।"
        ],
        [
            "कुछ लोग दूर चले जाते हैं,",
            "लेकिन दिल में रह जाते हैं,",
            "यादें कभी खत्म नहीं होतीं,",
            "बस आँखें नम कर जाती हैं।"
        ],
        [
            "जिंदगी हर दिन कुछ सिखाती है,",
            "कभी हँसाती कभी रुलाती है,",
            "जो अपने दिल के करीब होते हैं,",
            "उनकी याद हमेशा आती है।"
        ]
    ],

    "TRAVEL": [
        [
            "नए रास्तों पर चलते जाओ,",
            "दुनिया की खूबसूरती देखते जाओ,",
            "हर सफर कुछ सिखाता है,",
            "नई यादें बनाते जाओ।"
        ],
        [
            "पहाड़ों की हवा कुछ कहती है,",
            "नदियों की धारा बहती है,",
            "सफर में सुकून मिलता है,",
            "प्रकृति दिल के करीब रहती है।"
        ],
        [
            "मंजिल से सुंदर रास्ते हैं,",
            "हर मोड़ पर नए वास्ते हैं,",
            "चलते रहो खुले आसमान में,",
            "सफर ही जिंदगी के किस्से हैं।"
        ],
        [
            "चलो कहीं दूर निकल जाएँ,",
            "नई दुनिया से मिलकर आएँ,",
            "पहाड़ों और वादियों में,",
            "कुछ खूबसूरत पल बिताएँ।"
        ],
        [
            "खुले आसमान के नीचे चलना,",
            "हर रास्ते से कुछ सीखना,",
            "दुनिया बहुत खूबसूरत है,",
            "बस उसे दिल से देखना।"
        ]
    ]
}


# ==========================================
# SELECT DAILY QUOTES
# ==========================================

def get_daily_quotes(title, original_lines):
    choices = QUOTE_BANK.get(title)

    if not choices:
        return original_lines

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date()

    index = today.toordinal() % len(choices)

    return choices[index]


# ==========================================
# COMMAND RUNNER
# ==========================================

def run(command):
    subprocess.run(command, check=True)


# ==========================================
# CREATE POSTER
# ==========================================

def make_poster(background, destination, size, title, lines):

    with Image.open(background) as source:
        img = ImageOps.fit(
            source.convert("RGB"),
            size,
            method=Image.Resampling.LANCZOS
        )

    img = img.convert("RGBA")

    overlay = Image.new(
        "RGBA",
        size,
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(overlay)

    w, h = size

    draw.rounded_rectangle(
        (
            int(w * 0.045),
            int(h * 0.28),
            int(w * 0.955),
            int(h * 0.75)
        ),
        radius=32,
        fill=(0, 0, 0, 165)
    )

    title_font = ImageFont.truetype(
        FONT_BOLD,
        int(w * 0.046)
    )

    hindi_font = ImageFont.truetype(
        FONT,
        int(w * 0.046)
    )

    brand_font = ImageFont.truetype(
        FONT_BOLD,
        int(w * 0.032)
    )

    draw.text(
        (w // 2, int(h * 0.33)),
        title,
        font=title_font,
        anchor="mm",
        fill="#FFDB85"
    )

    for idx, line in enumerate(lines):
        draw.text(
            (
                w // 2,
                int(h * (0.43 + idx * 0.072))
            ),
            line,
            font=hindi_font,
            anchor="mm",
            fill="white",
            stroke_width=1,
            stroke_fill="#151515"
        )

    draw.text(
        (w // 2, int(h * 0.85)),
        "RK GAUTAM | FOLLOW FOR MORE",
        font=brand_font,
        anchor="mm",
        fill="white",
        stroke_width=2,
        stroke_fill="black"
    )

    final_img = Image.alpha_composite(
        img,
        overlay
    ).convert("RGB")

    final_img.save(
        destination,
        format="PNG"
    )


# ==========================================
# CREATE HINDI AI VOICE WITH RETRY
# ==========================================

async def create_voice(text, path):

    voices = [
        "hi-IN-MadhurNeural",
        "hi-IN-SwaraNeural"
    ]

    for attempt in range(1, 5):

        voice_name = voices[
            (attempt - 1) % len(voices)
        ]

        try:
            print(
                f"Voice attempt {attempt}/4: {voice_name}",
                flush=True
            )

            if path.exists():
                path.unlink()

            voice = edge_tts.Communicate(
                text,
                voice_name,
                rate="-8%"
            )

            await voice.save(str(path))

            if (
                path.exists()
                and path.stat().st_size > 0
            ):
                print(
                    "Hindi voice created successfully!",
                    flush=True
                )
                return

            raise RuntimeError(
                "Generated audio file is empty"
            )

        except Exception as error:

            print(
                f"Voice attempt {attempt} failed: {error}",
                flush=True
            )

            if attempt == 4:
                raise RuntimeError(
                    "Hindi voice failed after 4 attempts"
                ) from error

            await asyncio.sleep(attempt * 5)


# ==========================================
# GET AUDIO DURATION
# ==========================================

def get_duration(path):

    result = subprocess.check_output(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path)
        ],
        text=True
    )

    return float(result.strip())


# ==========================================
# MAIN AGENT
# ==========================================

async def main():

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%d-%m-%Y")

    print(
        f"RK GAUTAM DAILY AI AGENT: {today}",
        flush=True
    )

    for i, (title, bg_name, music_name, lines) in enumerate(
        IDEAS,
        start=1
    ):

        # Select today's quotes
        lines = get_daily_quotes(title, lines)

        background = (
            ASSETS / "backgrounds" / f"{bg_name}.jpg"
        )

        music = (
            ASSETS / "music" / f"{music_name}.mp3"
        )

        if not background.is_file():
            raise FileNotFoundError(
                f"Missing background: {background}"
            )

        if not music.is_file():
            raise FileNotFoundError(
                f"Missing music: {music}"
            )

        photo = OUT / f"post_{i}.png"
        cover = OUT / f"reel_{i}_cover.png"
        voice_file = OUT / f"voice_{i}.mp3"
        video = OUT / f"reel_{i}.mp4"

        print(
            f"Creating content {i}: {title}",
            flush=True
        )

        # Create Facebook Photo
        make_poster(
            background,
            photo,
            (1080, 1080),
            title,
            lines
        )

        # Create Vertical Reel Cover
        make_poster(
            background,
            cover,
            (1080, 1920),
            title,
            lines
        )

        # Generate Hindi AI Voice
        await create_voice(
            " ".join(lines),
            voice_file
        )

        length = max(
            20.0,
            get_duration(voice_file) + 2.5
        )

        fade_start = length - 1

        # Generate MP4 Reel
        run([
            "ffmpeg",
            "-y",

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

            str(video)
        ])

        # Generate Facebook Caption
        caption = (
            f"{title}\n\n"
            + "\n".join(lines)
            + "\n\n"
            + "#RKGautam #HindiReels "
            + "#DigitalCreator #Motivation "
            + "#FacebookReels\n"
        )

        caption_file = OUT / f"caption_{i}.txt"

        caption_file.write_text(
            caption,
            encoding="utf-8"
        )

        print(
            f"SUCCESS: Created {photo} and {video}",
            flush=True
        )

    print(
        "SUCCESS: 4 Photos + 4 Hindi Voice Reels!",
        flush=True
    )


if __name__ == "__main__":
    asyncio.run(main())
