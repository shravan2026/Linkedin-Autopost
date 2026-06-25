import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

TOKEN = os.environ["LINKEDIN_ACCESS_TOKEN"].strip()
PERSON_ID = os.environ["LINKEDIN_PERSON_ID"].strip()
CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("LINKEDIN_REFRESH_TOKEN", "").strip()
GH_TOKEN = os.environ.get("GH_PAT", "").strip()
GH_REPO = "shravan2026/Linkedin-Autopost"

LINKEDIN_VERSION = "202606"


def refresh_access_token():
    if not REFRESH_TOKEN or not CLIENT_ID or not CLIENT_SECRET:
        print("Refresh token or client credentials not configured.")
        return None

    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken", data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        new_token = result["access_token"]
        new_refresh = result.get("refresh_token", REFRESH_TOKEN)
        print(f"Token refreshed! Expires in {result['expires_in']} seconds.")
        update_github_secret("LINKEDIN_ACCESS_TOKEN", new_token)
        if new_refresh != REFRESH_TOKEN:
            update_github_secret("LINKEDIN_REFRESH_TOKEN", new_refresh)
        return new_token
    except urllib.error.HTTPError as e:
        print(f"Token refresh failed: {e.code} - {e.read().decode()}")
        return None


def update_github_secret(secret_name, secret_value):
    if not GH_TOKEN:
        print(f"No GH_PAT configured. Cannot update {secret_name}.")
        return
    try:
        import nacl.public
        import base64

        req = urllib.request.Request(f"https://api.github.com/repos/{GH_REPO}/actions/secrets/public-key")
        req.add_header("Authorization", f"Bearer {GH_TOKEN}")
        req.add_header("Accept", "application/vnd.github+json")
        resp = urllib.request.urlopen(req)
        key_data = json.loads(resp.read())

        public_key_bytes = base64.b64decode(key_data["key"])
        sealed_box = nacl.public.SealedBox(nacl.public.PublicKey(public_key_bytes))
        encrypted = base64.b64encode(sealed_box.encrypt(secret_value.encode())).decode()

        payload = json.dumps({"encrypted_value": encrypted, "key_id": key_data["key_id"]}).encode()
        req = urllib.request.Request(
            f"https://api.github.com/repos/{GH_REPO}/actions/secrets/{secret_name}",
            data=payload, method="PUT"
        )
        req.add_header("Authorization", f"Bearer {GH_TOKEN}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req)
        print(f"GitHub secret {secret_name} updated.")
    except Exception as e:
        print(f"Warning: Could not update {secret_name}: {e}")


def get_today_post():
    tracker_file = "last_posted_day.txt"
    posts = sorted(
        [f for f in os.listdir("posts") if f.startswith("day") and f.endswith(".md")],
        key=lambda x: int(x.replace("day", "").replace(".md", ""))
    )
    if not posts:
        return None

    last_day = 0
    if os.path.exists(tracker_file):
        with open(tracker_file, "r") as f:
            try:
                last_day = int(f.read().strip())
            except ValueError:
                last_day = 0

    next_day = last_day + 1
    found = None
    for p in posts:
        day_num = int(p.replace("day", "").replace(".md", ""))
        if day_num == next_day:
            found = p
            break

    if not found:
        next_day = int(posts[0].replace("day", "").replace(".md", ""))
        found = posts[0]

    with open(tracker_file, "w") as f:
        f.write(str(next_day))

    with open(f"posts/{found}", "r", encoding="utf-8") as f:
        content = f.read().strip()

    print(f"Selected: {found} (Day {next_day})")
    return content


def post_to_linkedin(text, token):
    payload = {
        "author": f"urn:li:person:{PERSON_ID}",
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request("https://api.linkedin.com/rest/posts", data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Restli-Protocol-Version", "2.0.0")
    req.add_header("LinkedIn-Version", LINKEDIN_VERSION)

    try:
        response = urllib.request.urlopen(req)
        post_id = response.headers.get("x-restli-id", "unknown")
        print(f"Posted successfully! Post ID: {post_id}")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 401:
            print("Token expired. Attempting refresh...")
            return None
        elif e.code == 422 and "DUPLICATE" in body.upper():
            print("Duplicate post. Skipping.")
            return True
        else:
            print(f"Error {e.code}: {body}")
            raise


if __name__ == "__main__":
    ist = timezone(timedelta(hours=5, minutes=30))
    print(f"LinkedIn Auto-Post - {datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')}")
    print(f"Profile: Shravan Kumar | Medical Writing")
    print(f"API Version: {LINKEDIN_VERSION}")
    print("-" * 50)

    content = get_today_post()
    if not content:
        print("No post content available.")
        exit(0)

    print(f"Post length: {len(content)} characters")
    print("-" * 50)

    result = post_to_linkedin(content, TOKEN)

    if result is None:
        new_token = refresh_access_token()
        if new_token:
            result = post_to_linkedin(content, new_token)
        else:
            print("FATAL: Could not refresh token.")
            exit(1)

    if not result:
        exit(1)
