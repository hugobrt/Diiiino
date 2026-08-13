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

bot.web_app = web.Application()

# ON AJOUTE cogs.customcommands ICI !
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
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"✅ Module chargé: {extension}")
        except Exception as e:
            print(f"❌ Erreur avec {extension}: {e}")
            
    runner = web.AppRunner(bot.web_app)
    await runner.setup()
    port = int(os.environ.get('PORT', 5000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Serveur web démarré sur le port {port} (Render est content !)")
    
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
