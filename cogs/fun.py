import random
import disnake
from disnake.ext import commands
from utils.reddit import fetch_random_reddit_image
from utils.http import _get_json

CAT_FALLBACK_API = "https://api.thecatapi.com/v1/images/search"
MEME_FALLBACK_API = "https://meme-api.com/gimme"

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="fun", description="Fun & entertainment commands")
    async def fun_group(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @fun_group.sub_command(name="cat", description="Get a random cat picture.")
    async def cat(
        self,
        inter: disnake.ApplicationCommandInteraction,
        sort: str = commands.Param(default="hot"),
        time: str = commands.Param(default="day"),
        allow_nsfw: bool = commands.Param(default=False),
    ):
        await inter.response.defer()

        # First try Reddit
        img_url = await fetch_random_reddit_image(
            "cats",
            sort=sort,
            t=time,
            allow_nsfw=allow_nsfw,
        )

        # If Reddit fails, fallback to TheCatAPI
        if img_url is None:
            data = await _get_json(CAT_FALLBACK_API)
            if data and isinstance(data, list) and data[0].get("url"):
                img_url = data[0]["url"]

        if img_url is None:
            await inter.edit_original_response("Couldn't fetch a cat. Reality is broken.")
            return
        
        embed = disnake.Embed(title="Random Cat")
        embed.set_image(url=img_url)
        await inter.edit_original_response(embed=embed)

    @fun_group.sub_command(description="Send a random dog picture.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dog(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        data = await _get_json("https://random.dog/woof.json")
        url = data.get("url") if data else None
        if url and any(url.lower().endswith(v) for v in (".mp4",".webm",".mov")):
            data = await _get_json("https://random.dog/woof.json")
            url = data.get("url") if data else None
        if not url:
            return await inter.edit_original_response("Dog API had a moment.")
        embed = disnake.Embed(title="🐶 Woof", color=disnake.Color.blurple())
        embed.set_image(url=url)
        await inter.edit_original_response(embed=embed)

    @fun_group.sub_command(name="meme", description="Get a random meme.")
    async def meme(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subreddit: str = commands.Param(default="memes"),
    ):
        await inter.response.defer()

        # Try Reddit first
        img_url = await fetch_random_reddit_image(
            subreddit,
            sort="hot",
            t="day",
            allow_nsfw=False,
        )

        # If Reddit fails, try meme-api
        if img_url is None:
            data = await _get_json(MEME_FALLBACK_API)
            if data and data.get("url"):
                img_url = data["url"]

        if img_url is None:
            await inter.edit_original_response("Couldn't fetch a meme. The internet has failed us.")
            return

        embed = disnake.Embed(title=f"Random meme from r/{subreddit}")
        embed.set_image(url=img_url)
        await inter.edit_original_response(embed=embed)

    @fun_group.sub_command(name="8ball", description="Ask the magic 8-ball a question.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def eightball(self, inter: disnake.ApplicationCommandInteraction, question: str):
        await inter.response.defer()
        normal = [
            "It is certain.", "Without a doubt.", "Yes.", "Ask again later.",
            "Reply hazy, try again.", "Better not tell you now.", "Don’t count on it.",
            "My reply is no.", "Very doubtful."
        ]
        rude = [
            "No. And that question hurt my circuits.",
            "Absolutely not. Touch grass.",
            "Ask a better question."
        ]
        answer = random.choice(rude) if random.randint(1, 200) == 1 else random.choice(normal)
        embed = disnake.Embed(title="🎱 The Magic 8-Ball", color=disnake.Color.blurple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        await inter.edit_original_response(embed=embed)

    @fun_group.sub_command(description="Roll dice, e.g., 3d6 with optional modifier.")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def roll(
        self,
        inter: disnake.ApplicationCommandInteraction,
        count: int = commands.Param(default=1, ge=1, le=30, description="How many dice"),
        sides: int = commands.Param(default=6, choices=[4,6,8,10,12,20,100], description="Die type"),
        modifier: int = commands.Param(default=0, description="Add/subtract after rolling"),
    ):
        await inter.response.defer()
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        preview = ", ".join(map(str, rolls[:50])) + ("..." if len(rolls) > 50 else "")
        head = f"{count}d{sides}{('+' if modifier>=0 else '')}{modifier}"
        embed = disnake.Embed(title=f"🎲 {head}", color=disnake.Color.blurple())
        embed.add_field(name="Rolls", value=preview or "—", inline=False)
        embed.add_field(name="Total", value=str(total), inline=True)
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(Fun(bot))
