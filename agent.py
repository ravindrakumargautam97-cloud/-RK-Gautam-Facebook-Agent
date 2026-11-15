
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

now = datetime.now(ZoneInfo("Asia/Kolkata"))
today = now.strftime("%Y-%m-%d")

content = [
    {
        "time": "08:00",
        "topic": "Good Morning",
        "caption": "नई सुबह, नए सपने और नई उम्मीद। 🌅",
        "hook": "हर सुबह एक नया मौका लेकर आती है!"
    },
    {
        "time": "12:00",
        "topic": "Motivation",
        "caption": "मेहनत कभी बेकार नहीं जाती। 💪",
        "hook": "सफल होना है तो ये बात याद रखना!"
    },
    {
        "time": "17:00",
        "topic": "Daily Life",
        "caption": "जिंदगी की छोटी खुशियाँ ही असली दौलत हैं। ❤️",
        "hook": "जिंदगी की एक सच्ची बात सुनिए!"
    },
    {
        "time": "20:00",
        "topic": "Comedy",
        "caption": "Salary आते ही EMI का मैसेज आ गया! 😂",
        "hook": "जब Salary और EMI एक ही दिन मिलें!"
    }
]

folder = Path("output")
folder.mkdir(exist_ok=True)

for i, item in enumerate(content, start=1):
    post = f"""RK Gautam | {today}
Time: {item['time']} IST

{item['caption']}

Follow RK Gautam ❤️
#RKGautam #HindiContent
"""

    reel = f"""RK Gautam Reel {i}
Topic: {item['topic']}
Time: {item['time']} IST

HOOK: {item['hook']}

STORY: {item['caption']}

ENDING: Follow for more!

Format: 9:16
Duration: 15-20 seconds
"""

    (folder / f"post_{i}.txt").write_text(
        post, encoding="utf-8"
    )

    (folder / f"reel_{i}.txt").write_text(
        reel, encoding="utf-8"
    )

print("4 Posts and 4 Reel scripts generated!")
