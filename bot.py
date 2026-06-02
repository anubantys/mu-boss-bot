import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import json, os
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

BOSSES_FILE = "bosses.json"
VE_OFFSET = timezone(timedelta(hours=-4))

BOSS_CATALOG = {
    "yellow goblin": {
        "nombre": "Yellow Goblin", "emoji": "🟡", "mapa": "Shadow Abyss",
        "min_h": 11, "max_h": 12, "imagen": "https://i.imgur.com/fWL67fH.gif"
    },
    "red goblin": {
        "nombre": "Red Goblin", "emoji": "🔴", "mapa": "Shadow Abyss",
        "min_h": 11, "max_h": 12, "imagen": "https://i.imgur.com/76UUAuZ.gif"
    },
    "blue goblin": {
        "nombre": "Blue Goblin", "emoji": "🔵", "mapa": "Shadow Abyss",
        "min_h": 11, "max_h": 12, "imagen": "https://i.imgur.com/BHXkAoK.gif"
    },
    "red dragon": {
        "nombre": "Red Dragon", "emoji": "🐉", "mapa": "Shadow Abyss",
        "min_h": 6, "max_h": 6, "imagen": "https://i.imgur.com/ibHLECk.gif"
    },
    "bogart": {
        "nombre": "Bogart", "emoji": "🗡️", "mapa": "Shadow Abyss",
        "min_h": 2, "max_h": 3, "imagen": "https://i.imgur.com/TLV5d3q.gif"
    },
    # Mugron
    "mugron shadow": {
        "nombre": "Mugron", "emoji": "🟡", "mapa": "Shadow Abyss",
        "min_h": 3, "max_h": 4, "imagen": "https://i.imgur.com/dTNmEvR.gif"
    },
    "mugron crywolf 1": {
        "nombre": "Mugron 1", "emoji": "🟡", "mapa": "Crywolf",
        "min_h": 3, "max_h": 4, "imagen": "https://i.imgur.com/dTNmEvR.gif"
    },
    "mugron crywolf 2": {
        "nombre": "Mugron 2", "emoji": "🟡", "mapa": "Crywolf",
        "min_h": 3, "max_h": 4, "imagen": "https://i.imgur.com/dTNmEvR.gif"
    },
    "mugron barracks 1": {
        "nombre": "Mugron 1", "emoji": "🟡", "mapa": "Barracks",
        "min_h": 3, "max_h": 4, "imagen": "https://i.imgur.com/dTNmEvR.gif"
    },
    "mugron barracks 2": {
        "nombre": "Mugron 2", "emoji": "🟡", "mapa": "Barracks",
        "min_h": 3, "max_h": 4, "imagen": "https://i.imgur.com/dTNmEvR.gif"
    },
    # Vescryal
    "vescryal shadow": {
        "nombre": "Vescryal", "emoji": "🟣", "mapa": "Shadow Abyss",
        "min_h": 7, "max_h": 8, "imagen": "https://i.imgur.com/c7YT5D6.gif"
    },
    "vescryal devias 1": {
        "nombre": "Vescryal 1", "emoji": "🟣", "mapa": "Devias Ruins",
        "min_h": 7, "max_h": 8, "imagen": "https://i.imgur.com/c7YT5D6.gif"
    },
    "vescryal devias 2": {
        "nombre": "Vescryal 2", "emoji": "🟣", "mapa": "Devias Ruins",
        "min_h": 7, "max_h": 8, "imagen": "https://i.imgur.com/c7YT5D6.gif"
    },
    "vescryal devias 3": {
        "nombre": "Vescryal 3", "emoji": "🟣", "mapa": "Devias Ruins",
        "min_h": 7, "max_h": 8, "imagen": "https://i.imgur.com/c7YT5D6.gif"
    },
    # Kharzul
    "kharzul shadow": {
        "nombre": "Kharzul", "emoji": "🔵", "mapa": "Shadow Abyss",
        "min_h": 7, "max_h": 8, "imagen": "https://i.imgur.com/YzJiH1T.gif"
    },
    "kharzul loren 1": {
        "nombre": "Kharzul 1", "emoji": "🔵", "mapa": "Loren Ruins",
        "min_h": 7, "max_h": 8, "imagen": "https://i.imgur.com/YzJiH1T.gif"
    },
    "kharzul loren 2": {
        "nombre": "Kharzul 2", "emoji": "🔵", "mapa": "Loren Ruins",
        "min_h": 7, "max_h": 8, "imagen": "https://i.imgur.com/YzJiH1T.gif"
    },
    "kharzul loren 3": {
        "nombre": "Kharzul 3", "emoji": "🔵", "mapa": "Loren Ruins",
        "min_h": 7, "max_h": 8, "imagen": "https://i.imgur.com/YzJiH1T.gif"
    },
}

INVASION_HORARIOS = [(2,30),(6,30),(10,30),(14,30),(18,30),(22,30)]
INVASION_IMG = "https://i.imgur.com/oGc9qdV.gif"
CANAL_ID_FIJO = None  # Se setea automáticamente al primer !mate

def load_bosses():
    if os.path.exists(BOSSES_FILE):
        with open(BOSSES_FILE) as f:
            return json.load(f)
    return {}

def save_bosses(data):
    with open(BOSSES_FILE, "w") as f:
        json.dump(data, f, indent=2)

bosses = load_bosses()

def tiempo_str(secs):
    if secs <= 0:
        return "¡AHORA!"
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    return f"{h}h {m}m" if h > 0 else f"{m}m"

def proxima_invasion():
    now = datetime.now(VE_OFFSET)
    for h, m in sorted(INVASION_HORARIOS):
        c = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if c > now:
            return c
    fh, fm = INVASION_HORARIOS[0]
    return (now + timedelta(days=1)).replace(hour=fh, minute=fm, second=0, microsecond=0)

def get_canal_id():
    for b in bosses.values():
        if b.get("canal_id"):
            return b["canal_id"]
    return None

class BossView(View):
    def __init__(self, boss_key):
        super().__init__(timeout=None)
        self.boss_key = boss_key

    @discord.ui.button(label="⚔️ Maté", style=discord.ButtonStyle.danger, custom_id="mate_btn")
    async def mate_btn(self, interaction: discord.Interaction, button: Button):
        key = self.boss_key
        catalogo = BOSS_CATALOG.get(key)
        if not catalogo or key not in bosses:
            await interaction.response.send_message("❌ Timer no encontrado.", ephemeral=True)
            return

        muerte_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        respawn_min = muerte_utc + timedelta(hours=catalogo["min_h"])
        respawn_max = muerte_utc + timedelta(hours=catalogo["max_h"])

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
        rmin_ve = respawn_min.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        rmax_ve = respawn_max.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)

        embed = discord.Embed(
            title=f"💀 {catalogo['emoji']} {catalogo['nombre']} — {catalogo['mapa']}",
            description="**VENTANA OBLIGATORIA DE SPAWN**",
            color=0xFF4444
        )
        embed.add_field(name="⏰ Muerte (VE)", value=muerte_ve.strftime("%H:%M"), inline=True)
        embed.add_field(name="🟢 Mínimo (VE)", value=rmin_ve.strftime("%H:%M"), inline=True)
        embed.add_field(name="🔴 Máximo (VE)", value=rmax_ve.strftime("%H:%M"), inline=True)
        embed.add_field(name="👤 Confirmado por", value=interaction.user.name, inline=False)
        embed.set_image(url=catalogo["imagen"])
        embed.set_footer(text=f"Ventana: {catalogo['min_h']}h – {catalogo['max_h']}h | Se reinicia automáticamente si no se confirma")
        await interaction.response.send_message(embed=embed, view=BossView(key))

    @discord.ui.button(label="🔁 Repetir horario", style=discord.ButtonStyle.success, custom_id="repetir_btn")
    async def repetir_btn(self, interaction: discord.Interaction, button: Button):
        key = self.boss_key
        catalogo = BOSS_CATALOG.get(key)
        if not catalogo or key not in bosses or not bosses[key].get("respawn_min_utc"):
            await interaction.response.send_message("❌ No hay muerte registrada.", ephemeral=True)
            return
        boss = bosses[key]
        rmin_ve = datetime.fromisoformat(boss["respawn_min_utc"]).replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        rmax_ve = datetime.fromisoformat(boss["respawn_max_utc"]).replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        embed = discord.Embed(
            title=f"🔁 {catalogo['emoji']} {catalogo['nombre']} — {catalogo['mapa']}",
            description="**Repitiendo último horario**",
            color=0x00AA00
        )
        embed.add_field(name="🟢 Mínimo (VE)", value=rmin_ve.strftime("%H:%M"), inline=True)
        embed.add_field(name="🔴 Máximo (VE)", value=rmax_ve.strftime("%H:%M"), inline=True)
        embed.set_image(url=catalogo["imagen"])
        await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    for key in BOSS_CATALOG:
        bot.add_view(BossView(key))
    check_timers.start()
    check_invasion.start()

@bot.command(name="mate")
async def registrar_muerte(ctx, *, nombre: str):
    key = nombre.lower().strip()
    catalogo = BOSS_CATALOG.get(key)
    if not catalogo:
        lista = "\n".join([f"• `!mate {k}`" for k in BOSS_CATALOG.keys()])
        await ctx.send(f"❌ Boss no encontrado. Opciones:\n{lista}")
        return

    muerte_utc = datetime.now(timezone.utc).replace(tzinfo=None)
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
    rmin_ve = respawn_min.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
    rmax_ve = respawn_max.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)

    embed = discord.Embed(
        title=f"💀 {catalogo['emoji']} {catalogo['nombre']} — {catalogo['mapa']}",
        description="**VENTANA OBLIGATORIA DE SPAWN**",
        color=0xFF4444
    )
    embed.add_field(name="⏰ Muerte (VE)", value=muerte_ve.strftime("%H:%M"), inline=True)
    embed.add_field(name="🟢 Mínimo (VE)", value=rmin_ve.strftime("%H:%M"), inline=True)
    embed.add_field(name="🔴 Máximo (VE)", value=rmax_ve.strftime("%H:%M"), inline=True)
    embed.add_field(name="👤 Registrado por", value=ctx.author.name, inline=False)
    embed.set_image(url=catalogo["imagen"])
    embed.set_footer(text=f"Ventana: {catalogo['min_h']}h – {catalogo['max_h']}h | Se reinicia automáticamente si no se confirma")
    await ctx.send(embed=embed, view=BossView(key))

@bot.command(name="timers")
async def ver_timers(ctx):
    if not bosses:
        await ctx.send("📭 No hay timers activos.")
        return
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    embed = discord.Embed(title="⏱️ Timers Activos", color=0xFFAA00)
    embed.set_footer(text="Hora Venezuela (UTC-4)")
    activos = []
    for key, boss in bosses.items():
        if not boss.get("respawn_min_utc"):
            continue
        cat = BOSS_CATALOG.get(key, {})
        rmin = datetime.fromisoformat(boss["respawn_min_utc"])
        rmax = datetime.fromisoformat(boss["respawn_max_utc"])
        diff_min = (rmin - now).total_seconds()
        diff_max = (rmax - now).total_seconds()
        rmin_ve = rmin.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        rmax_ve = rmax.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
        if diff_max < 0:
            status = "🟢 VENTANA CERRADA"
        elif diff_min < 0:
            status = f"🚨 EN VENTANA — máx. {rmax_ve.strftime('%H:%M')}"
        else:
            status = f"🔴 {tiempo_str(diff_min)} — {rmin_ve.strftime('%H:%M')} a {rmax_ve.strftime('%H:%M')}"
        nombre = f"{cat.get('emoji','')} {cat.get('nombre', key)} [{cat.get('mapa','')}]"
        activos.append((diff_min, nombre, status))
    activos.sort()
    for _, nombre, status in activos:
        embed.add_field(name=nombre, value=status, inline=False)
    prox = proxima_invasion()
    diff_inv = (prox - datetime.now(VE_OFFSET)).total_seconds()
    embed.add_field(name="⚔️ Invasión Dorada", value=f"Próxima {prox.strftime('%H:%M')} VE — en {tiempo_str(diff_inv)}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="bosses")
async def lista_bosses(ctx):
    embed = discord.Embed(title="📋 Bosses disponibles", color=0x7777FF)
    for key, cat in BOSS_CATALOG.items():
        embed.add_field(
            name=f"{cat['emoji']} {cat['nombre']} — {cat['mapa']}",
            value=f"Respawn: {cat['min_h']}h–{cat['max_h']}h | `!mate {key}`",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command(name="borrar")
async def borrar_timer(ctx, *, nombre: str):
    key = nombre.lower().strip()
    if key in bosses:
        del bosses[key]
        save_bosses(bosses)
        cat = BOSS_CATALOG.get(key, {})
        await ctx.send(f"✅ Timer de **{cat.get('nombre', key)}** [{cat.get('mapa','')}] eliminado.")
    else:
        await ctx.send(f"❌ No encontré el timer de `{key}`")

@bot.command(name="limpiar")
async def limpiar_timers(ctx):
    bosses.clear()
    save_bosses(bosses)
    await ctx.send("🧹 Todos los timers han sido eliminados.")

@tasks.loop(minutes=1)
async def check_timers():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for key, boss in list(bosses.items()):
        if not boss.get("respawn_min_utc"):
            continue
        cat = BOSS_CATALOG.get(key)
        if not cat:
            continue
        rmin = datetime.fromisoformat(boss["respawn_min_utc"])
        rmax = datetime.fromisoformat(boss["respawn_max_utc"])
        diff_min = (rmin - now).total_seconds()
        diff_max = (rmax - now).total_seconds()
        canal = bot.get_channel(boss["canal_id"])
        if not canal:
            continue
        nombre = f"{cat['emoji']} {cat['nombre']} [{cat['mapa']}]"

        if 1740 <= diff_min <= 1800 and not boss.get("notif_30"):
            bosses[key]["notif_30"] = True
            save_bosses(bosses)
            await canal.send(f"⚠️ **{nombre}** spawna en **30 minutos**")

        elif 540 <= diff_min <= 600 and not boss.get("notif_10"):
            bosses[key]["notif_10"] = True
            save_bosses(bosses)
            await canal.send(f"⚠️ **{nombre}** spawna en **10 minutos**")

        elif -60 <= diff_min <= 0 and not boss.get("notif_spawn"):
            bosses[key]["notif_spawn"] = True
            save_bosses(bosses)
            rmax_ve = rmax.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
            embed = discord.Embed(
                title=f"🚨 {nombre} — ¡VENTANA ABIERTA!",
                description=f"¡El boss **puede spawnear ahora**!\nVentana cierra a las **{rmax_ve.strftime('%H:%M')} VE**",
                color=0xFF0000
            )
            embed.set_image(url=cat["imagen"])
            await canal.send(embed=embed, view=BossView(key))

        elif diff_max <= 0 and not boss.get("auto_reinicio"):
            bosses[key]["auto_reinicio"] = True
            save_bosses(bosses)
            nueva_muerte = now
            nuevo_min = nueva_muerte + timedelta(hours=cat["min_h"])
            nuevo_max = nueva_muerte + timedelta(hours=cat["max_h"])
            nmin_ve = nuevo_min.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
            nmax_ve = nuevo_max.replace(tzinfo=timezone.utc).astimezone(VE_OFFSET)
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
                title=f"🔄 {nombre} — Reinicio automático",
                description="Nadie confirmó la muerte. Timer reiniciado automáticamente.",
                color=0xFFAA00
            )
            embed.add_field(name="🟢 Próximo mínimo (VE)", value=nmin_ve.strftime("%H:%M"), inline=True)
            embed.add_field(name="🔴 Próximo máximo (VE)", value=nmax_ve.strftime("%H:%M"), inline=True)
            embed.set_image(url=cat["imagen"])
            await canal.send(embed=embed, view=BossView(key))

@tasks.loop(minutes=1)
async def check_invasion():
    now_ve = datetime.now(VE_OFFSET)
    prox = proxima_invasion()
    diff = (prox - now_ve).total_seconds()
    if 540 <= diff <= 600:
        canal_id = get_canal_id()
        if canal_id:
            canal = bot.get_channel(canal_id)
            if canal:
                embed = discord.Embed(
                    title="⚔️ ¡INVASIÓN DORADA EN 10 MINUTOS!",
                    description=f"La invasión comienza a las **{prox.strftime('%H:%M')} VE**",
                    color=0xFFD700
                )
                embed.set_image(url=INVASION_IMG)
                await canal.send(embed=embed)

bot.run(TOKEN)

