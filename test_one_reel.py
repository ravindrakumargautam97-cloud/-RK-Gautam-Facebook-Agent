
import os
import sys
from pathlib import Path

from facebook_post import post_reel

def main():
    # Only one reel is allowed
    reel = Path("output/reel_1.mp4")
    caption_file = Path("output/caption_1.txt")

    if not reel.is_file():
        sys.exit("ERROR: reel_1.mp4 not found")

    if not caption_file.is_file():
        sys.exit("ERROR: caption_1.txt not found")

    if not os.getenv("FACEBOOK_PAGE_ID"):
        sys.exit("ERROR: Facebook Page ID missing")

    if not os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"):
        sys.exit("ERROR: Facebook Page token missing")

    caption = caption_file.read_text(
        encoding="utf-8"
    ).strip()

    if not caption:
        sys.exit("ERROR: Empty caption")

    print("Starting ONE Facebook Reel test")
    print("File:", reel)
    print("No photos or other reels will be posted")

    post_reel(reel, caption)

    print("Single Reel API request completed")


if __name__ == "__main__":
    main()
