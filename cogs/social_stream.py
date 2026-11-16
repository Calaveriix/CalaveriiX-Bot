"""Puente Social Stream Ninja -> canal de chat de Discord.

Requiere SSN_SESSION_ID, SSN_DISCORD_CHANNEL_ID y los toggles de API
de Social Stream Ninja activados. No comparte la sesión en logs.
"""
import asyncio
import json
import logging
import os
from collections import deque

import discord
from discord import app_commands
from discord.ext import commands

try:
    import websockets
except ImportError:
    websockets = None

log = logging.getLogger("calaveriix.social_stream")


def _env_int(name: str, default: int = 0) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class SocialStreamBridge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_id = os.getenv("SSN_SESSION_ID", "").strip()
        self.channel_id = _env_int("SSN_DISCORD_CHANNEL_ID")
        self.connected = False
        self.task = None
        self._seen_ids = set()
        self._seen_order = deque(maxlen=500)

    async def cog_load(self):
        if self.session_id and self.channel_id:
            self.task = asyncio.create_task(self._listen(), name="calaveriix-ssn-listener")
        else:
            log.info("Social Stream Ninja no configurado; puente desactivado.")

    async def cog_unload(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    def _remember(self, message_id: str) -> bool:
        if not message_id:
            return True
        if message_id in self._seen_ids:
            return False
        if len(self._seen_order) == self._seen_order.maxlen:
            old = self._seen_order.popleft()
            self._seen_ids.discard(old)
        self._seen_order.append(message_id)
        self._seen_ids.add(message_id)
        return True

    async def _listen(self):
        await self.bot.wait_until_ready()
        if websockets is None:
            log.error("Social Stream Ninja: falta instalar websockets.")
            return

        uri = f"wss://io.socialstream.ninja/join/{self.session_id}/4"
        while not self.bot.is_closed():
            try:
                async with websockets.connect(
                    uri,
                    open_timeout=15,
                    close_timeout=5,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=1_048_576,
                ) as socket:
                    self.connected = True
                    log.info("Conectado al canal de chat de Social Stream Ninja.")
                    async for raw in socket:
                        try:
                            data = json.loads(raw)
                        except (json.JSONDecodeError, TypeError):
                            continue
                        if isinstance(data, dict):
                            await self._forward_message(data)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.connected = False
                log.warning("Conexión Social Stream Ninja interrumpida: %s", type(exc).__name__)
                await asyncio.sleep(10)
            finally:
                self.connected = False

    async def _forward_message(self, data: dict):
        name = str(data.get("chatname") or "").strip()
        message = str(data.get("chatmessage") or "").strip()
        if not name or not message:
            return

        message_id = str(data.get("mid") or data.get("id") or "")
        if not self._remember(message_id):
            return

        platform = str(data.get("type") or "Live").strip()[:32]
        name = discord.utils.escape_markdown(name[:80])
        message = message[:1500]

        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(self.channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                log.exception("No se pudo acceder al canal de chat de Discord.")
                return

        if not callable(getattr(channel, "send", None)):
            log.error("SSN_DISCORD_CHANNEL_ID no es un canal de texto.")
            return

        embed = discord.Embed(
            description=message,
            color=discord.Color.from_rgb(0, 255, 255),
        )
        embed.set_author(name=f"{name} • {platform}")
        embed.set_footer(text="IMPERIO CALAVERIIX • Chat en vivo")
        try:
            await channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.HTTPException:
            log.exception("No se pudo reenviar un mensaje de Social Stream Ninja.")

    @app_commands.command(
        name="ssnestado",
        description="Comprueba el estado del puente de chat Social Stream Ninja",
    )
    async def ssnestado(self, interaction: discord.Interaction):
        configured = bool(self.session_id and self.channel_id and websockets is not None)
        if not configured:
            status = "⚙️ No configurado. Revisa SSN_SESSION_ID, SSN_DISCORD_CHANNEL_ID y dependencias."
        elif self.connected:
            status = "🟢 Conectado a Social Stream Ninja; escuchando el canal 4."
        else:
            status = "🟠 Configurado, pero sin conexión activa. Se reintentará automáticamente."
        await interaction.response.send_message(status, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SocialStreamBridge(bot))
