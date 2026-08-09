import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from aiohttp import web
import asyncio
import datetime

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

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} est connecté !")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} commande(s) slash synchronisée(s) !")
    except Exception as e:
        print(f"❌ Erreur de sync: {e}")
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="la communauté"))

# ==========================================
#         ÉVÉNEMENTS COMMUNAUTAIRES
# ==========================================
@bot.event
async def on_member_join(member):
    # Remplace 'général' par le nom exact du salon d'accueil
    channel = discord.utils.get(member.guild.text_channels, name="général")
    if channel:
        embed = discord.Embed(
            title=f"Bienvenue {member.name} ! 🎉",
            description=f"Heureux de t'accueillir sur **{member.guild.name}** ! Tu es le {member.guild.member_count}ème membre. Installe-toi bien !",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="général")
    if channel:
        embed = discord.Embed(
            title=f"Au revoir {member.name} 👋",
            description=f"**{member.name}** a quitté le serveur. On est maintenant {member.guild.member_count} membres.",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)

# ==========================================
#         COMMANDES DE MODÉRATION
# ==========================================
@bot.tree.command(name="kick", description="Expulser un membre du serveur.")
@app_commands.describe(member="Le membre à expulser", reason="La raison de l'expulsion")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Tu ne peux pas expulser quelqu'un qui a un rôle supérieur ou égal au tien.", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member.mention} a été expulsé. Raison : {reason}")

@bot.tree.command(name="ban", description="Bannir un membre du serveur.")
@app_commands.describe(member="Le membre à bannir", reason="La raison du bannissement")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Tu ne peux pas bannir quelqu'un qui a un rôle supérieur ou égal au tien.", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member.mention} a été banni. Raison : {reason}")

@bot.tree.command(name="mute", description="Mettre un membre en isolement (Timeout).")
@app_commands.describe(member="Le membre à mute", minutes="Durée en minutes", reason="La raison")
@app_commands.default_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Aucune raison fournie"):
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"🔇 {member.mention} a été mute pendant **{minutes} minutes**. Raison : {reason}")

@bot.tree.command(name="unmute", description="Retirer l'isolement d'un membre.")
@app_commands.describe(member="Le membre à unmute")
@app_commands.default_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔊 {member.mention} a été unmute et peut de nouveau parler.")

@bot.tree.command(name="clear", description="Supprimer des messages en masse.")
@app_commands.describe(amount="Nombre de messages à supprimer (1-100)")
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Le nombre doit être entre 1 et 100.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 J'ai supprimé **{len(deleted)}** messages !", ephemeral=True)

# ==========================================
#         COMMANDES UTILITAIRES & COMMU
# ==========================================
@bot.tree.command(name="ping", description="Vérifie la latence du bot.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong ! La latence est de **{latency}ms**.")

@bot.tree.command(name="avatar", description="Afficher la photo de profil d'un membre en grand.")
@app_commands.describe(member="De qui veux-tu voir l'avatar ?")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"🖼️ Avatar de {member.name}", color=discord.Color.blue())
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sondage", description="Créer un sondage pour la communauté.")
@app_commands.describe(question="La question de ton sondage")
async def sondage(interaction: discord.Interaction, question: str):
    embed = discord.Embed(
        title="📊 Sondage Communautaire",
        description=question,
        color=discord.Color.gold()
    )
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text="Réagissez ci-dessous pour voter !")
    
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    await message.add_reaction("✅")
    await message.add_reaction("❌")

# ==========================================
#         LANCEMENT DU BOT
# ==========================================
async def main():
    await start_web_server()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
