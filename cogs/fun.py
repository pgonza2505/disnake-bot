import disnake
from disnake.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Echo back your text.")
    async def echo(self, inter: disnake.ApplicationCommandInteraction, message: str):
        await inter.response.send_message(message)
    
    @commands.user_command(name="Greet")
    async def greet_user(self, inter: disnake.UserCommandInteraction, user: disnake.User):
        await inter.response.send_message(f"Hey {user.mention}!")
    
    @commands.slash_command(description="Show a user's profile picture.")
    async def pfp(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User | None = commands.Param(default=None, description="Whose avatar"),
        server_avatar: bool = commands.Param(default=True, description="Prefer server avatar if available"),
        size: int = commands.Param(default=1024, choices=[128, 256, 512, 1024, 2048], description="Image size"),
    ):
        target = user or inter.author

        if isinstance(target, disnake.Member):
            asset = (target.guild_avatar or target.display_avatar) if server_avatar else target.display_avatar
        else:
            asset = target.display_avatar

        asset = asset.with_size(size)
        png = asset.with_format("png").url
        jpg = asset.with_format("jpg").url
        webp = asset.with_format("webp").url

        embed = disnake.Embed(title=f"{target.display_name}'s avatar", color=disnake.Color.blurple())
        embed.set_image(url=png)
        embed.set_footer(text=f"{size}px • server_avatar={server_avatar}")

        await inter.response.send_message(
            f"Links: [PNG]({png}) | [JPG]({jpg}) | [WEBP]({webp})",
            embed=embed
        )

def setup(bot):
    bot.add_cog(Fun(bot))