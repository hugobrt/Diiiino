import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# On active les intents (permissions)
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
    # On synchronise les commandes slash sur Discord
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} commande(s) slash synchronisée(s) avec succès !")
    except Exception as e:
        print(f"❌ Erreur de synchronisation: {e}")
        
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="gérer la communauté"))

# --- COMMANDES SLASH ---
@bot.tree.command(name="ping", description="Vérifie si le bot est en ligne et sa latence.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong ! La latence est de **{latency}ms**.")

@bot.tree.command(name="serverinfo", description="Affiche les informations du serveur.")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"Infos sur {guild.name}", color=discord.Color.green())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
    embed.add_field(name="👑 Propriétaire", value=guild.owner.mention, inline=True)
    embed.add_field(name="👥 Membres", value=guild.member_count, inline=True)
    embed.add_field(name="📅 Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    await interaction.response.send_message(embed=embed)
# ----------------------

async def main():
    await start_web_server()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
