import os
import discord
from discord.ext import commands
from aiohttp import web

class WebDashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.setup_routes()

    async def cog_load(self):
        self.bot.loop.create_task(self.run_web())

    async def run_web(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        port = int(os.environ.get('PORT', 5000))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"🌐 Dashboard web démarré sur le port {port}")

    def setup_routes(self):
        self.app.router.add_get('/', self.dashboard_home)
        self.app.router.add_get('/api/guilds', self.api_guilds)
        self.app.router.add_get('/api/guild/{guild_id}/data', self.api_guild_data)
        self.app.router.add_post('/api/send-embed', self.api_send_embed)
        self.app.router.add_post('/api/send-rules', self.api_send_rules)
        self.app.router.add_post('/api/send-rr', self.api_send_rr)
        self.app.router.add_post('/api/set-status', self.api_set_status)

    async def dashboard_home(self, request):
        html = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard Bot</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
                * { box-sizing: border-box; font-family: 'Inter', sans-serif; }
                body { background: radial-gradient(circle at 0% 0%, #1a1c20 0%, #0e0f12 100%); color: #e6e8eb; margin: 0; padding: 50px 20px; display: flex; justify-content: center; min-height: 100vh; }
                ::-webkit-scrollbar { width: 8px; }
                ::-webkit-scrollbar-track { background: #1e1f22; }
                ::-webkit-scrollbar-thumb { background: #5865F2; border-radius: 4px; }
                .wrapper { width: 100%; max-width: 800px; }
                .glass-card { background: rgba(35, 37, 42, 0.6); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 24px; padding: 40px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5); margin-bottom: 32px; }
                h1 { font-size: 32px; font-weight: 800; margin: 0 0 20px 0; background: linear-gradient(90deg, #ffffff, #b5bac1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 20px; }
                h2 { font-size: 20px; font-weight: 600; margin: 0 0 24px 0; color: #ffffff; text-transform: uppercase; letter-spacing: 1px; }
                .status-badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; background: rgba(45, 199, 112, 0.1); border: 1px solid rgba(45, 199, 112, 0.3); border-radius: 50px; color: #2dc770; font-size: 14px; font-weight: 600; margin-bottom: 30px; }
                .dot { width: 8px; height: 8px; background: #2dc770; border-radius: 50%; box-shadow: 0 0 10px #2dc770; }
                .form-group { margin-bottom: 24px; }
                label { display: block; margin-bottom: 10px; font-size: 12px; font-weight: 600; text-transform: uppercase; color: #80848e; letter-spacing: 0.5px; }
                select, input[type="text"], input[type="url"], textarea { width: 100%; background: rgba(14, 15, 18, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px 16px; color: #e6e8eb; font-size: 15px; outline: none; transition: all 0.2s; }
                select:focus, input:focus, textarea:focus { border-color: #5865F2; box-shadow: 0 0 0 4px rgba(88, 101, 242, 0.1); }
                textarea { resize: vertical; min-height: 100px; }
                select[multiple] { height: 120px; }
                .btn { border: none; padding: 16px 24px; border-radius: 12px; font-size: 15px; font-weight: 700; cursor: pointer; width: 100%; transition: all 0.3s; text-transform: uppercase; letter-spacing: 0.5px; }
                .btn-primary { background: linear-gradient(135deg, #5865F2, #4752c4); color: white; box-shadow: 0 4px 15px rgba(88, 101, 242, 0.3); margin-bottom: 10px; }
                .btn-success { background: linear-gradient(135deg, #2dc770, #26a85f); color: white; }
                .btn-gold { background: linear-gradient(135deg, #FFD700, #FFB800); color: black; }
                .btn-pink { background: linear-gradient(135deg, #EB459E, #d63384); color: white; }
                .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3); }
                .alert { padding: 16px; border-radius: 12px; margin-bottom: 20px; font-weight: 600; display: none; }
                .alert.success { background: rgba(45, 199, 112, 0.1); color: #2dc770; border: 1px solid rgba(45, 199, 112, 0.2); }
                .alert.error { background: rgba(242, 63, 66, 0.1); color: #f23f42; border: 1px solid rgba(242, 63, 66, 0.2); }
                .row { display: flex; gap: 20px; }
                .row .form-group { flex: 1; }
            </style>
        </head>
        <body>
            <div class="wrapper">
                <div class="glass-card">
                    <h1>🤖 Dashboard Bot</h1>
                    <div class="status-badge"><span class="dot"></span> Bot En Ligne</div>
                    <div class="form-group">
                        <label for="guildSelect">Sélectionne un Serveur</label>
                        <select id="guildSelect"><option>Chargement...</option></select>
                    </div>
                </div>

                <div class="glass-card">
                    <h2>🎮 Activité du Bot</h2>
                    <div id="statusAlert" class="alert"></div>
                    <div class="row">
                        <div class="form-group"><label>Type</label><select id="statusType"><option value="playing">Joue à</option><option value="watching">Regarde</option><option value="listening">Écoute</option><option value="competing">Participe à</option></select></div>
                        <div class="form-group" style="flex: 2;"><label>Texte</label><input type="text" id="statusText" placeholder="ex: la communauté"></div>
                    </div>
                    <button class="btn btn-success" onclick="setStatus()">Mettre à jour le statut</button>
                </div>

                <div class="glass-card">
                    <h2>📝 Annonce (Embed)</h2>
                    <div id="embedAlert" class="alert"></div>
                    <div class="form-group"><label>Salon</label><select id="embedChannel" disabled><option>-</option></select></div>
                    <div class="form-group"><label>Titre</label><input type="text" id="embedTitle" placeholder="Titre de l'annonce"></div>
                    <div class="form-group"><label>Description</label><textarea id="embedDesc" placeholder="Texte principal"></textarea></div>
                    <div class="row">
                        <div class="form-group"><label>Couleur (Hex)</label><input type="text" id="embedColor" value="#5865F2" placeholder="#FF0000"></div>
                        <div class="form-group" style="flex: 2;"><label>Image (URL)</label><input type="url" id="embedImage" placeholder="https://..."></div>
                    </div>
                    <button class="btn btn-primary" onclick="sendEmbed()">Envoyer l'Embed</button>
                </div>

                <div class="glass-card">
                    <h2>📜 Règlement avec Captcha</h2>
                    <div id="rulesAlert" class="alert"></div>
                    <div class="form-group"><label>Salon</label><select id="rulesChannel" disabled><option>-</option></select></div>
                    <div class="form-group"><label>Rôle à donner après validation</label><select id="rulesRole" disabled><option>-</option></select></div>
                    <button class="btn btn-primary" onclick="sendRules()">Envoyer le Règlement</button>
                </div>

                <div class="glass-card">
                    <h2>🎭 Rôles à Réaction</h2>
                    <div id="rrAlert" class="alert"></div>
                    <div class="form-group"><label>Salon</label><select id="rrChannel" disabled><option>-</option></select></div>
                    <div class="form-group"><label>Rôles (Maintiens Ctrl pour choisir plusieurs)</label><select id="rrRoles" multiple disabled></select></div>
                    <button class="btn btn-pink" onclick="sendRR()">Envoyer le Panneau</button>
                </div>
            </div>

            <script>
                const guildSelect = document.getElementById('guildSelect');
                
                async function loadGuilds() {
                    const res = await fetch('/api/guilds');
                    const guilds = await res.json();
                    guildSelect.innerHTML = '<option value="">-- Choisir un serveur --</option>' + guilds.map(g => '<option value="' + g.id + '">' + g.name + '</option>').join('');
                }

                guildSelect.addEventListener('change', async (e) => {
                    const guildId = e.target.value;
                    if (!guildId) return;
                    const res = await fetch('/api/guild/' + guildId + '/data');
                    const data = await res.json();
                    
                    const channels = data.channels.map(c => '<option value="' + c.id + '">#' + c.name + '</option>').join('');
                    const roles = data.roles.map(r => '<option value="' + r.id + '">' + r.name + '</option>').join('');
                    
                    document.getElementById('embedChannel').innerHTML = channels;
                    document.getElementById('rulesChannel').innerHTML = channels;
                    document.getElementById('rrChannel').innerHTML = channels;
                    document.getElementById('rulesRole').innerHTML = roles;
                    document.getElementById('rrRoles').innerHTML = roles;
                    
                    document.getElementById('embedChannel').disabled = false;
                    document.getElementById('rulesChannel').disabled = false;
                    document.getElementById('rrChannel').disabled = false;
                    document.getElementById('rulesRole').disabled = false;
                    document.getElementById('rrRoles').disabled = false;
                });

                function showAlert(id, success, msg) {
                    const el = document.getElementById(id);
                    el.className = 'alert ' + (success ? 'success' : 'error');
                    el.innerText = (success ? '✅ ' : '❌ ') + msg;
                    el.style.display = 'block';
                    setTimeout(() => el.style.display = 'none', 4000);
                }

                async function setStatus() {
                    const type = document.getElementById('statusType').value;
                    const text = document.getElementById('statusText').value;
                    const res = await fetch('/api/set-status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type, text }) });
                    const data = await res.json();
                    showAlert('statusAlert', data.success, data.message);
                }

                async function sendEmbed() {
                    const body = {
                        guildId: guildSelect.value,
                        channelId: document.getElementById('embedChannel').value,
                        title: document.getElementById('embedTitle').value,
                        description: document.getElementById('embedDesc').value,
                        color: document.getElementById('embedColor').value,
                        image: document.getElementById('embedImage').value
                    };
                    const res = await fetch('/api/send-embed', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
                    const data = await res.json();
                    showAlert('embedAlert', data.success, data.message);
                }

                async function sendRules() {
                    const body = {
                        guildId: guildSelect.value,
                        channelId: document.getElementById('rulesChannel').value,
                        roleId: document.getElementById('rulesRole').value
                    };
                    const res = await fetch('/api/send-rules', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
                    const data = await res.json();
                    showAlert('rulesAlert', data.success, data.message);
                }

                async function sendRR() {
                    const roles = Array.from(document.getElementById('rrRoles').selectedOptions).map(opt => opt.value);
                    const body = {
                        guildId: guildSelect.value,
                        channelId: document.getElementById('rrChannel').value,
                        roles: roles
                    };
                    const res = await fetch('/api/send-rr', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
                    const data = await res.json();
                    showAlert('rrAlert', data.success, data.message);
                }

                loadGuilds();
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')

    async def api_guilds(self, request):
        guilds = [{"id": str(g.id), "name": g.name} for g in self.bot.guilds]
        return web.json_response(guilds)

    async def api_guild_data(self, request):
        guild_id = int(request.match_info.get('guild_id'))
        guild = self.bot.get_guild(guild_id)
        if not guild: return web.json_response({"error": "Serveur introuvable"}, status=404)
        
        channels = [{"id": str(c.id), "name": c.name} for c in guild.text_channels]
        roles = [{"id": str(r.id), "name": r.name} for r in guild.roles if not r.managed and r.name != "@everyone"]
        return web.json_response({"channels": channels, "roles": roles})

    async def api_send_embed(self, request):
        data = await request.json()
        guild = self.bot.get_guild(int(data['guildId']))
        channel = guild.get_channel(int(data['channelId']))
        if not channel: return web.json_response({"success": False, "message": "Salon introuvable"})
        
        try:
            color = int(data['color'].replace("#", ""), 16)
        except:
            color = 0x5865F2
            
        embed = discord.Embed(title=data['title'], description=data['description'], color=color)
        if data.get('image'): embed.set_image(url=data['image'])
        embed.set_footer(text="Dashboard Bot")
        
        await channel.send(embed=embed)
        return web.json_response({"success": True, "message": "Embed envoyé !"})

    async def api_send_rules(self, request):
        data = await request.json()
        guild = self.bot.get_guild(int(data['guildId']))
        channel = guild.get_channel(int(data['channelId']))
        if not channel: return web.json_response({"success": False, "message": "Salon introuvable"})
        
        embed = discord.Embed(title="📜 Règlement", description="Voici les règles à respecter !", color=discord.Color.dark_blue())
        embed.add_field(name="1. Respect", value="Aucune insulte n'est tolérée.", inline=False)
        embed.add_field(name="2. Pas de spam", value="Le spam est interdit.", inline=False)
        embed.add_field(name="3. Publicité", value="La pub pour d'autres serveurs est interdite.", inline=False)
        embed.set_footer(text="Clique sur le bouton pour accepter et prouver que tu n'es pas un robot.")
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="J'accepte le règlement", style=discord.ButtonStyle.success, emoji="✅", custom_id=f"accept_rules_{data['roleId']}"))
        
        await channel.send(embed=embed, view=view)
        return web.json_response({"success": True, "message": "Règlement envoyé !"})

    async def api_send_rr(self, request):
        data = await request.json()
        guild = self.bot.get_guild(int(data['guildId']))
        channel = guild.get_channel(int(data['channelId']))
        if not channel: return web.json_response({"success": False, "message": "Salon introuvable"})
        if not data['roles']: return web.json_response({"success": False, "message": "Sélectionne au moins un rôle."})

        view = discord.ui.View(timeout=None)
        for i, role_id in enumerate(data['roles']):
            role = guild.get_role(int(role_id))
            if role:
                btn = discord.ui.Button(label=role.name[:70], style=discord.ButtonStyle.primary, custom_id=f"rr_{role_id}", row=i//5)
                view.add_item(btn)
        
        embed = discord.Embed(title="🎨 Rôles auto-attribuables", description="Choisis tes rôles en cliquant sur les boutons ci-dessous !", color=discord.Color.purple())
        await channel.send(embed=embed, view=view)
        return web.json_response({"success": True, "message": "Panneau de rôles envoyé !"})

    async def api_set_status(self, request):
        data = await request.json()
        activity_type = getattr(discord.ActivityType, data['type'])
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=activity_type, name=data['text']))
        return web.json_response({"success": True, "message": "Statut mis à jour !"})

async def setup(bot):
    await bot.add_cog(WebDashboard(bot))
