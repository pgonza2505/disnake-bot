import os
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = disnake.Intents.default()
intents.message_content = False

sync_flags = commands.CommandSyncFlags.default()
sync_flags.sync_commands_debug = True

bot = commands.InteractionBot(
    command_sync_flags=sync_flags,
    intents=intents,
)

bot.launch_time = datetime.now(timezone.utc)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id={bot.user.id})")

initial_extensions = [
    "cogs.fun",
    "cogs.util",
    "cogs.context",
    "cogs.moderation",
    "cogs.info",
    "cogs.spicy",
]

for ext in initial_extensions:
    try:
        bot.load_extension(ext)
        print(f"Loaded extension: {ext}")
    except Exception as e:
        print(f"Failed to load {ext}: {e}")

from utils.autoupdate import auto_update

def main():
    auto_update()
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
