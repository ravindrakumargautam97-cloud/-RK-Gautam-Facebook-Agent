import os
import requests

page_id = os.getenv("FACEBOOK_PAGE_ID")
token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

if not page_id or not token:
    raise RuntimeError("Facebook credentials missing")

url = f"https://graph.facebook.com/v27.0/{page_id}"

response = requests.get(
    url,
    params={
        "fields": "id,name",
        "access_token": token,
    },
    timeout=30,
)

data = response.json()

if not response.ok or "error" in data:
    print("Facebook connection FAILED")
    print("Error:", data.get("error", {}).get("message"))
    raise SystemExit(1)

print("Facebook connection SUCCESS")
print("Page ID:", data.get("id"))
print("Page Name:", data.get("name"))
