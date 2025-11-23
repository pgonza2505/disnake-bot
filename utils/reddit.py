import random
from .http import _get_json

UA_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

UA_LINUX = (
    "Mozilla/5.0 (X11; Linux armv8l) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

BASE_URL = "https://old.reddit.com"

def _image_from_post(post: dict, allow_nsfw: bool) -> str | None:
    data = post.get("data", {}) or {}
    if data.get("over_18") and not allow_nsfw:
        return None

    url = data.get("url_overridden_by_dest") or data.get("url")
    if not url:
        return None
    low = url.lower()

    if any(low.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".gifv", ".webp")):
        if low.endswith(".gifv"):
            url = url[:-1]
        return url

    if "i.redd.it" in low or "preview.redd.it" in low or "i.imgur.com" in low:
        return url

    if data.get("is_gallery") or data.get("is_video"):
        return None
    return None

async def fetch_random_reddit_image(
    subreddit: str,
    *,
    sort: str = "hot",
    t: str = "day",
    limit: int = 50,
    allow_nsfw: bool = False,
):
    url = f"{BASE_URL}/r/{subreddit}/{sort}.json?limit={limit}&t={t}"

    # Try Windows UA first
    payload = await _get_json(
        url,
        headers={"User-Agent": UA_WINDOWS},
    )

    # If FAILS → try Linux/Pi UA
    if payload is None:
        print("[reddit] Windows UA failed, retrying with Linux UA...")
        payload = await _get_json(
            url,
            headers={"User-Agent": UA_LINUX},
        )

    # If STILL fails → give up
    if payload is None:
        print("[reddit] Both UAs failed. Giving up.")
        return None

    # Same parsing logic as before below
    posts = payload.get("data", {}).get("children", [])
    if not posts:
        return None

    candidates = []
    for post in posts:
        pdata = post.get("data", {})
        img = pdata.get("url_overridden_by_dest") or pdata.get("url")
        if not img:
            continue

        if not allow_nsfw and pdata.get("over_18"):
            continue

        if img.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            candidates.append(img)

    if not candidates:
        return None

    return random.choice(candidates)
