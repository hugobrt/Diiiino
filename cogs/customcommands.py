import discord
from discord.ext import commands
import json
import os

def load_custom_commands():
    if os.path.exists('commands.json'):
        try:
            with open('commands.json', 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {} # Si le fichier est vide ou cassé, on retourne un dictionnaire vide
    return {}

def save_custom_commands(data):
    with open('commands.json', 'w') as f:
        json.dump(data, f, indent=4)

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if message.content.startswith('!'):
            cmd_name = message.content[1:].split(' ')[0].lower()
            
            commands_data = load_custom_commands()
            guild_id = str(message.guild.id)
            
            if guild_id in commands_data and cmd_name in commands_data[guild_id]:
                cmd_data = commands_data[guild_id][cmd_name]
                
                try:
                    color = int(cmd_data.get('color', '#5865F2').replace("#", ""), 16)
                except:
                    color = 0x5865F2
                    
                embed = discord.Embed(
                    title=cmd_data.get('title', ''),
                    description=cmd_data.get('description', ''),
                    color=color
                )
                await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))
