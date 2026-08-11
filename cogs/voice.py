import discord
from discord.ext import commands
from discord import app_commands

# --- LA FENÊTRE DE CONFIGURATION (MODAL) ---
class VoiceConfigModal(discord.ui.Modal, title='🛠️ Configuration de ton salon vocal'):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    name = discord.ui.TextInput(
        label='Nom du salon',
        placeholder='Ex: Chill avec les gars 🎮',
        required=True,
        max_length=50
    )
    limit = discord.ui.TextInput(
        label='Limite de membres (0 = illimité)',
        placeholder='Ex: 5',
        required=False,
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Vérifie si l'utilisateur est bien dans un vocal
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ Tu dois être connecté à un salon vocal pour créer ton propre salon !", ephemeral=True)

        # Récupération des valeurs
        channel_name = self.name.value
        try:
            user_limit = int(self.limit.value) if self.limit.value else 0
            if user_limit < 0 or user_limit > 99: user_limit = 0
        except:
            user_limit = 0

        # Création du salon
        category = interaction.user.voice.channel.category
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True),
            interaction.user: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True, move_members=True, mute_members=True, deafen_members=True)
        }
        
        new_channel = await interaction.guild.create_voice_channel(
            name=channel_name,
            category=category,
            user_limit=user_limit,
            overwrites=overwrites
        )
        
        # Déplacement du membre
        try:
            await interaction.user.move_to(new_channel)
        except:
            pass

        # Enregistrement dans la mémoire du bot
        cog = self.bot.get_cog('TempVoice')
        if cog:
            cog.temp_channels.append(new_channel.id)

        await interaction.response.send_message(f"✅ Ton salon vocal **{channel_name}** a été créé ! Tu es maintenant le chef de ce salon.", ephemeral=True)

# --- LA VUE AVEC LE BOUTON ---
class VoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Créer mon salon vocal", style=discord.ButtonStyle.success, emoji="🔊", custom_id="create_voice_btn")
    async def create_voice(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.client.get_cog('TempVoice'):
            return await interaction.response.send_message("Le système vocal n'est pas prêt.", ephemeral=True)
        
        await interaction.response.send_modal(VoiceConfigModal(interaction.client))

# --- LE COG ---
class TempVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = []
        bot.add_view(VoiceView())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Si l'utilisateur quitte un salon, et que ce salon est un salon temporaire
        if before.channel and before.channel.id in self.temp_channels:
            # Si le salon est vide, on le supprime
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    self.temp_channels.remove(before.channel.id)
                except:
                    pass

    @app_commands.command(name="voice-setup", description="Créer le panneau pour générer des salons vocaux personnalisés.")
    @app_commands.default_permissions(administrator=True)
    async def voice_setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔊 Salons Vocaux Personnalisés",
            description="Clique sur le bouton ci-dessous pour créer ton propre salon vocal !\n\nTu pourras le configurer (nom et limite de personnes) et tu en seras le propriétaire. Il sera supprimé automatiquement quand tout le monde le quittera.",
            color=discord.Color.blurple()
        )
        await interaction.channel.send(embed=embed, view=VoiceView())
        await interaction.response.send_message("✅ Panneau vocal créé !", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TempVoice(bot))
