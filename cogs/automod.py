import discord
from discord.ext import commands

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if "discord.gg/" in message.content.lower() or "discord.com/invite/" in message.content.lower():
            if not message.author.guild_permissions.manage_messages:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, la publicité pour les serveurs Discord est interdite !", delete_after=5)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
