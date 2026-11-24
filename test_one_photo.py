from pathlib import Path
from facebook_post import post_photo

photo = Path("output/post_1.png")
caption_file = Path("output/caption_1.txt")

if not photo.is_file():
    raise FileNotFoundError(photo)

if not caption_file.is_file():
    raise FileNotFoundError(caption_file)

caption = caption_file.read_text(
    encoding="utf-8"
).strip()

if not caption:
    raise RuntimeError("Caption is empty")

print("Starting single photo test")

result = post_photo(photo, caption)

print("Photo test result:", result)
