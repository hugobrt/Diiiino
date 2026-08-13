import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

# Gestion du fichier de sauvegarde
def load_afk():
    if os.path.exists('afk.json'):
        with open('afk.json', 'r') as f:
            return json.load(f)
    return {}

def save_afk(data):
    with open('afk.json', 'w') as f:
        json.dump(data, f, indent=4)

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = load_afk()

    @app_commands.command(name="afk", description="Te met en mode AFK (Absent).")
    @app_commands.describe(reason="La raison de ton absence")
    async def afk(self, interaction: discord.Interaction, reason: str = "Aucune raison"):
        user_id = str(interaction.user.id)
        
        # Sauvegarde de l'utilisateur AFK
        self.afk_users[user_id] = reason
        save_afk(self.afk_users)
        
        # Ajout du [AFK] devant le pseudo
        try:
            if not interaction.user.display_name.startswith("[AFK]"):
                await interaction.user.edit(nick=f"[AFK] {interaction.user.display_name}")
        except:
            pass # Ignore si le bot n'a pas la permission de changer le pseudo
            
        embed = discord.Embed(
            title="💤 Mode AFK Activé",
            description=f"Tu es maintenant AFK.\n**Raison :** {reason}\n\nJe préviendrai ceux qui te mentionnent. Tu seras de retour dès que tu taperas un message !",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore les bots et les messages privés
        if message.author.bot or not message.guild:
            return

        author_id = str(message.author.id)
        
        # 1. Vérifie si l'auteur du message était AFK (pour le faire revenir)
        if author_id in self.afk_users:
            del self.afk_users[author_id]
            save_afk(self.afk_users)
            
            # Retire le [AFK] du pseudo
            try:
                if message.author.nick and message.author.nick.startswith("[AFK] "):
                    new_nick = message.author.nick.replace("[AFK] ", "")
                    await message.author.edit(nick=new_nick)
            except:
                pass
            
            # Envoie un message temporaire pour confirmer le retour
            msg = await message.channel.send(f"Bon retour {message.author.mention} ! Ton mode AFK a été désactivé. ✅")
            await asyncio.sleep(5)
            await msg.delete()

        # 2. Vérifie si le message mentionne quelqu'un qui est AFK
        if message.mentions:
            for mentioned_user in message.mentions:
                if mentioned_user.bot: continue
                mentioned_id = str(mentioned_user.id)
                if mentioned_id in self.afk_users:
                    reason = self.afk_users[mentioned_id]
                    embed = discord.Embed(
                        title=f"💤 {mentioned_user.display_name} est AFK",
                        description=f"**Raison :** {reason}",
                        color=discord.Color.orange()
                    )
                    await message.reply(embed=embed, delete_after=10) # Le message s'efface tout seul après 10s

async def setup(bot):
    await bot.add_cog(AFK(bot))
