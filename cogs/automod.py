import discord
from discord.ext import commands
from core.database import fetchone, execute

BAD_WORDS = {"puta", "mierda", "ctm", "culiao", "culiada", "weon", "weona"}

async def ensure_guild_row(guild_id: int):
    row = await fetchone("SELECT guild_id FROM guild_config WHERE guild_id = ?", (guild_id,))
    if not row:
        await execute("INSERT INTO guild_config (guild_id, welcome_channel_id, log_channel_id, staff_role_id, autorole_id, leveling_enabled, suggestion_channel_id, automod_enabled, automod_log_channel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (guild_id, None, None, None, None, 1, None, 0, None))

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="toggleautomod")
    @commands.has_permissions(administrator=True)
    async def toggleautomod(self, ctx):
        await ensure_guild_row(ctx.guild.id)
        row = await fetchone("SELECT automod_enabled FROM guild_config WHERE guild_id = ?", (ctx.guild.id,))
        current = int(row[0]) if row else 0
        new_value = 0 if current == 1 else 1
        await execute("UPDATE guild_config SET automod_enabled = ? WHERE guild_id = ?", (new_value, ctx.guild.id))
        await ctx.send(f"✅ AutoMod {'activado' if new_value == 1 else 'desactivado'}.")

    @commands.command(name="setautomodlogs")
    @commands.has_permissions(administrator=True)
    async def setautomodlogs(self, ctx, channel: discord.TextChannel):
        await ensure_guild_row(ctx.guild.id)
        await execute("UPDATE guild_config SET automod_log_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        await ctx.send(f"✅ Canal de logs de AutoMod configurado: {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        row = await fetchone("SELECT automod_enabled, automod_log_channel_id FROM guild_config WHERE guild_id = ?", (message.guild.id,))
        if not row or int(row[0]) == 0:
            return
        content = (message.content or "").lower()
        if any(word in content for word in BAD_WORDS):
            try:
                await message.delete()
            except Exception:
                return
            try:
                await message.channel.send(f"🚫 {message.author.mention}, ese mensaje fue eliminado por AutoMod.", delete_after=5)
            except Exception:
                pass
            log_channel_id = row[1]
            if log_channel_id:
                log_channel = message.guild.get_channel(int(log_channel_id))
                if log_channel:
                    embed = discord.Embed(title="🤖 AutoMod")
                    embed.add_field(name="Usuario", value=message.author.mention, inline=False)
                    embed.add_field(name="Canal", value=message.channel.mention, inline=False)
                    embed.add_field(name="Contenido", value=(message.content or "(sin texto)")[:1000], inline=False)
                    await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
