import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

initial_extensions = ['cogs.dashboard', 'cogs.moderation', 'cogs.utilities', 'cogs.community', 'cogs.automod']

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
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
