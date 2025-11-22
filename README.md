# disnake-bot

![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)
![Python 3.13](https://img.shields.io/badge/python%203.13-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)

A small, modular Discord bot built with [disnake]. It uses slash commands, context menus, and command groups for clean organization.

## Command Groups
### Core Commands

`/ping` — check bot latency

`/echo` — echo back your message

`/pfp` — show a user's profile picture (supports server avatars & custom sizes)

`Greet` (user context menu) — greet a user directly from right-click

### Fun Commands (`/fun ...`)

Grouped under the `/fun` command namespace for entertainment and randomness.

`/fun cat` — random cat from Reddit with a CATAAS fallback

`/fun dog` — random dog from Random.Dog

`/fun meme` — meme from Reddit (r/memes, r/dankmemes, etc.)

`/fun 8ball` — ask the magic 8-ball a question (1/200 chance of a special response)

`/fun roll` — roll dice (supports custom dice count, sides, and modifiers)

### Utility Commands (`/util ...`)

Grouped under the `/util` command namespace for server info, reminders, and productivity.

`/util userinfo` — view information about a user (roles, join date, account age)

`/util serverinfo` — view server statistics and creation info

`/util remindme` — set a reminder with custom delay and optional DM delivery

`/util poll` — create a quick reaction-based poll with up to 5 options

`/util stats` — check bot uptime, latency, and server count

`/util define` — fetch English word definitions via dictionaryapi.dev

## Modular Structure
```bash
disnake-bot/
├─ bot.py
├─ cogs/
│  ├─ fun.py        # /fun commands
│  ├─ util.py       # /util commands
│  └─ context.py    # context menu commands (e.g., Greet)
└─ utils/
   ├─ autoupdate.py # Autoupdate helper
   ├─ http.py       # HTTP helper for safe requests
   └─ reddit.py     # Reddit image fetcher logic
```

Each cog is self-contained, so adding new commands or categories is straightforward.

## Setup

1. **Python 3.10+** required.
2. Create a bot in the [Discord Developer Portal](https://discord.com/developers/applications).
    - Invite it with scopes `bot` and `applications.commands`.
    - Enable only the intents you actually use.
3. Clone this repository and install dependencies:
```bash
python -m venv .venv
. .venv/Scripts/activate      # or source .venv/bin/activate (Linux/macOS)
pip install -r requirements.txt
```
4. Create a .env file and add your bot token:
```bash
DISCORD_TOKEN=your_token_here
```
5. Run the bot:
```bash
python bot.py
```
## Development Tips

- Add `guild_ids=[YOUR_GUILD_ID]` to command decorators for instant visibility while testing.
- Remove it for **global sync** when deploying (Discord may take up to an hour).
- Use `Ctrl+R` in Discord to hard reload if commands don’t appear after sync.
- To add new command categories, just create a new cog in `/cogs/` and load it in `bot.py`.
