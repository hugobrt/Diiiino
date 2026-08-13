import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import json
import os

# Fonction pour lire la configuration
def get_welcome_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            return json.load(f)
    return {}

class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Ouvrir un Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        existing = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing: return await interaction.response.send_message(f"❌ Tu as déjà un ticket : {existing.mention}", ephemeral=True)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for role in interaction.guild.roles:
            if role.permissions.manage_guild: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        ticket_channel = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {ticket_channel.mention}", ephemeral=True)
        embed = discord.Embed(title="🎫 Ticket Ouvert", description=f"Bienvenue {interaction.user.mention} ! Un membre du staff arrive vite.", color=discord.Color.blue())
        await ticket_channel.send(embed=embed, view=CloseTicketView())

class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Fermer le Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Fermeture du ticket dans 5 secondes...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.participants = []
    @discord.ui.button(label="Participer", style=discord.ButtonStyle.primary, emoji="🎉", custom_id="giveaway_join")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.participants:
            self.participants.append(interaction.user.id)
            await interaction.response.send_message("✅ Tu participes ! Bonne chance.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Tu participes déjà !", ephemeral=True)

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'events_data'): bot.events_data = {}
        bot.add_view(TicketView())
        bot.add_view(CloseTicketView())
        bot.add_view(GiveawayView(0))

    # ==========================================
    #         SYSTÈME DE BIENVENUE CONFIGURABLE
    # ==========================================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = get_welcome_config()
        guild_id = str(member.guild.id)
        
        if guild_id in config and config[guild_id].get('welcome_channel'):
            channel_id = int(config[guild_id]['welcome_channel'])
            channel = member.guild.get_channel(channel_id)
            
            if channel:
                msg_text = config[guild_id].get('welcome_message', 'Bienvenue {user} !')
                msg_text = msg_text.replace('{user}', member.mention)
                msg_text = msg_text.replace('{server}', member.guild.name)
                msg_text = msg_text.replace('{count}', str(member.guild.member_count))

                embed = discord.Embed(
                    title="🎉 Nouveau Membre !",
                    description=msg_text,
                    color=discord.Color.dark_green()
                )
                
                img_url = config[guild_id].get('welcome_image')
                if img_url:
                    embed.set_image(url=img_url)
                
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Nous sommes désormais {member.guild.member_count} membres !")

                await channel.send(content=member.mention, embed=embed)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            return
            
        custom_id = interaction.data.get('custom_id', '')
        if not custom_id:
            return

        # SYSTÈME D'ÉVÉNEMENTS
        if custom_id.startswith('event_join_'):
            event_id = custom_id.replace('event_join_', '')
            event = self.bot.events_data.get(event_id)
            
            if not event:
                return await interaction.response.send_message("❌ Cet événement est terminé ou introuvable.", ephemeral=True)
                
            if interaction.user.id not in event['participants']:
                event['participants'].append(interaction.user.id)
                await interaction.response.send_message("✅ Ta participation est confirmée !", ephemeral=True)
            else:
                event['participants'].remove(interaction.user.id)
                await interaction.response.send_message("❌ Tu as retiré ta participation.", ephemeral=True)
                
            try:
                channel = interaction.channel
                msg = await channel.fetch_message(event['message_id'])
                embed = msg.embeds[0]
                embed.set_field_at(1, name="👥 Participants", value=str(len(event['participants'])), inline=False)
                await msg.edit(embed=embed)
            except:
                pass
            return

        # SYSTÈME DE CAPTCHA
        if custom_id.startswith('accept_rules_'):
            role_id = int(custom_id.replace('accept_rules_', ''))
            role = interaction.guild.get_role(role_id)
            if not role:
                return await interaction.response.send_message("Erreur : Rôle introuvable.", ephemeral=True)
            if role in interaction.user.roles:
                return await interaction.response.send_message("Tu as déjà accepté le règlement !", ephemeral=True)

            green_index = random.randint(0, 8)
            view = discord.ui.View(timeout=60)
            btn_index = 0
            
            for r in range(3):
                for c in range(3):
                    if btn_index == green_index:
                        btn = discord.ui.Button(emoji="🟩", style=discord.ButtonStyle.secondary, custom_id=f"captcha_ok_{role_id}", row=r)
                    else:
                        btn = discord.ui.Button(emoji="🟥", style=discord.ButtonStyle.secondary, custom_id=f"captcha_no_{role_id}_{btn_index}", row=r)
                    view.add_item(btn)
                    btn_index += 1

            embed = discord.Embed(title="🤖 Vérification Anti-Bot", description="Pour valider ton accès au serveur, prouve que tu es humain.\n### **Clique sur le carré VERT 🟩**", color=discord.Color.orange())
            embed.set_footer(text="Si tu te trompes, tu devras recommencer.")
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        if custom_id.startswith('captcha_'):
            parts = custom_id.split('_')
            if len(parts) < 3: return
            
            is_correct = parts[1] == 'ok'
            role_id = int(parts[2])
            role = interaction.guild.get_role(role_id)

            if not role:
                return await interaction.response.edit_message(content="Erreur : Le rôle est introuvable.", embed=None, view=None)

            if is_correct:
                try:
                    await interaction.user.add_roles(role)
                    success_embed = discord.Embed(description="✅ **Vérification réussie !** Tu as prouvé que tu n'es pas un robot. Tu as maintenant accès au serveur. 🎉", color=discord.Color.green())
                    return await interaction.response.edit_message(embed=success_embed, view=None)
                except Exception:
                    return await interaction.response.edit_message(content="❌ Je n'ai pas la permission de te donner le rôle.", embed=None, view=None)
            else:
                fail_embed = discord.Embed(description="❌ **Perdu !** Tu as cliqué sur un carré rouge. Clique à nouveau sur le bouton du règlement pour réessayer.", color=discord.Color.red())
                return await interaction.response.edit_message(embed=fail_embed, view=None)

        # SYSTÈME DE RÔLES À RÉACTION
        if custom_id.startswith('rr_'):
            role_id = int(custom_id.replace('rr_', ''))
            role = interaction.guild.get_role(role_id)
            if not role:
                return await interaction.response.send_message("Ce rôle n'existe plus.", ephemeral=True)

            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                return await interaction.response.send_message(f"❌ Le rôle **{role.name}** t'a été retiré.", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                return await interaction.response.send_message(f"✅ Le rôle **{role.name}** t'a été attribué.", ephemeral=True)

    @app_commands.command(name="ticket-setup", description="Créer le panneau des tickets.")
    @app_commands.default_permissions(administrator=True)
    async def ticket_setup(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎫 Support - Tickets", description="Besoin d'aide ? Clique sur le bouton ci-dessous pour ouvrir un salon privé avec le staff.", color=discord.Color.blue())
        await interaction.channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message("✅ Panneau créé !", ephemeral=True)

    @app_commands.command(name="role-setup", description="Créer un panneau de rôles avec plusieurs boutons.")
    @app_commands.describe(roles="Mentionne les rôles (ex: @Role1 @Role2)")
    @app_commands.default_permissions(administrator=True)
    async def role_setup(self, interaction: discord.Interaction, roles: str):
        role_ids = [int(r.strip('<@&>')) for r in roles.split() if r.startswith('<@&')]
        if not role_ids: return await interaction.response.send_message("❌ Mentionne au moins un rôle.", ephemeral=True)
        if len(role_ids) > 25: return await interaction.response.send_message("❌ Maximum 25 rôles.", ephemeral=True)
        
        view = discord.ui.View(timeout=None)
        for i, role_id in enumerate(role_ids):
            role = interaction.guild.get_role(role_id)
            if role:
                btn = discord.ui.Button(label=role.name[:70], style=discord.ButtonStyle.primary, custom_id=f"rr_{role_id}", row=i//5)
                view.add_item(btn)
        
        embed = discord.Embed(title="🎨 Rôles auto-attribuables", description="Choisis tes rôles en cliquant sur les boutons ci-dessous !", color=discord.Color.purple())
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Panneau créé !", ephemeral=True)

    @app_commands.command(name="giveaway", description="Lancer un giveaway !")
    @app_commands.describe(duration_minutes="Durée en minutes", prize="Le lot à gagner")
    @app_commands.default_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, duration_minutes: int, prize: str):
        g_id = random.randint(1000, 9999)
        view = GiveawayView(g_id)
        embed = discord.Embed(title="🎉 GIVEAWAY !", description=f"**Lot :** {prize}\n**Fin dans :** {duration_minutes} minutes", color=discord.Color.gold())
        embed.set_footer(text=f"ID: {g_id}")
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        await asyncio.sleep(duration_minutes * 60)
        if not view.participants:
            return await msg.edit(content="🎉 Giveaway terminé ! Aucun participant.", embed=None, view=None)
        winner_id = random.choice(view.participants)
        winner = interaction.guild.get_member(winner_id)
        await msg.edit(content=f"🎉 Giveaway terminé !\nFélicitations à {winner.mention} qui remporte **{prize}** !", embed=None, view=None)

    @app_commands.command(name="sondage", description="Créer un sondage automatique.")
    @app_commands.describe(question="Ta question", minutes="Durée en minutes (défaut: 5)")
    async def sondage(self, interaction: discord.Interaction, question: str, minutes: int = 5):
        embed = discord.Embed(title="📊 Sondage", description=question, color=discord.Color.gold())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Finit dans {minutes} minutes. Votez ci-dessous !")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        await asyncio.sleep(minutes * 60)
        fetched_msg = await msg.channel.fetch_message(msg.id)
        yes = 0
        no = 0
        for r in fetched_msg.reactions:
            if r.emoji == "✅": yes = r.count - 1
            if r.emoji == "❌": no = r.count - 1
            
        if yes > no: res = f"✅ Oui gagne avec {yes} votes ! (Contre {no})"
        elif no > yes: res = f"❌ Non gagne avec {no} votes ! (Contre {yes})"
        else: res = f"🤝 Égalité parfaite ! ({yes} votes chacun)"
        
        final_embed = discord.Embed(title="📊 Sondage Terminé !", description=f"**{question}**\n\n{res}", color=discord.Color.red())
        await msg.edit(embed=final_embed)
        await msg.reply(content="Le sondage est terminé, voici les résultats !")

    @app_commands.command(name="reglement", description="Afficher le règlement avec Captcha Anti-Bot.")
    @app_commands.describe(role="Le rôle à donner après l'acceptation")
    @app_commands.default_permissions(administrator=True)
    async def reglement(self, interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(title="📜 Règlement", description="Voici les règles à respecter !", color=discord.Color.dark_blue())
        embed.add_field(name="1. Respect", value="Aucune insulte n'est tolérée.", inline=False)
        embed.add_field(name="2. Pas de spam", value="Le spam est interdit.", inline=False)
        embed.add_field(name="3. Publicité", value="La pub pour d'autres serveurs est interdite.", inline=False)
        embed.set_footer(text="Clique sur le bouton pour accepter et prouver que tu n'es pas un robot.")
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="J'accepte le règlement", style=discord.ButtonStyle.success, emoji="✅", custom_id=f"accept_rules_{role.id}"))
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="social", description="Affiche tous les liens des réseaux sociaux de la communauté.")
    async def social(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌐 Réseaux Sociaux de la Communauté",
            description="Suis-nous sur nos différentes plateformes pour ne rien rater !",
            color=discord.Color.purple()
        )
        embed.add_field(name="💬 Discord", value="[Rejoins le serveur](https://discord.gg/TONLIEN)", inline=False)
        embed.add_field(name="📺 YouTube", value="[Abonne-toi](https://youtube.com/TONLIEN)", inline=False)
        embed.add_field(name="🎮 Twitch", value="[Suis nos lives](https://twitch.tv/TONLIEN)", inline=False)
        embed.add_field(name="📸 Instagram", value="[Nos photos](https://instagram.com/TONLIEN)", inline=False)
        embed.add_field(name="🎵 TikTok", value="[Nos vidéos](https://tiktok.com/@TONLIEN)", inline=False)
        embed.add_field(name="🐦 Twitter / X", value="[Nos tweets](https://twitter.com/TONLIEN)", inline=False)
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "")
        embed.set_footer(text="Merci de ton soutien ! ❤️")
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    #         COMMANDE /rs (ARTISTES)
    # ==========================================
    @app_commands.command(name="rs", description="Affiche les liens sociaux des artistes de la communauté.")
    @app_commands.describe(artiste="Choisis l'artiste dont tu veux voir les liens.")
    @app_commands.choices(artiste=[
        app_commands.Choice(name="Inima", value="inima"),
        app_commands.Choice(name="Oddymat", value="oddymat"),
        app_commands.Choice(name="RAWPVCK", value="rawpvck"),
        app_commands.Choice(name="Dyph", value="dyph"),
        app_commands.Choice(name="NRKI", value="nrki")
    ])
    async def rs(self, interaction: discord.Interaction, artiste: app_commands.Choice[str]):
        
        embed = discord.Embed(title=f"🎨 Réseaux de {artiste.name}", color=discord.Color.orange())
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "")
        
        if artiste.value == "inima":
            embed.description = "Retrouve **Inima** sur ses plateformes !"
            embed.add_field(name="🎧 Soundcloud", value="[Soundcloud](https://soundcloud.com/inima404)", inline=False)
            embed.add_field(name="Linktree", value="[Linktree](https://linktr.ee/inima.404?utm_source=ig&utm_medium=social&utm_content=link_in_bio)", inline=False)
            embed.add_field(name="📸 Instagram", value="[Suivre sur Instagram](https://www.instagram.com/inima.404?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==)", inline=False)
            
        elif artiste.value == "oddymat":
            embed.description = "Retrouve **Oddymatt** sur ses plateformes !"
            embed.add_field(name="🎧 Spotify", value="[Écouter sur Spotify](https://open.spotify.com/intl-fr/artist/7J8dXDX8bBsEs4N1tWJDnI?si=_ik2dFHJSpGiPKf_vLL-Uw)", inline=False)
            embed.add_field(name="Site", value="[Site](https://oddymatt.com/?utm_source=ig&utm_medium=social&utm_content=link_in_bio)", inline=False)
            embed.add_field(name="📸 Instagram", value="[Suivre sur Instagram](https://www.instagram.com/oddymatt_music?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==)", inline=False)
            
        elif artiste.value == "rawpvck":
            embed.description = "Retrouve **RAWPVCK** sur ses plateformes !"
            embed.add_field(name="🎧 Spotify", value="[Écouter sur Spotify](https://open.spotify.com/intl-fr/artist/0u4s0r7U9ryKAz568hYnhe?si=fHSmBjknQWemqA3mPM23ug)", inline=False)
            embed.add_field(name="Linktree", value="[Linktree](https://linktr.ee/rawpvck?utm_source=ig&utm_medium=social&utm_content=link_in_bio)", inline=False)
            embed.add_field(name="📸 Instagram", value="[Suivre sur Instagram](https://www.instagram.com/rawpvck?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==)", inline=False)
            
        elif artiste.value == "dyph":
            embed.description = "Retrouve **Dyph** sur ses plateformes !"
            embed.add_field(name="🎧 Spotify", value="[Écouter sur Spotify](https://open.spotify.com/intl-fr/artist/0sdN10uN7U1xmEbPlkla7k?si=xfhgwx6yQOSqAH0H5UnOTQ)", inline=False)
            embed.add_field(name="📸 Instagram", value="[Suivre sur Instagram](https://www.instagram.com/dyphmusic?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==)", inline=False)
            
        elif artiste.value == "nrki":
            embed.description = "Retrouve **NRKI** sur ses plateformes !"
            embed.add_field(name="🎧 Spotify", value="[Écouter sur Spotify](https://open.spotify.com/intl-fr/artist/1t8yas984NoFDReRcOpI3n?si=32p1SJtBSsu6m3iCVett5A)", inline=False)
            embed.add_field(name="📺 Tiktok", value="[Voir sur Tiktok](https://www.tiktok.com/@nrkihard?is_from_webapp=1&sender_device=pc)", inline=False)
            embed.add_field(name="📸 Instagram", value="[Suivre sur Instagram](https://www.instagram.com/nrkihard?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==)", inline=False)
            
        embed.set_footer(text="Soutiens nos artistes ! ❤️")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Community(bot))
