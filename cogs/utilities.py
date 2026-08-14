import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sniped_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        self.sniped_messages[message.channel.id] = message

    @app_commands.command(name="ping", description="Vérifie la latence.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 Pong ! Latence: **{round(self.bot.latency * 1000)}ms**.", ephemeral=True)

    @app_commands.command(name="serverinfo", description="Infos sur le serveur.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"Infos sur {guild.name}", color=discord.Color.green())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
        embed.add_field(name="👑 Propriétaire", value=guild.owner.mention, inline=True)
        embed.add_field(name="👥 Membres", value=guild.member_count, inline=True)
        embed.add_field(name="💬 Salons", value=len(guild.text_channels), inline=True)
        embed.add_field(name="🔊 Vocaux", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="📅 Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="userinfo", description="Infos d'un membre.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"Infos sur {member.name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 ID", value=member.id, inline=False)
        embed.add_field(name="📅 Compte créé le", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="📥 A rejoint le", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
        roles = [r.mention for r in member.roles if r != interaction.guild.default_role]
        embed.add_field(name=f"🎭 Rôles ({len(roles)})", value=" ".join(roles) if roles else "Aucun", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="avatar", description="Afficher la photo de profil.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar de {member.name}", color=discord.Color.blue())
        embed.set_image(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="snipe", description="Voir le dernier message supprimé.")
    async def snipe(self, interaction: discord.Interaction):
        message = self.sniped_messages.get(interaction.channel.id)
        if not message: return await interaction.response.send_message("❌ Rien à sniper.", ephemeral=True)
        embed = discord.Embed(description=message.content, color=discord.Color.orange(), timestamp=message.created_at)
        embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="dino", description="Appelle le dinosaure !")
    async def dino(self, interaction: discord.Interaction):
        await interaction.response.send_message("rawrrrrr 🦖")

    @app_commands.command(name="rappel", description="Te rappelle de faire quelque chose.")
    @app_commands.describe(minutes="Dans combien de minutes", chose="De quoi te rappeler ?")
    async def rappel(self, interaction: discord.Interaction, minutes: int, chose: str):
        await interaction.response.send_message(f"⏰ C'est noté {interaction.user.mention} ! Je te rappellerai de '{chose}' dans **{minutes} minutes**.")
        await asyncio.sleep(minutes * 60)
        await interaction.channel.send(f"⏰ {interaction.user.mention} ! Il est l'heure de : **{chose}** !")

    @app_commands.command(name="say", description="Faire parler le bot (Admin).")
    @app_commands.describe(message="Le message que le bot doit envoyer")
    @app_commands.default_permissions(administrator=True)
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.channel.send(message)
        await interaction.response.send_message("✅ Message envoyé !", ephemeral=True)

    @app_commands.command(name="status", description="Changer le statut d'activité du bot (Admin).")
    @app_commands.describe(type="Le type d'activité", texte="Le texte de l'activité")
    @app_commands.choices(type=[
        app_commands.Choice(name="Joue à", value="playing"),
        app_commands.Choice(name="Regarde", value="watching"),
        app_commands.Choice(name="Écoute", value="listening"),
        app_commands.Choice(name="Participe à", value="competing")
    ])
    @app_commands.default_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction, type: app_commands.Choice[str], texte: str):
        activity_type = getattr(discord.ActivityType, type.value)
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=activity_type, name=texte))
        await interaction.response.send_message(f"✅ Statut mis à jour : **{type.name} {texte}**", ephemeral=True)

    @app_commands.command(name="embed", description="Créer un message sur-mesure ultime (Admin).")
    @app_commands.describe(titre="Titre", description="Texte du message", couleur="Code hex (ex: #FF0000)", image="URL de l'image (optionnel)", miniature="URL de la miniature (optionnel)", footer="Pied de page (optionnel)")
    @app_commands.default_permissions(administrator=True)
    async def embed(self, interaction: discord.Interaction, titre: str, description: str, couleur: str = "#5865F2", image: str = None, miniature: str = None, footer: str = None):
        try:
            color = int(couleur.replace("#", ""), 16)
        except ValueError:
            color = 0x5865F2
            
        embed = discord.Embed(title=titre, description=description, color=color)
        if image: embed.set_image(url=image)
        if miniature: embed.set_thumbnail(url=miniature)
        if footer: embed.set_footer(text=footer)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Ton embed a été envoyé !", ephemeral=True)

    # ==========================================
    #         COMMANDE DE PRISE EN CHARGE TICKET
    # ==========================================
    @app_commands.command(name="hld", description="Prise en charge ticket")
    @app_commands.default_permissions(administrator=True)
    async def handled(self, interaction: discord.Interaction):
        # 1er message
        await interaction.channel.send(f"**Ticket handled by:** {interaction.user.mention}")
        # 2ème message
        await interaction.channel.send("**Demande traité sous 24h maximum**")

async def setup(bot):
    await bot.add_cog(Utilities(bot))
