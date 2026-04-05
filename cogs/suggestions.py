import discord
from discord.ext import commands
from core.database import fetchone, execute

async def ensure_guild_row(guild_id: int):
    row = await fetchone("SELECT guild_id FROM guild_config WHERE guild_id = ?", (guild_id,))
    if not row:
        await execute("INSERT INTO guild_config (guild_id, welcome_channel_id, log_channel_id, staff_role_id, autorole_id, leveling_enabled, suggestion_channel_id, automod_enabled, automod_log_channel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (guild_id, None, None, None, None, 1, None, 0, None))

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setsuggestions")
    @commands.has_permissions(administrator=True)
    async def setsuggestions(self, ctx, channel: discord.TextChannel):
        await ensure_guild_row(ctx.guild.id)
        await execute("UPDATE guild_config SET suggestion_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        await ctx.send(f"✅ Canal de sugerencias configurado: {channel.mention}")

    @commands.command(name="suggest")
    async def suggest(self, ctx, *, text: str):
        row = await fetchone("SELECT suggestion_channel_id FROM guild_config WHERE guild_id = ?", (ctx.guild.id,))
        if not row or not row[0]:
            return await ctx.send("❌ No hay canal de sugerencias configurado. Usa `!setsuggestions #canal`.")
        channel = ctx.guild.get_channel(int(row[0]))
        if not channel:
            return await ctx.send("❌ El canal de sugerencias configurado no existe.")
        embed = discord.Embed(title="💡 Nueva sugerencia", description=text)
        embed.add_field(name="Autor", value=ctx.author.mention, inline=False)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await ctx.send(f"✅ Sugerencia enviada a {channel.mention}")

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
