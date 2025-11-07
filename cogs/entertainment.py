import random
import asyncio
import aiohttp
import disnake
from disnake.ext import commands

UA = "disnake-bot/1.0 (by u/NightFreddyF12)"
REDDIT_BASE = "https://www.reddit.com"

async def _get_json(url: str, *, headers: dict | None = None, timeout: int = 10):
    headers = headers or {}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=timeout) as resp:
                if resp.status != 200:
                    return None
                try:
                    return await resp.json()
                except aiohttp.ContentTypeError:
                    return None
    except (aiohttp.ClientConnectorError, aiohttp.ClientConnectorDNSError, asyncio.TimeoutError):
        return None
    except aiohttp.ClientError:
        return None

QUOTES_FALLBACK = {
    "inspirational": [
        ("The only way out is through.", "Robert Frost"),
        ("What we do now echoes in eternity.", "Marcus Aurelius"),
        ("Do or do not. There is no try.", "Yoda"),
    ],
    "wisdom": [
        ("Knowing yourself is the beginning of all wisdom.", "Aristotle"),
        ("The unexamined life is not worth living.", "Socrates"),
        ("Measure what is measurable, and make measurable what is not.", "Galileo"),
    ],
    "famous": [
        ("I think, therefore I am.", "René Descartes"),
        ("Float like a butterfly, sting like a bee.", "Muhammad Ali"),
        ("Stay hungry, stay foolish.", "Steve Jobs"),
    ],
    "technology": [
        ("Any sufficiently advanced technology is indistinguishable from magic.", "Arthur C. Clarke"),
        ("Programs must be written for people to read.", "Harold Abelson"),
        ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ],
    "humor": [
        ("I can resist everything except temptation.", "Oscar Wilde"),
        ("I refuse to join any club that would have me as a member.", "Groucho Marx"),
        ("I’m not lazy, I’m on energy-saving mode.", "Unknown"),
    ],
}

def _reddit_image_from_post(post: dict, allow_nsfw: bool) -> str | None:
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

async def _fetch_random_reddit_image(subreddit: str, *, allow_nsfw: bool, sort: str = "hot", t: str = "day"):
    params = "?limit=50"
    if sort == "top":
        params += f"&t={t}"
    url = f"{REDDIT_BASE}/r/{subreddit}/{sort}.json{params}"

    payload = await _get_json(url, headers={"User-Agent": UA})
    if not payload:
        return None

    posts = payload.get("data", {}).get("children", [])
    random.shuffle(posts)
    for post in posts:
        img = _reddit_image_from_post(post, allow_nsfw)
        if img:
            d = post["data"]
            meta = {
                "title": d.get("title", "Untitled"),
                "permalink": f"{REDDIT_BASE}{d.get('permalink', '')}",
                "author": d.get("author", "[deleted]"),
                "score": d.get("score", 0),
                "sub": d.get("subreddit", subreddit),
            }
            return img, meta
    return None

class Entertainment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Send a random dog picture.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dog(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        data = await _get_json("https://random.dog/woof.json")
        if not data:
            return await inter.edit_original_response("Dog API had a bone to pick. Try again.")

        url = data.get("url")
        if url and any(url.lower().endswith(ext) for ext in (".mp4", ".webm", ".mov")):
            # try again once
            data = await _get_json("https://random.dog/woof.json")
            url = data.get("url") if data else None

        if not url:
            return await inter.edit_original_response("No dogs fetched. Rude.")
        embed = disnake.Embed(title="🐶 Woof", color=disnake.Color.blurple())
        embed.set_image(url=url)
        await inter.edit_original_response(embed=embed)

    @commands.slash_command(description="Send a random meme.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme(
        self,
        inter: disnake.ApplicationCommandInteraction,
        kind: str = commands.Param(
            default="memes",
            choices=["memes", "dankmemes", "meirl", "wholesomememes", "ProgrammerHumor"],
            description="Which kind of meme?"
        ),
        sort: str = commands.Param(
            default="hot", choices=["hot", "new", "top"], description="Sort type"
        ),
        time: str = commands.Param(
            default="day", choices=["hour", "day", "week", "month", "year", "all"], description="Time range for 'top'"
        ),
        allow_nsfw: bool = commands.Param(default=False, description="Allow NSFW if channel allows it"),
    ):
        if allow_nsfw and not getattr(inter.channel, "is_nsfw", lambda: False)():
            return await inter.response.send_message("Not posting NSFW in a non-NSFW channel.", ephemeral=True)

        await inter.response.defer()
        result = await _fetch_random_reddit_image(kind, allow_nsfw=allow_nsfw, sort=sort, t=time)
        if not result:
            return await inter.edit_original_response(f"r/{kind} didn’t cooperate. Try another kind.")
        img_url, meta = result

        embed = disnake.Embed(title=meta["title"], url=meta["permalink"], color=disnake.Color.blurple())
        embed.set_image(url=img_url)
        embed.set_footer(text=f"r/{meta['sub']} • by u/{meta['author']} • {meta['score']} upvotes")
        await inter.edit_original_response(embed=embed)

    # Quotes are currently broken.
    @commands.slash_command(description="Get a random quote.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def quote(
        self,
        inter: disnake.ApplicationCommandInteraction,
        kind: str = commands.Param(
            default="inspirational",
            choices=["inspirational", "wisdom", "famous", "technology", "humor"],
            description="Quote type"
        ),
    ):
        await inter.response.defer()

        tag_map = {
            "inspirational": "inspirational",
            "wisdom": "wisdom",
            "famous": "famous-quotes",
            "technology": "technology",
            "humor": "humor",
        }
        tag = tag_map.get(kind, "inspirational")

        data = await _get_json(f"https://api.quotable.io/random?tags={tag}", headers={"User-Agent": UA})

        if data and "content" in data:
            content = data.get("content", "...")
            author = data.get("author", "Unknown")
        else:
            q = random.choice(QUOTES_FALLBACK.get(kind, QUOTES_FALLBACK["inspirational"]))
            content, author = q

        embed = disnake.Embed(description=f"“{content}”\n— **{author}**", color=disnake.Color.blurple())
        embed.set_footer(text=f"Type: {kind}{' • fallback' if not data else ''}")
        await inter.edit_original_response(embed=embed)

    @commands.slash_command(description="Ask the magic 8-ball a question.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def eightball(self, inter: disnake.ApplicationCommandInteraction, question: str):
        await inter.response.defer()
        normal_responses = [
            "It is certain.", "Without a doubt.", "You may rely on it.", "Yes.",
            "Ask again later.", "Reply hazy, try again.", "Better not tell you now.",
            "Don't count on it.", "My reply is no.", "Very doubtful."
        ]
        rare_rude_responses = [
            "No. And that question hurt my circuits.",
            "Absolutely not. Touch grass.",
            "Ask a better question.",
        ]
        if random.randint(1, 200) == 1:
            answer = random.choice(rare_rude_responses)
        else:
            answer = random.choice(normal_responses)

        embed = disnake.Embed(title="🎱 The Magic 8-Ball", color=disnake.Color.blurple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        await inter.edit_original_response(embed=embed)

    @commands.slash_command(description="Roll dice, like 3d6.")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def roll(
        self,
        inter: disnake.ApplicationCommandInteraction,
        count: int = commands.Param(default=1, ge=1, le=30, description="How many dice"),
        sides: int = commands.Param(
            default=6,
            choices=[4, 6, 8, 10, 12, 20, 100],
            description="What kind of die"
        ),
        modifier: int = commands.Param(default=0, description="Add or subtract after rolling"),
    ):
        await inter.response.defer()
        if count < 1 or count > 30:
            return await inter.edit_original_response("Pick between 1 and 30 dice.")

        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier

        rolls_preview = ", ".join(map(str, rolls[:50]))
        if len(rolls) > 50:
            rolls_preview += ", ..."

        embed = disnake.Embed(title=f"🎲 {count}d{sides}{'+' if modifier>=0 else ''}{modifier}", color=disnake.Color.blurple())
        embed.add_field(name="Rolls", value=rolls_preview, inline=False)
        embed.add_field(name="Total", value=str(total), inline=True)
        await inter.edit_original_response(embed=embed)


def setup(bot):
    bot.add_cog(Entertainment(bot))