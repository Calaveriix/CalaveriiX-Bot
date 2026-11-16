"""Integración OBS -> Discord para IMPERIO CALAVERIIX LIVE.

Configuración por variables de entorno:
OBS_HOST, OBS_PORT, OBS_PASSWORD, LIVE_ANNOUNCE_CHANNEL_ID,
LIVE_ROLE_ID (opcional), TWITCH_URL, KICK_URL, YOUTUBE_URL.
"""
import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

try:
    import obsws_python as obs
except ImportError:  # El bot puede arrancar aunque OBS no esté configurado.
    obs = None

log = logging.getLogger("calaveriix.live")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class ImperioCalaveriixLive(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.obs_host = os.getenv("OBS_HOST", "127.0.0.1")
        self.obs_port = _env_int("OBS_PORT", 4455)
        self.obs_password = os.getenv("OBS_PASSWORD", "")
        self.announce_channel_id = _env_int("LIVE_ANNOUNCE_CHANNEL_ID", 0)
        self.live_role_id = _env_int("LIVE_ROLE_ID", 0)
        self.last_live = None
        self.poll_task = None
        self._warned_obs = False

    async def cog_load(self):
        self.poll_task = asyncio.create_task(self._poll_obs(), name="calaveriix-obs-poll")

    async def cog_unload(self):
        if self.poll_task:
            self.poll_task.cancel()
            try:
                await self.poll_task
            except asyncio.CancelledError:
                pass

    def _read_obs_status(self) -> bool:
        if obs is None:
            raise RuntimeError("Falta instalar obsws-python")
        client = obs.ReqClient(
            host=self.obs_host,
            port=self.obs_port,
            password=self.obs_password,
            timeout=3,
        )
        try:
            status = client.get_stream_status()
            return bool(status.output_active)
        finally:
            disconnect = getattr(client, "disconnect", None)
            if callable(disconnect):
                disconnect()

    async def _poll_obs(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if self.announce_channel_id and self.obs_password:
                try:
                    is_live = await asyncio.to_thread(self._read_obs_status)
                    self._warned_obs = False
                    if self.last_live is None:
                        if is_live:
                            await self._announce_started()
                    elif is_live and not self.last_live:
                        await self._announce_started()
                    elif not is_live and self.last_live:
                        await self._announce_ended()
                    self.last_live = is_live
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    if not self._warned_obs:
                        log.warning("No se pudo consultar OBS (%s:%s): %s", self.obs_host, self.obs_port, exc)
                        self._warned_obs = True
            await asyncio.sleep(20)

    def _platform_links(self) -> list[str]:
        links = []
        for label, env_name in (
            ("Twitch", "TWITCH_URL"),
            ("Kick", "KICK_URL"),
            ("YouTube", "YOUTUBE_URL"),
        ):
            url = os.getenv(env_name, "").strip()
            if url:
                links.append(f"[{label}]({url})")
        return links

    async def _send_announcement(self, *, started: bool):
        channel = self.bot.get_channel(self.announce_channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(self.announce_channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                log.exception("No se pudo encontrar el canal de anuncios de directos")
                return

        if not hasattr(channel, "send"):
            log.error("LIVE_ANNOUNCE_CHANNEL_ID no apunta a un canal de mensajes")
            return

        if started:
            embed = discord.Embed(
                title="💀 ¡IMPERIO CALAVERIIX ESTÁ EN DIRECTO!",
                description="El directo acaba de comenzar. ¡Entra, saluda y forma parte del Imperio!",
                color=discord.Color.from_rgb(157, 0, 255),
            )
            links = self._platform_links()
            if links:
                embed.add_field(name="📺 Mira el directo", value=" • ".join(links), inline=False)
            embed.set_footer(text="Cyber-Skull Dark Neón • Calaveriix")
        else:
            embed = discord.Embed(
                title="💀 Directo finalizado",
                description="Gracias por acompañar al Imperio Calaveriix. ¡Nos vemos en el próximo directo!",
                color=discord.Color.from_rgb(0, 255, 255),
            )
            embed.set_footer(text="Gracias por formar parte del Imperio")

        content = f"<@&{self.live_role_id}>" if started and self.live_role_id else None
        try:
            await channel.send(content=content, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        except discord.HTTPException:
            log.exception("No se pudo publicar el aviso de directo")

    async def _announce_started(self):
        await self._send_announcement(started=True)

    async def _announce_ended(self):
        await self._send_announcement(started=False)

    @app_commands.command(name="liveestado", description="Comprueba si OBS está transmitiendo")
    async def liveestado(self, interaction: discord.Interaction):
        if not self.obs_password:
            await interaction.response.send_message(
                "⚙️ OBS aún no está configurado. Faltan OBS_PASSWORD y la conexión WebSocket.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            is_live = await asyncio.to_thread(self._read_obs_status)
        except Exception as exc:
            log.warning("Comprobación manual de OBS fallida: %s", exc)
            await interaction.followup.send(
                "❌ No pude conectar con OBS. Revisa que OBS esté abierto y que WebSocket esté activado en el puerto configurado.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            "🔴 OBS está transmitiendo." if is_live else "⚫ OBS no está transmitiendo.",
            ephemeral=True,
        )

    @app_commands.command(name="liveanunciar", description="Publica manualmente el aviso de directo")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def liveanunciar(self, interaction: discord.Interaction):
        if not self.announce_channel_id:
            await interaction.response.send_message(
                "Falta configurar LIVE_ANNOUNCE_CHANNEL_ID en las variables de entorno.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        await self._announce_started()
        await interaction.followup.send("✅ Aviso enviado al canal configurado.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ImperioCalaveriixLive(bot))
