# SerpentCore

![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)
![Python 3.13](https://img.shields.io/badge/python%203.13-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)

SerpentCore is a small, modular Discord bot built with **disnake**. It uses slash commands, context menus, and organized command groups for clean structure and easy maintenance. Designed to run beautifully on a Raspberry Pi.

## Command Groups 

### Fun (`/fun ...`)

`/fun cat` — random cat from Reddit with a CATAAS fallback  
`/fun dog` — random dog from Random.Dog  
`/fun meme` — random meme (r/memes, r/dankmemes, etc.)  
`/fun 8ball` — magic 8-ball (1/200 chance of a rare rude response)  
`/fun roll` — dice roller (custom dice count, sides, and modifiers)  

### Utility (`/util ...`)

`/util userinfo` — view user roles, join date, account age  
`/util serverinfo` — view server creation info and statistics  
`/util remindme` — lightweight reminder system  
`/util poll` — reaction-based polls (up to 5 options)  
`/util stats` — bot uptime, latency, and server count  
`/util define` — fetch definitions via dictionaryapi.dev  

### Moderation Commands

`/purge` — bulk delete messages  
`/slowmode` — set channel slowmode  
`/say` — send a message as the bot  
`/kick` — remove a user  
`/ban` — ban a user + delete message history (optional)  
`/warn` — issue a stored warning  
`/warnings` — view all warnings for a user  
`/clearwarnings` — wipe warnings  
`/timeout` — apply a timeout  
`/untimeout` — remove a timeout  
`/modlog set|disable|show` — configure mod logging channel  

---

## Project Structure

```bash
SerpentCore/
├─ bot.py
├─ cogs/
│  ├─ fun.py        # /fun commands
│  ├─ util.py       # /util commands
│  ├─ moderation.py # moderation commands
│  ├─ info.py       # helpful commands
│  └─ context.py    # context menu commands
└─ utils/
   ├─ autoupdate.py # Git auto-updater
   ├─ http.py       # HTTP request helper
   └─ reddit.py     # Reddit media fetcher
```
Setup
1. Python 3.10+
2. Create a bot in the Developer Portal
- Enable only the intents you need
- Invite with scopes: bot and applications.commands
3. Clone & install:
```
python -m venv .venv
. .venv/Scripts/activate     # Windows
source .venv/bin/activate    # Linux/macOS
pip install -r requirements.txt
```
4. Place your bot token in .env:
```
DISCORD_TOKEN=your_token_here
```

5. Run:
```
python bot.py
```
## Development Tips
- Add `guild_ids=[YOUR_ID]` to slash commands for instant sync during testing
- Hit `Ctrl+R` in Discord for a hard UI reload if commands don’t appear
- New cogs can be dropped into `/cogs/` and added to `initial_extensions`
