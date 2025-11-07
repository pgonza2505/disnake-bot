import random
from .http import _get_json

UA = "disnake-bot/1.0 (by u/your_username_or_bot_name)"
REDDIT_BASE = "https://www.reddit.com"

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

async def fetch_random_reddit_image(subreddit: str, *, sort: str = "hot", t: str = "day", allow_nsfw: bool = False):
    params = "?limit=50"
    if sort == "top":
        params += f"&t={t}"
    url = f"{REDDIT_BASE}/r/{subreddit}/{sort}.json{params}"
    payload = await _get_json(url, headers={"User-Agent": UA})
    if not payload:
        return None

    posts = (payload.get("data", {}) or {}).get("children", []) or []
    random.shuffle(posts)
    for p in posts:
        img = _image_from_post(p, allow_nsfw)
        if img:
            d = p["data"]
            meta = {
                "title": d.get("title", "Untitled"),
                "permalink": f"{REDDIT_BASE}{d.get('permalink','')}",
                "author": d.get("author", "[deleted]"),
                "score": d.get("score", 0),
                "subreddit": d.get("subreddit", subreddit),
            }
            return img, meta
    return None
