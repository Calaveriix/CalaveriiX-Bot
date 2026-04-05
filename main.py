import os
import asyncio
import logging
from aiohttp import web
import discord
from discord.ext import commands

from core.database import init_db

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")
PORT = int(os.getenv("PORT", "8080"))

if not TOKEN:
    raise RuntimeError("Falta la variable DISCORD_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("calaveriix")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True
intents.reactions = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

EXTENSIONS = [
    "cogs.utility",
    "cogs.economy",
    "cogs.games",
    "cogs.tickets",
    "cogs.moderation",
    "cogs.welcome_logs",
    "cogs.adminpanel",
    "cogs.leveling",
    "cogs.giveaways",
    "cogs.suggestions",
    "cogs.automod",
    "cogs.reactionroles",
]

async def healthcheck_server():
    async def handle_root(request):
        return web.Response(text="CalaveriiX Bot MAX ONLINE")

    async def handle_health(request):
        return web.json_response({
            "status": "ok",
            "service": "CalaveriiX Bot MAX",
            "guilds": len(bot.guilds)
        })

    app = web.Application()
    app.add_routes([
        web.get("/", handle_root),
        web.get("/health", handle_health),
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info("Healthcheck activo en puerto %s", PORT)

@bot.event
async def on_ready():
    log.info("💀 %s conectado en %s servidores", bot.user, len(bot.guilds))
    try:
        await bot.change_presence(activity=discord.Game(name="CalaveriiX OS MAX 💀"))
    except Exception:
        log.exception("No se pudo actualizar la presencia")

@bot.event
async def setup_hook():
    await init_db()
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            log.info("Cargado: %s", ext)
        except Exception:
            log.exception("Error cargando %s", ext)

async def main():
    await healthcheck_server()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
