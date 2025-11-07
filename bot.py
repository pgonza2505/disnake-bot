import disnake
from disnake.ext import commands
from disnake.ext.commands import Cog
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = disnake.Intents.default()
intents.message_content = False

sync_flags = commands.CommandSyncFlags.default()
sync_flags.sync_commands_debug = True

bot = commands.InteractionBot(intents=intents, command_sync_flags=sync_flags)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id={bot.user.id})")
    await bot.change_presence(activity=disnake.Game("Attention: This is not a drill."))

@bot.slash_command(description="Check bot latency.")
async def ping(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message(f"Pong! {round(bot.latency * 1000)} ms")

@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error):
    print(f"Slash command error: {error}")
    try:
        if not inter.response.is_done():
            await inter.response.send_message("That exploded. I'll log it.", ephemeral=True)
        else:
            await inter.followup.send("That exploded. I'll log it.", ephemeral=True)
    except:
        pass

class Fun(commands.Cog):
    @commands.Cog.listener("on_command_error")
    async def on_command_error(self, ctx, error):
        print(f"Prefix cmd error: {error}")

initial_extensions = ["cogs.fun", "cogs.cats", "cogs.entertainment", "cogs.utility"]

for ext in initial_extensions:
    try:
        bot.load_extension(ext)
        print(f"Loaded extension: {ext}")
    except Exception as e:
        print(f"Failed to load {ext}: {e}")


bot.run(TOKEN)
