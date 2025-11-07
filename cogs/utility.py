
import asyncio
import time
import platform
from collections import Counter

import disnake
from disnake.ext import commands

BOOT_TIME = time.time()

def _ts_rel(seconds_from_now: int) -> str:
    """Discord relative timestamp: <t:unix:R>"""
    return f"<t:{int(time.time() + seconds_from_now)}:R>"

def _fmt_seconds(secs: float) -> str:
    secs = int(secs)
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s or not parts: parts.append(f"{s}s")
    return " ".join(parts)

import json
import urllib.request
import urllib.error

def _http_get_json(url: str, timeout: int = 8):
    req = urllib.request.Request(url, headers={"User-Agent": "disnake-bot/utility"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            data = resp.read()
            return json.loads(data.decode("utf-8", errors="replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None


class PollView(disnake.ui.View):
    def __init__(self, options: list[str], author_id: int, duration: int = 60):
        super().__init__(timeout=duration)
        self.author_id = author_id
        self.tallies = Counter()
        self.votes_by_user: dict[int, int] = {}
        for idx, label in enumerate(options[:5]):
            self.add_item(PollButton(idx, label))
        self.message: disnake.Message | None = None

    async def on_timeout(self) -> None:
        for child in self.children:
            if isinstance(child, disnake.ui.Button):
                child.disabled = True
        if self.message:
            total = sum(self.tallies.values())
            if total == 0:
                desc = "No votes. Democracy cancelled."
            else:
                lines = []
                for child in self.children:
                    if isinstance(child, disnake.ui.Button):
                        count = self.tallies.get(child.custom_id, 0)
                        lines.append(f"**{child.label}** — {count}")
                desc = "\n".join(lines)
            embed = self.message.embeds[0].copy() if self.message.embeds else disnake.Embed()
            embed.add_field(name="Results", value=desc or "No votes.", inline=False)
            await self.message.edit(embed=embed, view=self)


class PollButton(disnake.ui.Button):
    def __init__(self, index: int, label: str):
        super().__init__(style=disnake.ButtonStyle.primary, label=label[:80], custom_id=str(index))

    async def callback(self, inter: disnake.MessageInteraction):
        view: PollView = self.view
        uid = inter.author.id
        prev = view.votes_by_user.get(uid)
        idx = int(self.custom_id)

        if prev is not None and prev != idx:
            view.tallies[str(prev)] -= 1
        if prev == idx:
            view.votes_by_user.pop(uid, None)
            view.tallies[str(idx)] -= 1
            note = f"Removed your vote for **{self.label}**."
        else:
            view.votes_by_user[uid] = idx
            view.tallies[str(idx)] += 1
            note = f"You voted for **{self.label}**."

        try:
            await inter.response.send_message(note, ephemeral=True)
        except disnake.InteractionResponded:
            await inter.followup.send(note, ephemeral=True)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Show info about a user.")
    async def userinfo(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member | None = commands.Param(default=None, description="User to inspect")
    ):
        user = user or (inter.author if isinstance(inter.author, disnake.Member) else None)
        if user is None:
            return await inter.response.send_message("This only works in servers.", ephemeral=True)

        roles = [r.mention for r in user.roles if r.name != "@everyone"]
        embed = disnake.Embed(title=f"{user} • User Info", color=user.top_role.color if user.top_role else disnake.Color.blurple())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ID", value=str(user.id))
        embed.add_field(name="Joined Server", value=disnake.utils.format_dt(user.joined_at, style="R") if user.joined_at else "Unknown")
        embed.add_field(name="Account Created", value=disnake.utils.format_dt(user.created_at, style="R"))
        if roles:
            embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles)[:1024], inline=False)
        embed.set_footer(text=f"Server avatar shown if set.")
        await inter.response.send_message(embed=embed)

    @commands.slash_command(description="Show info about this server.")
    async def serverinfo(self, inter: disnake.ApplicationCommandInteraction):
        if not inter.guild:
            return await inter.response.send_message("This only works in servers.", ephemeral=True)

        g = inter.guild
        humans = sum(1 for m in g.members if not m.bot) if g.members else "—"
        bots = sum(1 for m in g.members if m.bot) if g.members else "—"
        embed = disnake.Embed(title=f"{g.name} • Server Info", color=disnake.Color.blurple())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="ID", value=str(g.id))
        embed.add_field(name="Owner", value=str(g.owner) if g.owner else "Unknown")
        embed.add_field(name="Created", value=disnake.utils.format_dt(g.created_at, style="R"))
        embed.add_field(name="Members", value=f"Humans: {humans}\nBots: {bots}")
        embed.add_field(name="Channels", value=f"Text: {len(g.text_channels)} • Voice: {len(g.voice_channels)}")
        embed.add_field(name="Roles", value=str(len(g.roles)))
        await inter.response.send_message(embed=embed)

    @commands.slash_command(description="Set a reminder.")
    async def remindme(
        self,
        inter: disnake.ApplicationCommandInteraction,
        minutes: int = commands.Param(ge=1, le=10080, default=10, description="When to remind (minutes)"),
        message: str = commands.Param(default="Reminder!", description="What to remind you about"),
        dm: bool = commands.Param(default=True, description="Send reminder via DM instead of this channel"),
    ):
        await inter.response.send_message(f"⏰ Reminding you {_ts_rel(minutes*60)}.", ephemeral=True)

        async def _task():
            try:
                await asyncio.sleep(minutes * 60)
                content = f"⏰ **Reminder:** {message}\nRequested {_ts_rel(-minutes*60)}."
                if dm:
                    try:
                        await inter.author.send(content)
                        return
                    except disnake.Forbidden:
                        await inter.followup.send(content, allowed_mentions=disnake.AllowedMentions.none())
            except Exception:
                pass

        inter.bot.loop.create_task(_task())

    @commands.slash_command(description="Create a quick button poll (auto-closes).")
    async def poll(
        self,
        inter: disnake.ApplicationCommandInteraction,
        question: str = commands.Param(description="What are we voting on?"),
        option1: str = commands.Param(description="Option 1"),
        option2: str = commands.Param(description="Option 2"),
        option3: str = commands.Param(default="", description="Option 3 (optional)"),
        option4: str = commands.Param(default="", description="Option 4 (optional)"),
        option5: str = commands.Param(default="", description="Option 5 (optional)"),
        duration_seconds: int = commands.Param(default=60, ge=15, le=3600, description="How long the poll runs"),
    ):
        options = [o for o in [option1, option2, option3, option4, option5] if o]
        if len(options) < 2:
            return await inter.response.send_message("Need at least 2 options.", ephemeral=True)

        view = PollView(options, inter.author.id, duration=duration_seconds)
        embed = disnake.Embed(title="📊 Poll", description=question, color=disnake.Color.blurple())
        embed.set_footer(text=f"Closes {_ts_rel(duration_seconds)}")
        await inter.response.send_message(embed=embed, view=view)
        msg = await inter.original_message()
        view.message = msg

    @commands.slash_command(description="Show bot stats.")
    async def stats(self, inter: disnake.ApplicationCommandInteraction):
        uptime = _fmt_seconds(time.time() - BOOT_TIME)
        ping = f"{round(self.bot.latency * 1000)} ms"

        mem = "n/a"
        try:
            import os, tracemalloc
            tracemalloc.start()
            _, peak = tracemalloc.get_traced_memory()
            mem = f"{peak/1024/1024:.1f} MB (peak, tracer)"
            tracemalloc.stop()
        except Exception:
            pass

        embed = disnake.Embed(title="Bot Stats", color=disnake.Color.blurple())
        embed.add_field(name="Ping", value=ping)
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Python", value=platform.python_version())
        embed.add_field(name="Memory", value=mem)
        await inter.response.send_message(embed=embed)

    @commands.slash_command(description="Define an English word.")
    async def define(
        self,
        inter: disnake.ApplicationCommandInteraction,
        word: str = commands.Param(description="Word to define")
    ):
        await inter.response.send_message(f"Looking up **{word}**...", ephemeral=True)

        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        data = _http_get_json(url)

        if not data or not isinstance(data, list):
            return await inter.followup.send(f"Couldn’t fetch a definition for **{word}**.")

        entry = data[0]
        meanings = entry.get("meanings", [])
        if not meanings:
            return await inter.followup.send(f"No definitions found for **{word}**.")

        defs = []
        for m in meanings:
            part = m.get("partOfSpeech", "")
            for d in m.get("definitions", [])[:1]:
                text = d.get("definition", "")
                if text:
                    defs.append(f"*{part}*: {text}")
            if len(defs) >= 3:
                break

        embed = disnake.Embed(title=f"📚 {word}", color=disnake.Color.blurple())
        embed.description = "\n".join(defs)[:4000] or "No definition text."
        phon = entry.get("phonetic") or ""
        if phon:
            embed.set_footer(text=phon)

        await inter.followup.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
