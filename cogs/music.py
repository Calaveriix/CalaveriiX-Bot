import os
import discord
import wavelink
from discord.ext import commands


def get_player(guild: discord.Guild):
    player = guild.voice_client
    return player if isinstance(player, wavelink.Player) else None


class MusicControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    async def _player(self, interaction: discord.Interaction):
        player = get_player(interaction.guild) if interaction.guild else None
        if not player:
            await interaction.response.send_message("No hay música reproduciéndose.", ephemeral=True)
            return None
        return player

    @discord.ui.button(label="Pausar", emoji="⏸️", style=discord.ButtonStyle.secondary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._player(interaction)
        if player:
            await player.pause(True)
            await interaction.response.send_message("⏸️ Música pausada.", ephemeral=True)

    @discord.ui.button(label="Continuar", emoji="▶️", style=discord.ButtonStyle.success)
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._player(interaction)
        if player:
            await player.pause(False)
            await interaction.response.send_message("▶️ Música reanudada.", ephemeral=True)

    @discord.ui.button(label="Saltar", emoji="⏭️", style=discord.ButtonStyle.primary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._player(interaction)
        if player:
            await player.skip()
            await interaction.response.send_message("⏭️ Canción saltada.", ephemeral=True)

    @discord.ui.button(label="Detener", emoji="⏹️", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._player(interaction)
        if player:
            await player.stop()
            await player.disconnect()
            await interaction.response.send_message("⏹️ Música detenida.", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="play", description="Reproduce una canción o búsqueda")
    @app_commands.describe(query="Nombre o URL de la canción")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        if not interaction.guild:
            return await interaction.followup.send("Este comando solo funciona en servidores.")
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("Entra primero a un canal de voz.")
        if not wavelink.Pool.nodes:
            return await interaction.followup.send("Lavalink no está configurado. Añade LAVALINK_URI y LAVALINK_PASSWORD.")
        player = get_player(interaction.guild)
        if not player:
            player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        elif player.channel != interaction.user.voice.channel:
            await player.move_to(interaction.user.voice.channel)
        tracks = await wavelink.Playable.search(query)
        if not tracks:
            return await interaction.followup.send("No encontré canciones con esa búsqueda.")
        track = tracks[0]
        await player.play(track)
        embed = discord.Embed(title="🎶 Reproduciendo", description=f"[{track.title}]({track.uri})", color=discord.Color.blurple())
        await interaction.followup.send(embed=embed, view=MusicControls())

    @app_commands.command(name="pause", description="Pausa la música")
    async def pause(self, interaction: discord.Interaction):
        player = get_player(interaction.guild) if interaction.guild else None
        if not player:
            return await interaction.response.send_message("No hay música activa.", ephemeral=True)
        await player.pause(True)
        await interaction.response.send_message("⏸️ Pausada.")

    @app_commands.command(name="resume", description="Continúa la música")
    async def resume(self, interaction: discord.Interaction):
        player = get_player(interaction.guild) if interaction.guild else None
        if not player:
            return await interaction.response.send_message("No hay música activa.", ephemeral=True)
        await player.pause(False)
        await interaction.response.send_message("▶️ Reanudada.")

    @app_commands.command(name="skip", description="Salta la canción actual")
    async def skip(self, interaction: discord.Interaction):
        player = get_player(interaction.guild) if interaction.guild else None
        if not player:
            return await interaction.response.send_message("No hay música activa.", ephemeral=True)
        await player.skip()
        await interaction.response.send_message("⏭️ Saltada.")

    @app_commands.command(name="stop", description="Detiene y desconecta la música")
    async def stop(self, interaction: discord.Interaction):
        player = get_player(interaction.guild) if interaction.guild else None
        if not player:
            return await interaction.response.send_message("No hay música activa.", ephemeral=True)
        await player.stop()
        await player.disconnect()
        await interaction.response.send_message("⏹️ Música detenida.")

    @app_commands.command(name="musicpanel", description="Muestra los botones de música")
    async def musicpanel(self, interaction: discord.Interaction):
        await interaction.response.send_message("🎛️ **Panel de música CalaveriiX**", view=MusicControls())


from discord import app_commands


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
