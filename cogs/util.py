import asyncio, time, platform
import disnake
from disnake.ext import commands

BOOT_TIME = time.time()

def _fmt(seconds: float) -> str:
    s = int(seconds); m, s = divmod(s, 60); h, m = divmod(m, 60); d, h = divmod(h, 24)
    return " ".join([f"{d}d" if d else "", f"{h}h" if h else "", f"{m}m" if m else "", f"{s}s" if s or not (d or h or m) else "" ]).strip()

def _ts_rel(delta_sec: int) -> str:
    return f"<t:{int(time.time() + delta_sec)}:R>"

class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="util", description="Utility & QoL commands")
    async def util_group(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @util_group.sub_command(description="Show info about a user.")
    async def userinfo(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member | None = None):
        user = user or (inter.author if isinstance(inter.author, disnake.Member) else None)
        if user is None:
            return await inter.response.send_message("Use this in a server.", ephemeral=True)
        roles = [r.mention for r in user.roles if r.name != "@everyone"]
        embed = disnake.Embed(title=f"{user} • User Info", color=user.top_role.color if user.top_role else disnake.Color.blurple())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ID", value=str(user.id))
        embed.add_field(name="Joined", value=disnake.utils.format_dt(user.joined_at, style="R") if user.joined_at else "Unknown")
        embed.add_field(name="Created", value=disnake.utils.format_dt(user.created_at, style="R"))
        if roles:
            embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles)[:1024], inline=False)
        await inter.response.send_message(embed=embed)

    @util_group.sub_command(description="Show info about this server.")
    async def serverinfo(self, inter: disnake.ApplicationCommandInteraction):
        if not inter.guild:
            return await inter.response.send_message("Use this in a server.", ephemeral=True)
        g = inter.guild
        humans = sum(1 for m in g.members if not m.bot) if g.members else 0
        bots = sum(1 for m in g.members if m.bot) if g.members else 0
        embed = disnake.Embed(title=f"{g.name} • Server Info", color=disnake.Color.blurple())
        if g.icon: embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="ID", value=str(g.id))
        embed.add_field(name="Owner", value=str(g.owner) if g.owner else "Unknown")
        embed.add_field(name="Created", value=disnake.utils.format_dt(g.created_at, style="R"))
        embed.add_field(name="Members", value=f"Humans: {humans}\nBots: {bots}")
        embed.add_field(name="Channels", value=f"Text: {len(g.text_channels)} • Voice: {len(g.voice_channels)}")
        embed.add_field(name="Roles", value=str(len(g.roles)))
        await inter.response.send_message(embed=embed)

    @util_group.sub_command(description="Set a reminder.")
    async def remindme(
        self,
        inter: disnake.ApplicationCommandInteraction,
        minutes: int = commands.Param(ge=1, le=10080, default=10, description="When to remind (minutes)"),
        message: str = commands.Param(default="Reminder!", description="What to remind you about"),
        dm: bool = commands.Param(default=True, description="Send via DM if possible"),
    ):
        await inter.response.send_message(f"⏰ Reminding you {_ts_rel(minutes*60)}.", ephemeral=True)
        async def _task():
            try:
                await asyncio.sleep(minutes * 60)
                content = f"⏰ **Reminder:** {message}\nRequested {_ts_rel(-minutes*60)}."
                if dm:
                    try:
                        await inter.author.send(content); return
                    except disnake.Forbidden:
                        pass
                await inter.followup.send(content, allowed_mentions=disnake.AllowedMentions.none())
            except Exception:
                pass
        inter.bot.loop.create_task(_task())

    @util_group.sub_command(description="Create a quick poll with up to 5 options.")
    async def poll(
        self,
        inter: disnake.ApplicationCommandInteraction,
        question: str,
        option1: str,
        option2: str,
        option3: str = "",
        option4: str = "",
        option5: str = "",
        duration_seconds: int = commands.Param(default=60, ge=15, le=3600),
    ):
        from collections import Counter
        class View(disnake.ui.View):
            def __init__(self, opts, duration):
                super().__init__(timeout=duration)
                self.tallies = Counter()
                self.voted: dict[int,int] = {}
                for i, lab in enumerate(opts[:5]):
                    self.add_item(Btn(str(i), lab))
                self.message = None
            async def on_timeout(self):
                for c in self.children:
                    if isinstance(c, disnake.ui.Button): c.disabled = True
                if self.message:
                    total = sum(self.tallies.values())
                    if not total:
                        res = "No votes."
                    else:
                        lines = []
                        for c in self.children:
                            if isinstance(c, disnake.ui.Button):
                                lines.append(f"**{c.label}** — {self.tallies.get(c.custom_id,0)}")
                        res = "\n".join(lines)
                    emb = self.message.embeds[0].copy() if self.message.embeds else disnake.Embed()
                    emb.add_field(name="Results", value=res, inline=False)
                    await self.message.edit(embed=emb, view=self)
        class Btn(disnake.ui.Button):
            def __init__(self, cid, label):
                super().__init__(style=disnake.ButtonStyle.primary, label=label[:80], custom_id=cid)
            async def callback(self, i: disnake.MessageInteraction):
                v: View = self.view
                uid = i.author.id
                idx = int(self.custom_id)
                prev = v.voted.get(uid)
                if prev is not None and prev != idx:
                    v.tallies[str(prev)] -= 1
                if prev == idx:
                    v.voted.pop(uid, None); v.tallies[str(idx)] -= 1
                    msg = f"Removed your vote for **{self.label}**."
                else:
                    v.voted[uid] = idx; v.tallies[str(idx)] += 1
                    msg = f"You voted for **{self.label}**."
                try: await i.response.send_message(msg, ephemeral=True)
                except disnake.InteractionResponded: await i.followup.send(msg, ephemeral=True)

        options = [o for o in [option1, option2, option3, option4, option5] if o]
        if len(options) < 2:
            return await inter.response.send_message("Need at least 2 options.", ephemeral=True)

        view = View(options, duration_seconds)
        embed = disnake.Embed(title="📊 Poll", description=question, color=disnake.Color.blurple())
        embed.set_footer(text=f"Closes {_ts_rel(duration_seconds)}")
        await inter.response.send_message(embed=embed, view=view)
        view.message = await inter.original_message()

    @util_group.sub_command(description="Show bot stats.")
    async def stats(self, inter: disnake.ApplicationCommandInteraction):
        uptime = _fmt(time.time() - BOOT_TIME)
        ping = f"{round(self.bot.latency * 1000)} ms"
        embed = disnake.Embed(title="Bot Stats", color=disnake.Color.blurple())
        embed.add_field(name="Ping", value=ping)
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Python", value=platform.python_version())
        await inter.response.send_message(embed=embed)

    @util_group.sub_command(description="Define an English word.")
    async def define(self, inter: disnake.ApplicationCommandInteraction, word: str):
        await inter.response.send_message(f"Looking up **{word}**...", ephemeral=True)
        import json, urllib.request, urllib.error
        def _get(url: str):
            req = urllib.request.Request(url, headers={"User-Agent":"disnake-bot/util"})
            try:
                with urllib.request.urlopen(req, timeout=8) as r:
                    if r.status != 200: return None
                    return json.loads(r.read().decode("utf-8", "replace"))
            except Exception:
                return None
        data = _get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        if not data or not isinstance(data, list):
            return await inter.followup.send(f"Couldn’t fetch a definition for **{word}**.")
        entry = data[0]; meanings = entry.get("meanings", [])
        if not meanings:
            return await inter.followup.send(f"No definitions found for **{word}**.")
        defs = []
        for m in meanings:
            part = m.get("partOfSpeech","")
            for d in m.get("definitions",[])[:1]:
                txt = d.get("definition","")
                if txt: defs.append(f"*{part}*: {txt}")
            if len(defs) >= 3: break
        emb = disnake.Embed(title=f"📚 {word}", description="\n".join(defs)[:4000] or "No definition text.", color=disnake.Color.blurple())
        phon = entry.get("phonetic") or ""
        if phon: emb.set_footer(text=phon)
        await inter.followup.send(embed=emb)

def setup(bot):
    bot.add_cog(Util(bot))
