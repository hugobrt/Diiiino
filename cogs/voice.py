import discord
from discord.ext import commands
from discord import app_commands

# --- MODAL POUR RENOMMER ---
class VoiceRenameModal(discord.ui.Modal, title='📝 Renommer le salon vocal'):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    name = discord.ui.TextInput(
        label='Nouveau nom du salon',
        placeholder='Ex: Chill Gaming 🎮',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.channel.edit(name=self.name.value)
        await interaction.response.send_message(f"✅ Salon renommé en **{self.name.value}** !", ephemeral=True)

# --- PANNEAU DE CONTRÔLE ---
class VoiceControlView(discord.ui.View):
    def __init__(self, owner_id, channel):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.channel = channel

    # Sécurité : seul le créateur du salon peut utiliser ces boutons
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Tu n'es pas le propriétaire de ce salon !", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Verrouiller", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="vc_lock", row=0)
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = self.channel.overwrites_for(interaction.guild.default_role)
        overwrites.connect = False
        await self.channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        await interaction.response.send_message("🔒 Salon verrouillé ! Plus personne ne peut rejoindre.", ephemeral=True)

    @discord.ui.button(label="Déverrouiller", style=discord.ButtonStyle.success, emoji="🔓", custom_id="vc_unlock", row=0)
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = self.channel.overwrites_for(interaction.guild.default_role)
        overwrites.connect = True
        await self.channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        await interaction.response.send_message("🔓 Salon déverrouillé ! Les gens peuvent rejoindre.", ephemeral=True)

    @discord.ui.button(label="Cacher", style=discord.ButtonStyle.secondary, emoji="👁️", custom_id="vc_hide", row=0)
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = self.channel.overwrites_for(interaction.guild.default_role)
        overwrites.view_channel = False
        await self.channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        await interaction.response.send_message("👁️ Salon caché ! Il est maintenant invisible pour les autres.", ephemeral=True)

    @discord.ui.button(label="Afficher", style=discord.ButtonStyle.primary, emoji="👀", custom_id="vc_show", row=0)
    async def show(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = self.channel.overwrites_for(interaction.guild.default_role)
        overwrites.view_channel = True
        await self.channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
        await interaction.response.send_message("👀 Salon affiché ! Tout le monde le voit.", ephemeral=True)

    @discord.ui.button(label="Renommer", style=discord.ButtonStyle.secondary, emoji="📝", custom_id="vc_rename", row=1)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VoiceRenameModal(self.channel))

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="vc_delete", row=1)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.channel.delete()
        await interaction.response.send_message("🗑️ Salon supprimé !", ephemeral=True)

# --- FENÊTRE DE CRÉATION ---
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
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ Tu dois être connecté à un salon vocal pour créer ton propre salon !", ephemeral=True)

        channel_name = self.name.value
        try:
            user_limit = int(self.limit.value) if self.limit.value else 0
            if user_limit < 0 or user_limit > 99: user_limit = 0
        except:
            user_limit = 0

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
        
        try:
            await interaction.user.move_to(new_channel)
        except:
            pass

        cog = self.bot.get_cog('TempVoice')
        if cog:
            cog.temp_channels[new_channel.id] = interaction.user.id

        # 1. On répond juste "OK" pour fermer la fenêtre de configuration (invisible)
        await interaction.response.send_message(f"✅ Ton salon **{channel_name}** a été créé ! Regarde le chat du vocal pour le contrôler.", ephemeral=True)

        # 2. ON ENVOIE LE VRAI MESSAGE DANS LE CHAT TEXTUEL DU SALON VOCAL
        embed = discord.Embed(
            title="🛠️ Panneau de Contrôle Vocal",
            description=f"Bienvenue {interaction.user.mention} dans ton salon **{channel_name}** !\n\nUtilise les boutons ci-dessous pour gérer ton salon en temps réel.",
            color=discord.Color.green()
        )
        # On envoie dans new_channel (le chat texte du vocal)
        await new_channel.send(embed=embed, view=VoiceControlView(interaction.user.id, new_channel))

# --- BOUTON DU PANNEAU D'ACCUEIL ---
class VoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Créer mon salon vocal", style=discord.ButtonStyle.success, emoji="🔊", custom_id="create_voice_btn")
    async def create_voice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VoiceConfigModal(interaction.client))

# --- LE COG ---
class TempVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = {} # Dictionnaire {channel_id: owner_id}
        bot.add_view(VoiceView())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel and before.channel.id in self.temp_channels:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    del self.temp_channels[before.channel.id]
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
