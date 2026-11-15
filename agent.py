
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

now = datetime.now(ZoneInfo("Asia/Kolkata"))
today = now.strftime("%Y-%m-%d")

topics = [
    ("Motivation", "हार मत मानो, मेहनत का फल जरूर मिलेगा।"),
    ("Comedy", "जब Salary आती है और EMI पहले ही इंतजार कर रही होती है! 😂"),
    ("Daily Life", "छोटी-छोटी खुशियों से ही जिंदगी खूबसूरत बनती है।"),
    ("Success", "आज की मेहनत कल की पहचान बनेगी।"),
    ("Good Morning", "नई सुबह, नई उम्मीद और नई शुरुआत। 🌅"),
    ("Life", "मुश्किल वक्त हमें मजबूत बनाता है।"),
    ("Inspiration", "अपने सपनों को कभी छोटा मत समझो।")
]

index = now.toordinal() % len(topics)
topic, caption = topics[index]

post = f"""RK Gautam | {today}

{caption}

❤️ पसंद आए तो Follow करें।

#RKGautam #HindiReels #DigitalCreator
#{topic.replace(" ", "")}
"""

reel_script = f"""Today's Reel: {topic}

HOOK: क्या आपके साथ भी ऐसा होता है?

MESSAGE: {caption}

ENDING: ऐसी और Videos के लिए Follow करें।

Format: Vertical 9:16
Target duration: 15-20 seconds
"""

folder = Path("output")
folder.mkdir(exist_ok=True)

(folder / "facebook_post.txt").write_text(
    post, encoding="utf-8"
)

(folder / "reel_script.txt").write_text(
    reel_script, encoding="utf-8"
)

print("Daily content generated successfully!")
print(post)
