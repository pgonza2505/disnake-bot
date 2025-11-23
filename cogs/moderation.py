import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import disnake
from disnake.ext import commands

DATA_DIR = Path("data")
WARN_FILE = DATA_DIR / "warnings.json"
MODLOG_FILE = DATA_DIR / "modlog.json"


# ------------- Warnings storage ------------- #

def _load_warnings() -> dict:
    if not WARN_FILE.exists():
        return {}
    try:
        with WARN_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_warnings(data: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with WARN_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ------------- Modlog config storage ------------- #

def _load_modlog() -> dict:
    if not MODLOG_FILE.exists():
        return {}
    try:
        with MODLOG_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_modlog(data: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with MODLOG_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class Moderation(commands.Cog):
    """Moderation commands: purge, slowmode, say, kick, ban, warns, timeouts, modlog."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    # ------------- Internal helpers ------------- #

    async def _send_modlog(self, guild: disnake.Guild, embed: disnake.Embed) -> None:
        """Send an embed to the configured modlog channel for this guild, if any."""
        data = _load_modlog()
        ch_id = data.get(str(guild.id))
        if not ch_id:
            return

        channel = guild.get_channel(ch_id)
        if channel is None:
            return

        try:
            await channel.send(embed=embed)
        except disnake.Forbidden:
            # Bot can't send messages there; silently ignore.
            pass

    # ------------- Basic moderation commands ------------- #

    @commands.slash_command(
        name="purge",
        description="Delete a number of messages from this channel.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_messages=True),
    )
    async def purge(
        self,
        inter: disnake.ApplicationCommandInteraction,
        amount: int = commands.Param(
            gt=0,
            le=500,
            description="How many messages to delete (max 500).",
        ),
    ):
        await inter.response.defer(ephemeral=True)
        deleted = await inter.channel.purge(limit=amount)
        count = len(deleted)
        await inter.edit_original_message(f"🧹 Deleted **{count}** messages.")

        embed = disnake.Embed(
            title="Messages Purged",
            color=disnake.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("Channel", inter.channel.mention, inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Amount", str(count), inline=True)
        await self._send_modlog(inter.guild, embed)

    @commands.slash_command(
        name="slowmode",
        description="Set slowmode delay for this channel.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_channels=True),
    )
    async def slowmode(
        self,
        inter: disnake.ApplicationCommandInteraction,
        seconds: int = commands.Param(
            ge=0,
            le=21600,
            description="Slowmode delay in seconds (0 = off, max 6h).",
        ),
    ):
        await inter.channel.edit(slowmode_delay=seconds)
        await inter.response.send_message(
            f"🐢 Slowmode set to **{seconds} seconds**.",
            ephemeral=True,
        )

        embed = disnake.Embed(
            title="Slowmode Updated",
            color=disnake.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("Channel", inter.channel.mention, inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Slowmode", f"{seconds} seconds", inline=True)
        await self._send_modlog(inter.guild, embed)

    @commands.slash_command(
        name="say",
        description="Make the bot say something in this channel.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_messages=True),
    )
    async def say(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message: str = commands.Param(description="What should the bot say?"),
    ):
        await inter.response.send_message("✅ Sent.", ephemeral=True)
        await inter.channel.send(message)

        embed = disnake.Embed(
            title="Bot Message Sent",
            color=disnake.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("Channel", inter.channel.mention, inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Content", message[:1024], inline=False)
        await self._send_modlog(inter.guild, embed)

    @commands.slash_command(
        name="kick",
        description="Kick a member from the server.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(kick_members=True),
    )
    async def kick(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Member to kick."),
        reason: str = commands.Param(
            default="No reason provided.",
            description="Reason for kicking.",
        ),
    ):
        if user == inter.author:
            return await inter.response.send_message(
                "You can’t kick yourself, touch grass instead.",
                ephemeral=True,
            )
        if user == inter.guild.me:
            return await inter.response.send_message(
                "I’m not kicking myself out of the server.",
                ephemeral=True,
            )

        await inter.response.send_message(f"👢 Kicked **{user}**.", ephemeral=True)
        await user.kick(reason=f"{inter.author} | {reason}")

        embed = disnake.Embed(
            title="Member Kicked",
            color=disnake.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("User", f"{user} ({user.id})", inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Reason", reason, inline=False)
        await self._send_modlog(inter.guild, embed)

    @commands.slash_command(
        name="ban",
        description="Ban a member from the server.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(ban_members=True),
    )
    async def ban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Member to ban."),
        reason: str = commands.Param(
            default="No reason provided.",
            description="Reason for banning.",
        ),
        delete_days: int = commands.Param(
            default=0,
            ge=0,
            le=7,
            description="Delete message history from the last X days (0–7).",
        ),
    ):
        if user == inter.author:
            return await inter.response.send_message(
                "You can’t ban yourself. Therapy maybe, but not ban.",
                ephemeral=True,
            )
        if user == inter.guild.me:
            return await inter.response.send_message(
                "I’m not banning myself. That’s your job.",
                ephemeral=True,
            )

        await inter.response.send_message(f"🔨 Banned **{user}**.", ephemeral=True)
        await inter.guild.ban(
            user,
            reason=f"{inter.author} | {reason}",
            delete_message_days=delete_days,
        )

        embed = disnake.Embed(
            title="Member Banned",
            color=disnake.Color.dark_red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("User", f"{user} ({user.id})", inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Reason", reason, inline=False)
        embed.add_field("Deleted Messages (days)", str(delete_days), inline=True)
        await self._send_modlog(inter.guild, embed)

    # ------------- Warn system ------------- #

    @commands.slash_command(
        name="warn",
        description="Warn a member; warning is stored.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(moderate_members=True),
    )
    async def warn(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Member to warn."),
        reason: str = commands.Param(
            default="No reason provided.",
            description="Reason for the warning.",
        ),
        dm_user: bool = commands.Param(
            default=True,
            description="DM the user about this warning?",
        ),
    ):
        if user.bot:
            return await inter.response.send_message(
                "I’m not warning other bots. They’re already suffering.",
                ephemeral=True,
            )

        data = _load_warnings()
        guild_key = str(inter.guild.id)
        user_key = str(user.id)
        guild_warnings = data.setdefault(guild_key, {})
        user_warnings = guild_warnings.setdefault(user_key, [])

        warning = {
            "mod_id": inter.author.id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        user_warnings.append(warning)
        _save_warnings(data)

        if dm_user:
            try:
                embed_dm = disnake.Embed(
                    title=f"You have received a warning in {inter.guild.name}",
                    description=reason,
                    color=disnake.Color.orange(),
                    timestamp=datetime.now(timezone.utc),
                )
                embed_dm.set_footer(text=f"Issued by {inter.author}")
                await user.send(embed=embed_dm)
            except disnake.Forbidden:
                pass

        count = len(user_warnings)
        await inter.response.send_message(
            f"⚠️ Warned **{user}** for: `{reason}`.\n"
            f"This user now has **{count}** warning(s).",
            ephemeral=True,
        )

        embed = disnake.Embed(
            title="Member Warned",
            color=disnake.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("User", f"{user} ({user.id})", inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Reason", reason, inline=False)
        embed.add_field("Total Warnings", str(count), inline=True)
        await self._send_modlog(inter.guild, embed)

    @commands.slash_command(
        name="warnings",
        description="Show warnings for a member.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(moderate_members=True),
    )
    async def warnings(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Member to view warnings for."),
    ):
        data = _load_warnings()
        guild_warnings = data.get(str(inter.guild.id), {})
        user_warnings = guild_warnings.get(str(user.id), [])

        if not user_warnings:
            return await inter.response.send_message(
                f"✅ **{user}** has no warnings on record.",
                ephemeral=True,
            )

        embed = disnake.Embed(
            title=f"Warnings for {user}",
            color=disnake.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        for idx, w in enumerate(user_warnings, start=1):
            ts = w.get("timestamp")
            try:
                ts_parsed = datetime.fromisoformat(ts)
                ts_str = disnake.utils.format_dt(ts_parsed, style="R")
            except Exception:
                ts_str = ts or "Unknown time"

            mod_id = w.get("mod_id")
            mod_mention = f"<@{mod_id}>" if mod_id else "Unknown"
            reason = w.get("reason", "No reason.")

            embed.add_field(
                name=f"#{idx} • {ts_str}",
                value=f"**Mod:** {mod_mention}\n**Reason:** {reason}",
                inline=False,
            )

        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(
        name="clearwarnings",
        description="Clear all warnings for a member.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(moderate_members=True),
    )
    async def clearwarnings(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Member whose warnings to clear."),
    ):
        data = _load_warnings()
        guild_key = str(inter.guild.id)
        user_key = str(user.id)

        guild_warnings = data.get(guild_key, {})
        user_warnings = guild_warnings.get(user_key)

        if not user_warnings:
            return await inter.response.send_message(
                f"ℹ️ **{user}** has no warnings.",
                ephemeral=True,
            )

        count = len(user_warnings)
        guild_warnings.pop(user_key, None)
        if not guild_warnings:
            data.pop(guild_key, None)
        _save_warnings(data)

        await inter.response.send_message(
            f"🧽 Cleared **{count}** warning(s) for **{user}**.",
            ephemeral=True,
        )

        embed = disnake.Embed(
            title="Warnings Cleared",
            color=disnake.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("User", f"{user} ({user.id})", inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Cleared Count", str(count), inline=True)
        await self._send_modlog(inter.guild, embed)

    # ------------- Timeouts ------------- #

    @commands.slash_command(
        name="timeout",
        description="Timeout a member for a period of time.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(moderate_members=True),
    )
    async def timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Member to timeout."),
        minutes: int = commands.Param(
            ge=1,
            le=10080,
            description="Duration in minutes (1–10080, up to 7 days).",
        ),
        reason: str = commands.Param(
            default="No reason provided.",
            description="Reason for the timeout.",
        ),
    ):
        if user == inter.author:
            return await inter.response.send_message(
                "Timing yourself out is just called going to bed.",
                ephemeral=True,
            )
        if user == inter.guild.me:
            return await inter.response.send_message(
                "I’m not timing myself out.",
                ephemeral=True,
            )

        duration = timedelta(minutes=minutes)
        try:
            await user.timeout(duration, reason=f"{inter.author} | {reason}")
        except AttributeError:
            try:
                await user.edit(timeout=datetime.now(timezone.utc) + duration, reason=f"{inter.author} | {reason}")
            except Exception as e:
                return await inter.response.send_message(
                    f"Failed to timeout user: `{e}`",
                    ephemeral=True,
                )

        await inter.response.send_message(
            f"⏰ Timed out **{user}** for **{minutes}** minute(s).",
            ephemeral=True,
        )

        embed = disnake.Embed(
            title="Member Timed Out",
            color=disnake.Color.dark_gold(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("User", f"{user} ({user.id})", inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Duration (min)", str(minutes), inline=True)
        embed.add_field("Reason", reason, inline=False)
        await self._send_modlog(inter.guild, embed)

    @commands.slash_command(
        name="untimeout",
        description="Remove a timeout from a member.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(moderate_members=True),
    )
    async def untimeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Member to remove timeout from."),
        reason: str = commands.Param(
            default="Timeout ended.",
            description="Reason for removing the timeout.",
        ),
    ):
        try:
            await user.timeout(None, reason=f"{inter.author} | {reason}")
        except AttributeError:
            try:
                await user.edit(timeout=None, reason=f"{inter.author} | {reason}")
            except Exception as e:
                return await inter.response.send_message(
                    f"Failed to remove timeout: `{e}`",
                    ephemeral=True,
                )

        await inter.response.send_message(
            f"✅ Removed timeout for **{user}**.",
            ephemeral=True,
        )

        embed = disnake.Embed(
            title="Timeout Removed",
            color=disnake.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field("User", f"{user} ({user.id})", inline=True)
        embed.add_field("Moderator", f"{inter.author} ({inter.author.id})", inline=True)
        embed.add_field("Reason", reason, inline=False)
        await self._send_modlog(inter.guild, embed)

    # ------------- Modlog configuration ------------- #

    @commands.slash_command(
        name="modlog",
        description="Configure moderation logging.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def modlog_group(self, inter: disnake.ApplicationCommandInteraction):
        # This is just the slash command group root; sub-commands are below.
        pass

    @modlog_group.sub_command(
        name="set",
        description="Set the channel where moderation logs will be sent.",
    )
    async def modlog_set(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(description="Channel to use for moderation logs."),
    ):
        data = _load_modlog()
        data[str(inter.guild.id)] = channel.id
        _save_modlog(data)

        await inter.response.send_message(
            f"📝 Modlog channel set to {channel.mention}.",
            ephemeral=True,
        )

    @modlog_group.sub_command(
        name="disable",
        description="Disable moderation logging for this server.",
    )
    async def modlog_disable(self, inter: disnake.ApplicationCommandInteraction):
        data = _load_modlog()
        removed = data.pop(str(inter.guild.id), None)
        _save_modlog(data)

        if removed:
            msg = "🛑 Modlog disabled for this server."
        else:
            msg = "ℹ️ No modlog was configured for this server."

        await inter.response.send_message(msg, ephemeral=True)

    @modlog_group.sub_command(
        name="show",
        description="Show the current modlog channel.",
    )
    async def modlog_show(self, inter: disnake.ApplicationCommandInteraction):
        data = _load_modlog()
        ch_id = data.get(str(inter.guild.id))

        if not ch_id:
            return await inter.response.send_message(
                "ℹ️ No modlog channel is configured for this server.",
                ephemeral=True,
            )

        channel = inter.guild.get_channel(ch_id)
        if channel is None:
            return await inter.response.send_message(
                f"⚠️ A modlog channel is configured, but I can't see it or it no longer exists (ID: `{ch_id}`).",
                ephemeral=True,
            )

        await inter.response.send_message(
            f"📜 Current modlog channel: {channel.mention}",
            ephemeral=True,
        )


def setup(bot: commands.InteractionBot):
    bot.add_cog(Moderation(bot))
