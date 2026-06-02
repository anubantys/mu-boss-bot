import discord
from discord.ext import commands, tasks
import json, os, asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

BOSSES_FILE = "bosses.json"

def load_bosses():
    if os.path.exists(BOSSES_FILE):
        with open(BOSSES_FILE) as f:
            return json.load(f)
    return {}

def save_bosses(data):
    with open(BOSSES_FILE, "w") as f:
        json.dump(data, f, indent=2)

bosses = load_bosses()

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    check_timers.start()

@bot.command(name="muerto")
async def boss_muerto(ctx, *, nombre: str):
    """Registra la muerte de un boss. Uso: !muerto Yellow Goblin s1 11h"""
    parts = nombre.rsplit(" ", 2)
    if len(parts) < 3:
        await ctx.send("❌ Uso: `!muerto   h`\nEjemplo: `!muerto Yellow Goblin s1 11h`")
        return
    
    horas_str = parts[-1]
    servidor = parts[-2]
    boss_name = parts[-3] if len(parts) == 3 else " ".join(parts[:-2])
    
    try:
        horas = float(horas_str.replace("h", ""))
    except:
        await ctx.send("❌ Formato de horas inválido. Ejemplo: `11h` o `11.5h`")
        return
    
    respawn_time = datetime.utcnow() + timedelta(hours=horas)
    key = f"{boss_name}_{servidor}".lower().replace(" ", "_")
    
    bosses[key] = {
        "nombre": boss_name,
        "servidor": servidor,
        "respawn_utc": respawn_time.isoformat(),
        "horas": horas,
        "canal_id": ctx.channel.id
    }
    save_bosses(bosses)
    
    embed = discord.Embed(
        title="💀 Boss Muerto Registrado",
        color=0xFF4444
    )
    embed.add_field(name="Boss", value=boss_name, inline=True)
    embed.add_field(name="Servidor", value=servidor, inline=True)
    embed.add_field(name="Respawn en", value=f"{horas}h", inline=True)
    embed.add_field(name="Hora estimada (UTC)", value=respawn_time.strftime("%H:%M"), inline=False)
    embed.set_footer(text=f"Registrado por {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command(name="timers")
async def ver_timers(ctx):
    """Muestra todos los timers activos"""
    if not bosses:
        await ctx.send("📭 No hay timers activos. Usa `!muerto   h` para agregar uno.")
        return
    
    now = datetime.utcnow()
    embed = discord.Embed(title="⏱️ Timers de Bosses Activos", color=0xFFAA00)
    
    activos = []
    for key, boss in bosses.items():
        respawn = datetime.fromisoformat(boss["respawn_utc"])
        diff = respawn - now
        total_mins = int(diff.total_seconds() / 60)
        
        if total_mins < 0:
            status = "🟢 ¡SPAWNEADO! (confirmar con !muerto)"
        elif total_mins < 60:
            status = f"🟡 {total_mins} minutos"
        else:
            horas_rest = total_mins // 60
            mins_rest = total_mins % 60
            status = f"🔴 {horas_rest}h {mins_rest}m"
        
        activos.append((total_mins, boss["nombre"], boss["servidor"], status))
    
    activos.sort()
    for _, nombre, servidor, status in activos:
        embed.add_field(name=f"{nombre} [{servidor}]", value=status, inline=False)
    
    embed.set_footer(text="Usa !borrar   para eliminar un timer")
    await ctx.send(embed=embed)

@bot.command(name="borrar")
async def borrar_timer(ctx, *, nombre: str):
    """Borra un timer. Uso: !borrar Yellow Goblin s1"""
    parts = nombre.rsplit(" ", 1)
    if len(parts) < 2:
        await ctx.send("❌ Uso: `!borrar  `")
        return
    servidor = parts[-1]
    boss_name = parts[-2] if len(parts) == 2 else " ".join(parts[:-1])
    key = f"{boss_name}_{servidor}".lower().replace(" ", "_")
    
    if key in bosses:
        del bosses[key]
        save_bosses(bosses)
        await ctx.send(f"✅ Timer de **{boss_name}** [{servidor}] eliminado.")
    else:
        await ctx.send(f"❌ No encontré el timer de **{boss_name}** [{servidor}]")

@tasks.loop(minutes=1)
async def check_timers():
    now = datetime.utcnow()
    to_notify = []
    for key, boss in list(bosses.items()):
        respawn = datetime.fromisoformat(boss["respawn_utc"])
        diff_mins = int((respawn - now).total_seconds() / 60)
        if diff_mins in [30, 10, 0]:
            to_notify.append((key, boss, diff_mins))
    
    for key, boss, mins in to_notify:
        canal = bot.get_channel(boss["canal_id"])
        if canal:
            if mins == 0:
                msg = f"🚨 **{boss['nombre']}** [{boss['servidor']}] ¡ESTÁ SPAWNEANDO AHORA!"
            else:
                msg = f"⚠️ **{boss['nombre']}** [{boss['servidor']}] spawna en **{mins} minutos**"
            await canal.send(msg)

bot.run(TOKEN)