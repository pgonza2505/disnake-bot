import platform
from datetime import datetime, timezone

import disnake
from disnake.ext import commands


class Info(commands.Cog):
    """General information commands like /stats and /help."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    # /stats
    @commands.slash_command(
        name="stats",
        description="Show bot statistics.",
        dm_permission=False,
    )
    async def stats(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        now = datetime.now(timezone.utc)
        launch_time = getattr(self.bot, "launch_time", now)
        delta = now - launch_time

        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        uptime_str_parts = []
        if days:
            uptime_str_parts.append(f"{days}d")
        if hours:
            uptime_str_parts.append(f"{hours}h")
        if minutes:
            uptime_str_parts.append(f"{minutes}m")
        uptime_str_parts.append(f"{seconds}s")
        uptime_str = " ".join(uptime_str_parts)

        latency_ms = round(self.bot.latency * 1000)

        embed = disnake.Embed(
            title="Bot Statistics",
            color=disnake.Color.blurple(),
            timestamp=now,
        )
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Latency", value=f"{latency_ms} ms", inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(
            name="Users (approx.)",
            value=str(len(self.bot.users)),
            inline=True,
        )
        embed.add_field(
            name="Python",
            value=platform.python_version(),
            inline=True,
        )
        embed.add_field(
            name="disnake",
            value=disnake.__version__,
            inline=True,
        )
        embed.set_footer(text="Running on your friendly neighborhood Pi")

        await inter.edit_original_message(embed=embed)

    # /help
    @commands.slash_command(
        name="help",
        description="Show information about available commands.",
        dm_permission=False,
    )
    async def help_command(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
            title="disnake bot • Help",
            description="Here’s what I can do. Command names are shown without `/`.",
            color=disnake.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )

        # Adjust these lists if you add/remove commands later.
        embed.add_field(
            name="🎉 Fun",
            value=(
                "`cat` – random cat picture\n"
                "`dog` – random dog picture\n"
                "`meme` – random meme\n"
                "`eightball` – magic 8-ball\n"
                "`roll` – roll dice, like `3d6`\n"
            ),
            inline=False,
        )

        embed.add_field(
            name="🛠 Utility",
            value=(
                "`ping` – check latency\n"
                "`echo` – repeat your text\n"
                "`pfp` – show a user’s avatar\n"
                "`stats` – bot stats\n"
                "`help` – this message\n"
            ),
            inline=False,
        )

        embed.add_field(
            name="🛡 Moderation",
            value=(
                "`purge` – delete messages\n"
                "`slowmode` – set channel slowmode\n"
                "`say` – bot sends a message\n"
                "`kick` – kick a member\n"
                "`ban` – ban a member\n"
                "`warn` – add a warning\n"
                "`warnings` – view warnings\n"
                "`clearwarnings` – clear warnings\n"
                "`timeout` – timeout a member\n"
                "`untimeout` – remove timeout\n"
                "`modlog set/disable/show` – configure mod logs\n"
            ),
            inline=False,
        )

        embed.set_footer(text="Commands may be restricted by your server permissions.")

        await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot: commands.InteractionBot):
    bot.add_cog(Info(bot))
