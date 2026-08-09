import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="général")
        if channel:
            embed = discord.Embed(
                title=f"Bienvenue {member.name} ! 🎉",
                description=f"Heureux de t'accueillir sur **{member.guild.name}** ! Tu es le {member.guild.member_count}ème membre.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
