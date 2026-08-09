import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- PARTIE SERVEUR WEB (Aiohttp, beaucoup plus propre pour Render) ---
async def handle_web(request):
    return web.Response(text="Le bot est en ligne et tourne parfaitement !")

app_web = web.Application()
app_web.router.add_get('/', handle_web)

async def start_web_server():
    port = int(os.environ.get('PORT', 5000))
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Serveur web démarré sur le port {port}")
# ---------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} est connecté !")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching, name="la communauté")
    )

initial_extensions = ['cogs.welcome', 'cogs.utility', 'cogs.moderation']

async def main():
    # 1. On lance le petit serveur web pour Render
    await start_web_server()
    
    # 2. On charge les modules du bot
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"✅ Module chargé: {extension}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {extension}: {e}")

    # 3. On lance le bot Discord
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
