import os
import disnake
from disnake.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = disnake.Intents.default()
intents.message_content = False

sync_flags = commands.CommandSyncFlags.default()
sync_flags.sync_commands_debug = True

bot = commands.InteractionBot(
    intents=intents,
    command_sync_flags=sync_flags
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id={bot.user.id})")

initial_extensions = [
    "cogs.fun",
    "cogs.util",
    "cogs.context",
]

for ext in initial_extensions:
    try:
        bot.load_extension(ext)
        print(f"Loaded extension: {ext}")
    except Exception as e:
        print(f"Failed to load {ext}: {e}")

bot.run(TOKEN)
