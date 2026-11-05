import os
import logging
import discord
import wavelink
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("calaveriix.music")


class MusicControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def player_for(self, interaction):
        p = interaction.guild.voice_client if interaction.guild else None
        if not isinstance(p, wavelink.Player):
            await interaction.response.send_message("No hay música activa.", ephemeral=True)
            return None
        if not interaction.user.voice or interaction.user.voice.channel != p.channel:
            await interaction.response.send_message("Debes estar en el mismo canal de voz.", ephemeral=True)
            return None
        return p

    @discord.ui.button(label="Pausar", emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="cxmusic_pause")
    async def pause_button(self, interaction, button):
        p = await self.player_for(interaction)
        if p:
            await p.pause(True)
            await interaction.response.send_message("⏸️ Pausada.", ephemeral=True)

    @discord.ui.button(label="Seguir", emoji="▶️", style=discord.ButtonStyle.success, custom_id="cxmusic_resume")
    async def resume_button(self, interaction, button):
        p = await self.player_for(interaction)
        if p:
            await p.pause(False)
            await interaction.response.send_message("▶️ Reanudada.", ephemeral=True)

    @discord.ui.button(label="Saltar", emoji="⏭️", style=discord.ButtonStyle.primary, custom_id="cxmusic_skip")
    async def skip_button(self, interaction, button):
        p = await self.player_for(interaction)
        if p:
            await p.stop()
            await interaction.response.send_message("⏭️ Saltada.", ephemeral=True)

    @discord.ui.button(label="Detener", emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="cxmusic_stop")
    async def stop_button(self, interaction, button):
        p = await self.player_for(interaction)
        if p:
            p.queue.clear()
            await p.stop()
            await p.disconnect()
            await interaction.response.send_message("⏹️ Detenida.", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.node_ready = False

    async def cog_load(self):
        uri, password = os.getenv("LAVALINK_URI"), os.getenv("LAVALINK_PASSWORD")
        if not uri or not password:
            log.warning("Música no configurada: faltan LAVALINK_URI y LAVALINK_PASSWORD")
            return
        try:
            await wavelink.Pool.connect(client=self.bot, nodes=[wavelink.Node(uri=uri, password=password)])
            self.node_ready = True
        except Exception:
            log.exception("No se pudo conectar a Lavalink")

    @app_commands.command(name="play", description="Reproduce una canción o la agrega a la cola")
    @app_commands.describe(cancion="Nombre o URL de la canción")
    async def play(self, interaction: discord.Interaction, cancion: str):
        if not self.node_ready:
            await interaction.response.send_message("Música sin configurar: añade LAVALINK_URI y LAVALINK_PASSWORD.", ephemeral=True)
            return
        if not interaction.guild or not interaction.user.voice:
            await interaction.response.send_message("Entra primero a un canal de voz.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        channel = interaction.user.voice.channel
        p = interaction.guild.voice_client
        try:
            if not isinstance(p, wavelink.Player):
                p = await channel.connect(cls=wavelink.Player)
            elif p.channel != channel:
                await interaction.followup.send("Debes estar en el canal de voz del bot.")
                return
            found = await wavelink.Playable.search(cancion)
            if not found:
                await interaction.followup.send("No encontré esa canción.")
                return
            track = found[0]
            if p.playing:
                await p.queue.put_wait(track)
                await interaction.followup.send(f"➕ En cola: **{track.title}**")
            else:
                await p.play(track)
                await interaction.followup.send(f"🎶 Reproduciendo: **{track.title}**")
        except Exception:
            log.exception("Error en reproducción")
            await interaction.followup.send("Error al reproducir. Revisa el plugin de Lavalink.")

    @app_commands.command(name="skip", description="Salta la canción actual")
    async def skip(self, interaction: discord.Interaction):
        p = interaction.guild.voice_client if interaction.guild else None
        if not isinstance(p, wavelink.Player):
            await interaction.response.send_message("No hay música activa.", ephemeral=True)
            return
        await p.stop()
        await interaction.response.send_message("⏭️ Saltando.")

    @app_commands.command(name="queue", description="Muestra la cola")
    async def queue(self, interaction: discord.Interaction):
        p = interaction.guild.voice_client if interaction.guild else None
        if not isinstance(p, wavelink.Player) or p.queue.is_empty:
            await interaction.response.send_message("Cola vacía.")
            return
        items = [f"{i}. {t.title}" for i, t in enumerate(list(p.queue)[:10], 1)]
        await interaction.response.send_message("🎶 **Cola**\n" + "\n".join(items))

    @app_commands.command(name="musicpanel", description="Publica el panel interactivo")
    async def musicpanel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Necesitas Administrar servidor.", ephemeral=True)
            return
        await interaction.response.send_message("🎵 **CalaveriiX Music**", view=MusicControls())


async def setup(bot):
    await bot.add_cog(Music(bot))
    bot.add_view(MusicControls())
