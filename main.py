import os
import sys
# Force Render à afficher les logs en temps réel
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# On crée l'application web globalement
bot.web_app = web.Application()

# Liste de tous les modules du bot
initial_extensions = ['cogs.dashboard', 'cogs.moderation', 'cogs.utilities', 'cogs.community', 'cogs.automod', 'cogs.voice', 'cogs.afk', 'cogs.customcommands']

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} est connecté !")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} commande(s) slash synchronisée(s) !")
    except Exception as e:
        print(f"❌ Erreur de sync: {e}")
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="la communauté"))

async def main():
    # 1. On charge les modules
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"✅ Module chargé: {extension}")
        except Exception as e:
            print(f"❌ Erreur avec {extension}: {e}")
            
    # 2. On lance le serveur web (Il restera allumé quoi qu'il arrive !)
    runner = web.AppRunner(bot.web_app)
    await runner.setup()
    port = int(os.environ.get('PORT', 5000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Serveur web démarré sur le port {port} (Render est content !)")
    
    # 3. On lance le bot Discord avec un système de reconnexion automatique
    while True:
        try:
            await bot.start(TOKEN)
            break # Si le bot s'éteint normalement, on casse la boucle
        except Exception as e:
            # Si Cloudflare ou Discord bloque la connexion, on affiche l'erreur et on réessaaye
            print(f"❌ Erreur de connexion (Cloudflare/Discord) : {e}")
            print("⏳ Nouvelle tentative dans 20 secondes...")
            await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(main())
