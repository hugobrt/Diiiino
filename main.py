import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from aiohttp import web
import asyncio
import datetime
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- SERVEUR WEB INVISIBLE POUR RENDER ---
async def handle_web(request):
    return web.Response(text="Le bot est en ligne !")
app_web = web.Application()
app_web.router.add_get('/', handle_web)
async def start_web_server():
    port = int(os.environ.get('PORT', 5000))
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Serveur web démarré sur le port {port}")
# -----------------------------------------

# --- STOCKAGES EN MÉMOIRE ---
sniped_messages = {}
warnings_data = {}
giveaway_participants = {}

# ==========================================
#         VUES INTERACTIVES (Boutons)
# ==========================================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ouvrir un Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Vérifie si l'utilisateur a déjà un ticket
        existing = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"❌ Tu as déjà un ticket ouvert ici : {existing.mention}", ephemeral=True)
            return

        # Crée le salon
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        # Ajoute les perms pour les admins (à adapter si tu as un rôle "Staff" spécifique)
        for role in interaction.guild.roles:
            if role.permissions.manage_guild:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ticket_channel = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(title="🎫 Ticket Ouvert", description=f"Bienvenue {interaction.user.mention} !\nUn membre du staff arrive vite. Explique ton problème en attendant.", color=discord.Color.blue())
        await ticket_channel.send(embed=embed, view=CloseTicketView())

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer le Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Fermeture du ticket dans 5 secondes...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class RoleButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Notifications", style=discord.ButtonStyle.success, emoji="🔔", custom_id="role_notif")
    async def role_notif(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Ici on cherche un rôle nommé "Notifications". Crée ce rôle sur ton serveur !
        role = discord.utils.get(interaction.guild.roles, name="Notifications")
        if not role:
            await interaction.response.send_message("❌ Le rôle 'Notifications' n'existe pas sur le serveur.", ephemeral=True)
            return
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ Tu as retiré le rôle {role.name}.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Tu as reçu le rôle {role.name} !", ephemeral=True)

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="Participer", style=discord.ButtonStyle.primary, emoji="🎉", custom_id="giveaway_join")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in giveaway_participants.get(self.giveaway_id, []):
            giveaway_participants[self.giveaway_id].append(interaction.user.id)
            await interaction.response.send_message("✅ Tu participes au giveaway ! Bonne chance.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Tu participes déjà !", ephemeral=True)

# ==========================================
#         ÉVÉNEMENTS DE BASE
# ==========================================
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    sniped_messages[message.channel.id] = message

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} est connecté !")
    # Enregistrement des vues persistantes (pour que les boutons marchent même après un redémarrage)
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(RoleButtonView())
    
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} commande(s) slash synchronisée(s) !")
    except Exception as e:
        print(f"❌ Erreur de sync: {e}")
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="la communauté"))

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="général")
    if channel:
        embed = discord.Embed(title=f"Bienvenue {member.name} ! 🎉", description=f"Heureux de t'accueillir sur **{member.guild.name}** ! Tu es le {member.guild.member_count}ème membre.", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="général")
    if channel:
        embed = discord.Embed(title=f"Au revoir {member.name} 👋", description=f"**{member.name}** a quitté le serveur. On est maintenant {member.guild.member_count} membres.", color=discord.Color.red())
        await channel.send(embed=embed)

# ==========================================
#         COMMANDES DE MODÉRATION
# ==========================================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    msg = "❌ Tu n'as pas la permission ou une erreur est survenue."
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="kick", description="Expulser un membre.")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
    if member.top_role >= interaction.user.top_role: return await interaction.response.send_message("❌ Rôle trop haut.", ephemeral=True)
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member.mention} expulsé. Raison : {reason}", ephemeral=True)

@bot.tree.command(name="ban", description="Bannir un membre.")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
    if member.top_role >= interaction.user.top_role: return await interaction.response.send_message("❌ Rôle trop haut.", ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member.mention} banni. Raison : {reason}", ephemeral=True)

@bot.tree.command(name="mute", description="Mettre en isolement (Timeout).")
@app_commands.default_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Aucune raison"):
    await member.timeout(datetime.timedelta(minutes=minutes), reason=reason)
    await interaction.response.send_message(f"🔇 {member.mention} mute {minutes} min.", ephemeral=True)

@bot.tree.command(name="clear", description="Supprimer des messages.")
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 {len(deleted)} messages supprimés.", ephemeral=True)

@bot.tree.command(name="warn", description="Donner un avertissement à un membre.")
@app_commands.default_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if member.id not in warnings_data: warnings_data[member.id] = []
    warnings_data[member.id].append(reason)
    await interaction.response.send_message(f"⚠️ {member.mention} a reçu un avertissement. Total: {len(warnings_data[member.id])}.", ephemeral=True)

@bot.tree.command(name="warnings", description="Voir les avertissements d'un membre.")
@app_commands.default_permissions(moderate_members=True)
async def warnings(interaction: discord.Interaction, member: discord.Member):
    warns = warnings_data.get(member.id, [])
    if not warns: return await interaction.response.send_message(f"✅ {member.name} n'a aucun avertissement.", ephemeral=True)
    embed = discord.Embed(title=f"Avertissements de {member.name}", color=discord.Color.orange())
    for i, r in enumerate(warns, 1): embed.add_field(name=f"Warn {i}", value=r, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="lock", description="Verrouiller le salon actuel.")
@app_commands.default_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔒 Salon verrouillé.", ephemeral=True)

@bot.tree.command(name="unlock", description="Déverrouiller le salon actuel.")
@app_commands.default_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔓 Salon déverrouillé.", ephemeral=True)

@bot.tree.command(name="slowmode", description="Régler le slowmode du salon.")
@app_commands.describe(seconds="Nombre de secondes (0 pour désactiver)")
@app_commands.default_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"⏱️ Slowmode réglé sur {seconds} secondes.", ephemeral=True)

# ==========================================
#         COMMANDES INTERACTIVES (Panneaux)
# ==========================================
@bot.tree.command(name="ticket-setup", description="Créer le panneau des tickets.")
@app_commands.default_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 Support - Tickets", description="Besoin d'aide ? Un problème ?\nClique sur le bouton ci-dessous pour ouvrir un salon privé avec le staff.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Panneau des tickets créé !", ephemeral=True)

@bot.tree.command(name="role-setup", description="Créer le panneau des rôles.")
@app_commands.default_permissions(administrator=True)
async def role_setup(interaction: discord.Interaction):
    embed = discord.Embed(title="🎨 Rôles auto-attribuables", description="Choisis tes rôles en cliquant sur les boutons !", color=discord.Color.purple())
    embed.add_field(name="🔔 Notifications", value="Pour être prévenu des annonces et events importants.")
    await interaction.channel.send(embed=embed, view=RoleButtonView())
    await interaction.response.send_message("✅ Panneau des rôles créé !", ephemeral=True)

# ==========================================
#         COMMANDES UTILITAIRES & FUN
# ==========================================
@bot.tree.command(name="giveaway", description="Lancer un giveaway (Concours) !")
@app_commands.describe(duration_minutes="Durée en minutes", prize="Le lot à gagner")
@app_commands.default_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, duration_minutes: int, prize: str):
    g_id = random.randint(1000, 9999)
    giveaway_participants[g_id] = []
    
    embed = discord.Embed(title="🎉 GIVEAWAY !", description=f"**Lot :** {prize}\n**Fin dans :** {duration_minutes} minutes\n\nClique sur le bouton pour participer !", color=discord.Color.gold())
    embed.set_footer(text=f"ID: {g_id}")
    await interaction.response.send_message(embed=embed, view=GiveawayView(g_id))
    msg = await interaction.original_response()
    
    # Attendre la fin du giveaway
    await asyncio.sleep(duration_minutes * 60)
    
    if not giveaway_participants[g_id]:
        await msg.edit(content="🎉 Le giveaway est terminé ! Malheureusement, il n'y a pas eu de participants.", embed=None, view=None)
        return

    winner_id = random.choice(giveaway_participants[g_id])
    winner = interaction.guild.get_member(winner_id)
    
    await msg.edit(content=f"🎉 Le giveaway est terminé !\nFélicitations à {winner.mention} qui remporte **{prize}** !", embed=None, view=None)

@bot.tree.command(name="ping", description="Vérifie la latence.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong ! Latence: **{round(bot.latency * 1000)}ms**.", ephemeral=True)

@bot.tree.command(name="userinfo", description="Infos d'un membre.")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"Infos sur {member.name}", color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=False)
    embed.add_field(name="📅 Compte créé le", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="📥 A rejoint le", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
    roles = [r.mention for r in member.roles if r != interaction.guild.default_role]
    embed.add_field(name=f"🎭 Rôles ({len(roles)})", value=" ".join(roles) if roles else "Aucun", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="snipe", description="Voir le dernier message supprimé.")
async def snipe(interaction: discord.Interaction):
    message = sniped_messages.get(interaction.channel.id)
    if not message: return await interaction.response.send_message("❌ Rien à sniper.", ephemeral=True)
    embed = discord.Embed(description=message.content, color=discord.Color.orange(), timestamp=message.created_at)
    embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="dino", description="Appelle le dinosaure !")
async def dino(interaction: discord.Interaction):
    await interaction.response.send_message("rawrrrrr 🦖")

@bot.tree.command(name="sondage", description="Créer un sondage.")
async def sondage(interaction: discord.Interaction, question: str):
    embed = discord.Embed(title="📊 Sondage", description=question, color=discord.Color.gold())
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

@bot.tree.command(name="annonce", description="Faire une annonce officielle.")
@app_commands.default_permissions(administrator=True)
async def annonce(interaction: discord.Interaction, titre: str, message: str):
    embed = discord.Embed(title=f"📢 {titre}", description=message, color=discord.Color.red())
    embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else "")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="reglement", description="Afficher le règlement.")
@app_commands.default_permissions(administrator=True)
async def reglement(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 Règlement de la Communauté", description="Voici les règles à respecter !", color=discord.Color.dark_blue())
    embed.add_field(name="1. Respect mutuel", value="Aucun comportement toxique ou insulte n'est toléré.", inline=False)
    embed.add_field(name="2. Pas de spam", value="Le spam est interdit.", inline=False)
    embed.add_field(name="3. Publicité", value="La pub pour d'autres serveurs est interdite.", inline=False)
    embed.set_footer(text="Clique sur le bouton pour accepter.")
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="J'accepte le règlement", style=discord.ButtonStyle.success, emoji="✅"))
    await interaction.response.send_message(embed=embed, view=view)

# ==========================================
#         LANCEMENT DU BOT
# ==========================================
async def main():
    await start_web_server()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
