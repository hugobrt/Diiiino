import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {} 

    group = app_commands.Group(name="mod", description="Commandes de modération", default_permissions=discord.Permissions(moderate_members=True))

    @group.command(name="kick", description="Expulser un membre.")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Rôle trop haut.", ephemeral=True)
        await member.kick(reason=reason)
        await interaction.response.send_message(f"👢 {member.mention} expulsé. Raison : {reason}", ephemeral=True)

    @group.command(name="ban", description="Bannir un membre.")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Rôle trop haut.", ephemeral=True)
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 {member.mention} banni. Raison : {reason}", ephemeral=True)

    @group.command(name="mute", description="Mettre en isolement.")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Aucune raison"):
        await member.timeout(datetime.timedelta(minutes=minutes), reason=reason)
        await interaction.response.send_message(f"🔇 {member.mention} mute {minutes} min. Raison : {reason}", ephemeral=True)

    @group.command(name="clear", description="Supprimer des messages.")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 {len(deleted)} messages supprimés.", ephemeral=True)

    @group.command(name="warn", description="Avertir un membre (à la volée).")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if member.id not in self.warnings:
            self.warnings[member.id] = []
        self.warnings[member.id].append(reason)
        await interaction.response.send_message(f"⚠️ {member.mention} averti. Total: {len(self.warnings[member.id])}.", ephemeral=True)

    @group.command(name="warnings", description="Voir les avertissements.")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        warns = self.warnings.get(member.id, [])
        if not warns:
            return await interaction.response.send_message(f"✅ {member.name} est clean.", ephemeral=True)
        embed = discord.Embed(title=f"Warns de {member.name}", color=discord.Color.orange())
        for i, r in enumerate(warns, 1):
            embed.add_field(name=f"Warn {i}", value=r, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @group.command(name="lock", description="Verrouiller le salon.")
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔒 Salon verrouillé.", ephemeral=True)

    @group.command(name="unlock", description="Déverrouiller le salon.")
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 Salon déverrouillé.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
