import random
import aiohttp
import disnake
from disnake.ext import commands

REDDIT_BASE = "https://www.reddit.com"
UA = "disnake-bot/1.0 (by u/your_username_or_bot_name)"

def _good_image(post: dict, allow_nsfw: bool) -> str | None:
    """Return a direct image URL if the post looks usable, else None."""
    data = post.get("data", {})
    if not data:
        return None

    if data.get("over_18") and not allow_nsfw:
        return None

    url = data.get("url_overridden_by_dest") or data.get("url")
    if not url:
        return None

    lower = url.lower()
    if any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".gifv", ".webp")):
        if lower.endswith(".gifv"):
            url = url[:-1]
        return url

    if "i.redd.it" in lower or "preview.redd.it" in lower or "i.imgur.com" in lower:
        return url

    if data.get("is_gallery") or data.get("is_video"):
        return None

    return None


async def fetch_random_reddit_image(subreddit: str, sort: str, time: str, allow_nsfw: bool):
    """
    Returns (image_url, meta) or None.
    meta contains title, permalink, author, score.
    """
    if sort not in {"hot", "new", "top"}:
        sort = "hot"

    params = "?limit=50"
    if sort == "top":
        params += f"&t={time}"

    url = f"{REDDIT_BASE}/r/{subreddit}/{sort}.json{params}"

    async with aiohttp.ClientSession(headers={"User-Agent": UA}) as session:
        async with session.get(url, timeout=10) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()

    posts = payload.get("data", {}).get("children", [])
    random.shuffle(posts)

    for post in posts:
        img = _good_image(post, allow_nsfw)
        if not img:
            continue

        data = post["data"]
        meta = {
            "title": data.get("title", "Untitled"),
            "permalink": f"{REDDIT_BASE}{data.get('permalink', '')}",
            "author": data.get("author", "[deleted]"),
            "score": data.get("score", 0),
            "subreddit": data.get("subreddit", subreddit),
        }
        return img, meta

    return None


async def cataas_fallback() -> str:
    """Random cat from cataas.com (no API key)."""
    return "https://cataas.com/cat"


class Cats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Send a random cat picture from a cat subreddit.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def cat(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subreddit: str = commands.Param(
            default="cats", description="Which subreddit? (cats, catpictures, catpics...)"
        ),
        sort: str = commands.Param(
            default="hot",
            choices=["hot", "new", "top"],
            description="Sort type"
        ),
        time: str = commands.Param(
            default="day",
            choices=["hour", "day", "week", "month", "year", "all"],
            description="Time range (for 'top')"
        ),
        allow_nsfw: bool = commands.Param(
            default=False,
            description="Include NSFW if the channel allows it"
        ),
    ):
        if allow_nsfw and not getattr(inter.channel, "is_nsfw", lambda: False)():
            return await inter.response.send_message(
                "Not posting NSFW cats in a non-NSFW channel.",
                ephemeral=True
            )

        await inter.response.defer()

        result = await fetch_random_reddit_image(subreddit, sort, time, allow_nsfw)
        if result is None:
            img_url = await cataas_fallback()
            embed = disnake.Embed(
                title=f"r/{subreddit} didn’t cooperate. Here’s a cat anyway.",
                color=disnake.Color.blurple()
            )
            embed.set_image(url=img_url)
            return await inter.edit_original_response(embed=embed)

        img_url, meta = result
        title = meta["title"]
        permalink = meta["permalink"]
        author = meta["author"]
        score = meta["score"]
        sub = meta["subreddit"]

        embed = disnake.Embed(title=title, url=permalink, color=disnake.Color.blurple())
        embed.set_image(url=img_url)
        embed.set_footer(text=f"r/{sub} • by u/{author} • {score} upvotes")

        await inter.edit_original_response(embed=embed)


def setup(bot):
    bot.add_cog(Cats(bot))