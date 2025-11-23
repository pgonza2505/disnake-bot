import random
import aiohttp
import disnake
from disnake import Option
from disnake.ext import commands
import urllib.parse

# spicy.py - Disnake cog to fetch images from api.rule34.xxx with illegal-tag blacklist

BLACKLIST = {
    "child", "children", "minor", "underage", "infant", "baby", "kid",
    "young", "young-looking", "lolicon", "loli", "shota", "bestiality", "animal"
}

API_BASE = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&tags="

def contains_blacklisted(tags: str) -> bool:
    tl = tags.lower()
    for bad in BLACKLIST:
        if bad in tl:
            return True
    return False

def is_video_url(url: str) -> bool:
    if not url:
        return False
    url = url.lower()
    return url.endswith((".mp4", ".webm", ".mov", ".avi", ".mkv"))

class Spicy(commands.Cog):
    """R34 image fetcher. Restricts blacklisted/illegal tags and requires NSFW channel."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    async def fetch_posts(self, tags: str):
        url = API_BASE + urllib.parse.quote_plus(tags)
        async with self.session.get(url, timeout=15) as resp:
            if resp.status != 200:
                return None
            try:
                data = await resp.json()
            except Exception:
                return None
        # API may return a list or dict; normalize to list of posts
        if isinstance(data, dict):
            posts = data.get("post") or data.get("posts") or []
        else:
            posts = data
        return posts or []

    @commands.command(name="r34", aliases=("rule34",))
    async def r34(self, ctx: commands.Context, *, tags: str = ""):
        """Fetch a random image from rule34.xxx. Usage: !r34 tag1 tag2"""
        if not ctx.channel.is_nsfw():
            await ctx.reply("This command can only be used in NSFW channels.", delete_after=10)
            return

        tags = tags.strip()
        if not tags:
            await ctx.reply("Provide at least one tag.", delete_after=10)
            return

        if contains_blacklisted(tags):
            await ctx.reply("Request refused: contains illegal or blacklisted tags.", delete_after=10)
            return

        await ctx.typing()
        posts = await self.fetch_posts(tags)
        if posts is None:
            await ctx.reply("Failed to contact API.", delete_after=10)
            return
        if not posts:
            await ctx.reply("No results found.", delete_after=10)
            return

        post = random.choice(posts)
        # common fields: file_url, sample_url, preview_url
        url = post.get("file_url") or post.get("jpeg_url") or post.get("sample_url") or post.get("preview_url")
        if not url:
            await ctx.reply("No usable image URL returned.", delete_after=10)
            return

        embed = disnake.Embed(title="Rule34", color=0xED1C24)
        embed.set_image(url=url)
        pid = post.get("id") or post.get("post_id")
        ptags = post.get("tags") or post.get("tag_string") or ""
        if pid:
            embed.description = f"ID: {pid}"
        if ptags:
            embed.set_footer(text=("Tags: " + (ptags[:400] + "..." if len(ptags) > 400 else ptags)))
        await ctx.send(embed=embed)

    @commands.slash_command(name="r34", description="Fetch images from rule34.xxx (NSFW only)")
    async def r34_slash(
        self,
        inter: disnake.ApplicationCommandInteraction,
        tags: str = Option(" ", "Space-separated tags (max 5)"),
        results: int = Option(1, "Number of results (1-5)", min_value=1, max_value=5),
        videos: bool = Option(False, "Include video files (mp4/webm/etc.)")
    ):
        """
        Slash command to fetch up to `results` images (max 5), with up to 5 tags.
        videos=True will include video files; otherwise videos are filtered out.
        """
        # NSFW check
        if not inter.channel or not inter.channel.is_nsfw():
            await inter.response.send_message("This command can only be used in NSFW channels.", ephemeral=True)
            return

        tags = (tags or "").strip()
        if not tags:
            await inter.response.send_message("Provide at least one tag.", ephemeral=True)
            return

        tag_list = tags.split()
        if len(tag_list) > 5:
            await inter.response.send_message("You may provide at most 5 tags.", ephemeral=True)
            return

        if contains_blacklisted(tags):
            await inter.response.send_message("Request refused: contains illegal or blacklisted tags.", ephemeral=True)
            return

        await inter.response.defer()  # give more time for API call

        posts = await self.fetch_posts(tags)
        if posts is None:
            await inter.followup.send("Failed to contact API.", ephemeral=True)
            return

        # Filter posts that have usable file URLs
        usable = []
        for p in posts:
            url = p.get("file_url") or p.get("jpeg_url") or p.get("sample_url") or p.get("preview_url")
            if not url:
                continue
            if not videos and is_video_url(url):
                continue
            usable.append(p)

        if not usable:
            await inter.followup.send("No results found matching criteria.", ephemeral=True)
            return

        # choose up to `results` unique random posts
        if len(usable) <= results:
            chosen = usable
        else:
            chosen = random.sample(usable, results)

        for post in chosen:
            url = post.get("file_url") or post.get("jpeg_url") or post.get("sample_url") or post.get("preview_url")
            embed = disnake.Embed(title="Rule34", color=0xED1C24)
            embed.set_image(url=url)
            pid = post.get("id") or post.get("post_id")
            ptags = post.get("tags") or post.get("tag_string") or ""
            if pid:
                embed.description = f"ID: {pid}"
            if ptags:
                embed.set_footer(text=("Tags: " + (ptags[:400] + "..." if len(ptags) > 400 else ptags)))
            await inter.followup.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Spicy(bot))