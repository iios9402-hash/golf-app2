import requests
import base64
import os

REPO = "iios9402-hash/golf-app2"
FILE_PATH = "settings.json"
BRANCH = "main"

GITHUB_TOKEN = os.getenv("GH_TOKEN")

def get_file():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]

def update_file(new_content, sha):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": "Auto update settings.json (test)",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    r = requests.put(url, json=payload, headers=headers)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    print("Reading current settings.json...")
    content, sha = get_file()
    print(content)

    print("Updating settings.json...")

    new_content = """{
  "reserved_date": "2026-03-01",
  "emails": [
    "iios9402@yahoo.co.jp"
  ]
}"""

    update_file(new_content, sha)

    print("Update complete.")
