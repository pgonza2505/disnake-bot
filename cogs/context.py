import disnake
from disnake.ext import commands

class ContextMenus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.user_command(name="Greet")
    async def greet_user(self, inter: disnake.UserCommandInteraction, user: disnake.User):
        await inter.response.send_message(f"Hey {user.mention}!")

def setup(bot):
    bot.add_cog(ContextMenus(bot))