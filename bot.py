import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import json, os, asyncio
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

BOSSES_FILE = "bosses.json"

# Venezuela = UTC-4
VE_OFFSET = timezone(timedelta(hours=-4))

BOSS_CATALOG = {
    "yellow goblin": {
        "nombre": "Yellow Goblin",
        "emoji": "🟡",
        "mapa": "Shadow Abyss",
        "min_h": 11, "max_h": 12,
        "imagen": "https://i.imgur.com/fWL67fH.gif"
    },
    "red goblin": {
        "nombre": "Red Goblin",
        "emoji": "🔴",
        "mapa": "Shadow Abyss",
        "min_h": 11, "max_h": 12,
        "imagen": "https://i.imgur.com/76UUAuZ.gif"
    },
    "blue goblin": {
        "nombre": "Blue Goblin",
        "emoji": "🔵",
        "mapa": "Shadow Abyss",
        "min_h": 11, "max_h": 12,
        "imagen": "https://i.imgur.com/BHXkAoK.gif"
    },
    "mugron shadow": {
        "nombre": "Mugron",
        "emoji": "🟡",
        "mapa": "Shadow Abyss",
        "min_h": 3, "max_h": 4,
        "imagen": "https://i.imgur.com/dTNmEvR.gif"
    },
    "mugron crywolf": {
        "nombre": "Mugron",
        "emoji": "🟡",
        "mapa": "Crywolf",
        "min_h": 3, "max_h": 4,
        "imagen": "https://i.imgur.com/dTNmEvR.gif"
    },
    "mugron barracks": {
        "nombre": "Mugron",
        "emoji": "🟡",
        "mapa": "Barracks",
        "min_h": 3, "max_h": 4,
        "imagen": "https://i.imgur.com/dTNmEvR.gif"
    },
    "vescryal shadow": {
        "nombre": "Vescryal",
        "emoji": "🟣",
        "mapa": "Shadow Abyss",
        "min_h": 7, "max_h": 8,
        "imagen": "https://i.imgur.com/c7YT5D6.gif"
    },
    "vescryal devias": {
        "nombre": "Vescryal",
        "emoji": "🟣",
        "mapa": "Devias Ruins",
        "min_h": 7, "max_h": 8,
        "imagen": "https://i.imgur.com/c7YT5D6.gif"
    },
    "kharzul shadow": {
        "nombre": "Kharzul",
        "emoji": "🔵",
        "mapa": "Shadow Abyss",
        "min_h": 7, "max_h": 8,
        "imagen": "https://i.imgur.com/YzJiH1T.gif"
    },
    "kharzul loren": {
        "nombre": "Kharzul",
        "emoji": "🔵",
        "mapa": "Loren Ruins",
        "min_h": 7, "max_h": 8,
        "imagen": "https://i.imgur.com/YzJiH1T.gif"
    },
    "red dragon": {
        "nombre": "Red Dragon",
        "emoji": "🐉",
        "mapa": "Shadow Abyss",
        "min_h": 6, "max_h": 6,
        "imagen": "https://i.imgur.com/ibHLECk.gif"
    },
    "bogart": {
        "nombre": "Bogart",
        "emoji": "🗡️",
        "mapa": "Shadow Abyss",
        "min_h": 2, "max_h": 3,
        "imagen": "https://i.imgur.com/TLV5d3q.gif"
    },
}

# Invasión Dorada — horarios fijos Venezuela (UTC-4), cada 4h
# Primera: 6:30, luego 10:30, 14:30, 18:30, 22:30, 2:30
INVASION_HORARIOS = [
    (2, 30), (6, 30), (10, 30), (14, 30), (18, 30), (22, 30)
]
INVASION_IMG = "https://i.imgur.com/oGc9qdV.gif"

def load_bosses():
    if os.path.exists(BOSSES_FILE):
        with open(BOSSES_FILE) as f:
            return json.load(f)
    return {}

def save_bosses(data):
    with open(BOSSES_FILE, "w") as f:
        json.dump(data, f, indent=2)

bosses = load_bosses()

def tiempo_restante_str(diff_secs):
    if diff_secs <= 0:
        return "¡AHORA!"
    h = int(diff_secs // 3600)
    m = int((diff_secs % 3600) // 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

def proxima_invasion():
    now = datetime.now(VE_OFFSET)
    for h, m in sorted(INVASION_HORARIOS):
        candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if candidate > now:
            return candidate
    # siguiente día
    first_h, first_m = INVASION_HORARIOS[0]
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=first_h, minute=first_m, second=0, microsecond=0)

class BossView(View):
    def __init__(self, boss_key):
        super().__init__(timeout=None)
        self.boss_key = boss_key

    @discord.ui.button(label="⚔️ Maté", style=discord.ButtonStyle.danger, custom_id="mate_btn")
    async def mate_btn(self, interaction: discord.Interaction, button: Button):
        key = self.boss_key
        if key not in bosses:
            await interaction.response.send_message("❌ Timer no encontrado.", ephemeral=True)
            return

        boss = bosses[key]
        catalogo = BOSS_CATALOG.get(key)
        if not catalogo:
            await interaction.response.send_message("❌ Boss no encontrado en catálogo.", ephemeral=True)
            return

        min_h = catalogo["min_h"]
        max_h = catalogo["max_h"]
        muerte_utc = datetime.utcnow()
        respawn_min = muerte_utc + timedelta(hours=min_h)
        respawn_max = muerte_utc + timedelta(hours=max_h)

        bosses[key].update({
            "muerte_utc": muerte_utc.isoformat(),
            "respawn_min_utc": respawn_min.isoformat(),
            "respawn_max_utc": respawn_max.isoformat(),
            "confirmado_por": interaction.user.name,
            "auto_reinicio": False,
            "notif_30": False,
            "notif_10": False,
            "notif_spawn": False,
        })
        save_bosses(bosses)

        muerte_ve = muerte_utc.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        respawn_min_ve = respawn_min.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        respawn_max_ve = respawn_max.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)

        embed = discord.Embed(
            title=f"💀 {catalogo['emoji']} {catalogo['nombre']} — {catalogo['mapa']}",
            description="**VENTANA DE SPAWN**",
            color=0xFF4444
        )
        embed.add_field(name="Hora de muerte (VE)", value=muerte_ve.strftime("%H:%M"), inline=True)
        embed.add_field(name="Spawn mínimo (VE)", value=respawn_min_ve.strftime("%H:%M"), inline=True)
        embed.add_field(name="Spawn máximo (VE)", value=respawn_max_ve.strftime("%H:%M"), inline=True)
        embed.add_field(name="Confirmado por", value=interaction.user.name, inline=False)
        embed.set_image(url=catalogo["imagen"])
        embed.set_footer(text=f"⏱️ Ventana: {min_h}h – {max_h}h")

        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="🔁 Repetir horario", style=discord.ButtonStyle.success, custom_id="repetir_btn")
    async def repetir_btn(self, interaction: discord.Interaction, button: Button):
        key = self.boss_key
        if key not in bosses or not bosses[key].get("muerte_utc"):
            await interaction.response.send_message("❌ No hay muerte registrada para repetir.", ephemeral=True)
            return

        boss = bosses[key]
        catalogo = BOSS_CATALOG.get(key)
        respawn_min_ve = datetime.fromisoformat(boss["respawn_min_utc"]).replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        respawn_max_ve = datetime.fromisoformat(boss["respawn_max_utc"]).replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)

        embed = discord.Embed(
            title=f"🔁 {catalogo['emoji']} {catalogo['nombre']} — {catalogo['mapa']}",
            description="**Repitiendo último horario registrado**",
            color=0x00AA00
        )
        embed.add_field(name="Spawn mínimo (VE)", value=respawn_min_ve.strftime("%H:%M"), inline=True)
        embed.add_field(name="Spawn máximo (VE)", value=respawn_max_ve.strftime("%H:%M"), inline=True)
        embed.set_image(url=catalogo["imagen"])

        await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    # Registrar vistas persistentes
    for key in BOSS_CATALOG:
        bot.add_view(BossView(key))
    check_timers.start()
    check_invasion.start()

@bot.command(name="mate")
async def registrar_muerte(ctx, *, nombre: str):
    """Registra muerte de un boss. Uso: !mate yellow goblin"""
    key = nombre.lower().strip()
    catalogo = BOSS_CATALOG.get(key)

    if not catalogo:
        lista = "\n".join([f"• `!mate {k}`" for k in BOSS_CATALOG.keys()])
        await ctx.send(f"❌ Boss no encontrado. Opciones disponibles:\n{lista}")
        return

    muerte_utc = datetime.utcnow()
    respawn_min = muerte_utc + timedelta(hours=catalogo["min_h"])
    respawn_max = muerte_utc + timedelta(hours=catalogo["max_h"])

    bosses[key] = {
        "muerte_utc": muerte_utc.isoformat(),
        "respawn_min_utc": respawn_min.isoformat(),
        "respawn_max_utc": respawn_max.isoformat(),
        "canal_id": ctx.channel.id,
        "confirmado_por": ctx.author.name,
        "auto_reinicio": False,
        "notif_30": False,
        "notif_10": False,
        "notif_spawn": False,
    }
    save_bosses(bosses)

    muerte_ve = muerte_utc.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
    respawn_min_ve = respawn_min.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
    respawn_max_ve = respawn_max.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)

    embed = discord.Embed(
        title=f"💀 {catalogo['emoji']} {catalogo['nombre']} — {catalogo['mapa']}",
        description="**VENTANA OBLIGATORIA DE SPAWN**",
        color=0xFF4444
    )
    embed.add_field(name="⏰ Hora de muerte (VE)", value=muerte_ve.strftime("%H:%M"), inline=True)
    embed.add_field(name="🟢 Spawn mínimo (VE)", value=respawn_min_ve.strftime("%H:%M"), inline=True)
    embed.add_field(name="🔴 Spawn máximo (VE)", value=respawn_max_ve.strftime("%H:%M"), inline=True)
    embed.add_field(name="👤 Registrado por", value=ctx.author.name, inline=False)
    embed.set_image(url=catalogo["imagen"])
    embed.set_footer(text=f"Ventana: {catalogo['min_h']}h – {catalogo['max_h']}h | El timer se reinicia automáticamente si no se confirma")

    view = BossView(key)
    await ctx.send(embed=embed, view=view)

@bot.command(name="timers")
async def ver_timers(ctx):
    """Muestra todos los timers activos"""
    if not bosses:
        await ctx.send("📭 No hay timers activos. Usa `!mate <boss>` para registrar una muerte.")
        return

    now = datetime.utcnow()
    embed = discord.Embed(title="⏱️ Timers de Bosses Activos", color=0xFFAA00)
    embed.set_footer(text="Hora Venezuela (UTC-4)")

    activos = []
    for key, boss in bosses.items():
        if not boss.get("respawn_min_utc"):
            continue
        catalogo = BOSS_CATALOG.get(key, {})
        respawn_min = datetime.fromisoformat(boss["respawn_min_utc"])
        respawn_max = datetime.fromisoformat(boss["respawn_max_utc"])
        diff_min = (respawn_min - now).total_seconds()
        diff_max = (respawn_max - now).total_seconds()

        respawn_min_ve = respawn_min.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        respawn_max_ve = respawn_max.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)

        if diff_max < 0:
            status = "🟢 VENTANA CERRADA — reinicio pendiente"
        elif diff_min < 0:
            status = f"🚨 EN VENTANA — máximo a las {respawn_max_ve.strftime('%H:%M')}"
        else:
            status = f"🔴 {tiempo_restante_str(diff_min)} — ventana {respawn_min_ve.strftime('%H:%M')} a {respawn_max_ve.strftime('%H:%M')}"

        nombre_completo = f"{catalogo.get('emoji','')} {catalogo.get('nombre', key)} [{catalogo.get('mapa','')}]"
        activos.append((diff_min, nombre_completo, status))

    activos.sort()
    for _, nombre, status in activos:
        embed.add_field(name=nombre, value=status, inline=False)

    # Próxima invasión
    prox = proxima_invasion()
    diff_inv = (prox - datetime.now(VE_OFFSET)).total_seconds()
    embed.add_field(
        name="⚔️ Invasión Dorada",
        value=f"Próxima a las {prox.strftime('%H:%M')} VE — en {tiempo_restante_str(diff_inv)}",
        inline=False
    )

    await ctx.send(embed=embed)

@bot.command(name="bosses")
async def lista_bosses(ctx):
    """Muestra todos los bosses disponibles"""
    embed = discord.Embed(title="📋 Bosses disponibles", color=0x7777FF)
    for key, cat in BOSS_CATALOG.items():
        embed.add_field(
            name=f"{cat['emoji']} {cat['nombre']} — {cat['mapa']}",
            value=f"Respawn: {cat['min_h']}h – {cat['max_h']}h | `!mate {key}`",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command(name="borrar")
async def borrar_timer(ctx, *, nombre: str):
    """Borra un timer. Uso: !borrar yellow goblin"""
    key = nombre.lower().strip()
    if key in bosses:
        del bosses[key]
        save_bosses(bosses)
        cat = BOSS_CATALOG.get(key, {})
        await ctx.send(f"✅ Timer de **{cat.get('nombre', key)}** [{cat.get('mapa','')}] eliminado.")
    else:
        await ctx.send(f"❌ No encontré el timer de `{key}`")

@tasks.loop(minutes=1)
async def check_timers():
    now = datetime.utcnow()
    for key, boss in list(bosses.items()):
        if not boss.get("respawn_min_utc"):
            continue
        catalogo = BOSS_CATALOG.get(key)
        if not catalogo:
            continue

        respawn_min = datetime.fromisoformat(boss["respawn_min_utc"])
        respawn_max = datetime.fromisoformat(boss["respawn_max_utc"])
        diff_min_secs = (respawn_min - now).total_seconds()
        diff_max_secs = (respawn_max - now).total_seconds()
        canal = bot.get_channel(boss["canal_id"])
        if not canal:
            continue

        nombre_completo = f"{catalogo['emoji']} {catalogo['nombre']} [{catalogo['mapa']}]"

        # Aviso 30 min antes del mínimo
        if 1740 <= diff_min_secs <= 1800 and not boss.get("notif_30"):
            bosses[key]["notif_30"] = True
            save_bosses(bosses)
            await canal.send(f"⚠️ **{nombre_completo}** spawna en **30 minutos**")

        # Aviso 10 min antes del mínimo
        elif 540 <= diff_min_secs <= 600 and not boss.get("notif_10"):
            bosses[key]["notif_10"] = True
            save_bosses(bosses)
            await canal.send(f"⚠️ **{nombre_completo}** spawna en **10 minutos**")

        # Aviso al llegar al mínimo (ventana abierta)
        elif -60 <= diff_min_secs <= 0 and not boss.get("notif_spawn"):
            bosses[key]["notif_spawn"] = True
            save_bosses(bosses)
            respawn_max_ve = respawn_max.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
            embed = discord.Embed(
                title=f"🚨 {nombre_completo} — ¡VENTANA ABIERTA!",
                description=f"El boss **puede spawnear ahora**.\nVentana cierra a las **{respawn_max_ve.strftime('%H:%M')} VE**",
                color=0xFF0000
            )
            embed.set_image(url=catalogo["imagen"])
            view = BossView(key)
            await canal.send(embed=embed, view=view)

        # Reinicio automático al llegar al máximo sin confirmación
        elif diff_max_secs <= 0 and not boss.get("auto_reinicio"):
            bosses[key]["auto_reinicio"] = True
            save_bosses(bosses)

            # Reiniciar timer
            nueva_muerte = now
            nuevo_min = nueva_muerte + timedelta(hours=catalogo["min_h"])
            nuevo_max = nueva_muerte + timedelta(hours=catalogo["max_h"])
            nuevo_min_ve = nuevo_min.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
            nuevo_max_ve = nuevo_max.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)

            bosses[key].update({
                "muerte_utc": nueva_muerte.isoformat(),
                "respawn_min_utc": nuevo_min.isoformat(),
                "respawn_max_utc": nuevo_max.isoformat(),
                "auto_reinicio": False,
                "notif_30": False,
                "notif_10": False,
                "notif_spawn": False,
            })
            save_bosses(bosses)

            embed = discord.Embed(
                title=f"🔄 {nombre_completo} — Reinicio automático",
                description="Nadie confirmó la muerte. El timer se reinició automáticamente.",
                color=0xFFAA00
            )
            embed.add_field(name="Próximo mínimo (VE)", value=nuevo_min_ve.strftime("%H:%M"), inline=True)
            embed.add_field(name="Próximo máximo (VE)", value=nuevo_max_ve.strftime("%H:%M"), inline=True)
            embed.set_image(url=catalogo["imagen"])
            view = BossView(key)
            await canal.send(embed=embed, view=view)

@tasks.loop(minutes=1)
async def check_invasion():
    now_ve = datetime.now(VE_OFFSET)
    prox = proxima_invasion()
    diff_secs = (prox - now_ve).total_seconds()

    # Aviso 10 minutos antes
    if 540 <= diff_secs <= 600:
        # Buscar canal de cualquier boss activo para notificar
        for key, boss in bosses.items():
            canal = bot.get_channel(boss.get("canal_id", 0))
            if canal:
                embed = discord.Embed(
                    title="⚔️ ¡INVASIÓN DORADA EN 10 MINUTOS!",
                    description=f"La invasión comienza a las **{prox.strftime('%H:%M')} VE**",
                    color=0xFFD700
                )
                embed.set_image(url=INVASION_IMG)
                await canal.send(embed=embed)
                break

bot.run(TOKEN)
