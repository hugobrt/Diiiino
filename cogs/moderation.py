import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="Aucune raison fournie"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} a été expulsé. Raison : {reason}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="Aucune raison fournie"):
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member.mention} a été banni. Raison : {reason}")

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 J'ai supprimé **{amount}** messages !", delete_after=5)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande !")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Il manque des arguments ! Exemple: `!kick @user raison`")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
