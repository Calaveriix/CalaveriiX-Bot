import time
import random
import discord
from discord.ext import commands
from core.database import fetchone, fetchall, execute

def xp_for_next_level(level: int) -> int:
    return 100 + (level * 50)

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    async def ensure_user_level(self, guild_id: int, user_id: int):
        row = await fetchone("SELECT user_id FROM user_levels WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        if not row:
            await execute("INSERT INTO user_levels (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)", (guild_id, user_id, 0, 0))

    @commands.command(name="togglelevels")
    @commands.has_permissions(administrator=True)
    async def togglelevels(self, ctx):
        row = await fetchone("SELECT leveling_enabled FROM guild_config WHERE guild_id = ?", (ctx.guild.id,))
        if not row:
            await execute("INSERT INTO guild_config (guild_id, welcome_channel_id, log_channel_id, staff_role_id, autorole_id, leveling_enabled, suggestion_channel_id, automod_enabled, automod_log_channel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ctx.guild.id, None, None, None, None, 0, None, 0, None))
            return await ctx.send("✅ Sistema de niveles desactivado.")
        new_value = 0 if int(row[0]) == 1 else 1
        await execute("UPDATE guild_config SET leveling_enabled = ? WHERE guild_id = ?", (new_value, ctx.guild.id))
        await ctx.send(f"✅ Sistema de niveles {'activado' if new_value == 1 else 'desactivado'}.")

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await self.ensure_user_level(ctx.guild.id, member.id)
        row = await fetchone("SELECT xp, level FROM user_levels WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        xp, level = int(row[0]), int(row[1])
        embed = discord.Embed(title=f"🏆 Rank de {member.display_name}")
        embed.add_field(name="Nivel", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp}/{xp_for_next_level(level)}", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx):
        rows = await fetchall("SELECT user_id, xp, level FROM user_levels WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT 10", (ctx.guild.id,))
        if not rows:
            return await ctx.send("📉 No hay datos de niveles todavía.")
        lines = [f"**{idx}.** <@{user_id}> — Nivel {level} ({xp} XP)" for idx, (user_id, xp, level) in enumerate(rows, start=1)]
        embed = discord.Embed(title="🏅 Leaderboard", description="\n".join(lines))
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        row = await fetchone("SELECT leveling_enabled FROM guild_config WHERE guild_id = ?", (message.guild.id,))
        if row and int(row[0]) == 0:
            return
        key = (message.guild.id, message.author.id)
        now = time.time()
        if key in self.cooldowns and now - self.cooldowns[key] < 30:
            return
        self.cooldowns[key] = now
        await self.ensure_user_level(message.guild.id, message.author.id)
        row = await fetchone("SELECT xp, level FROM user_levels WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id))
        xp, level = int(row[0]), int(row[1])
        xp += random.randint(10, 20)
        needed = xp_for_next_level(level)
        if xp >= needed:
            xp -= needed
            level += 1
            await message.channel.send(f"🎉 {message.author.mention} subió a **nivel {level}**.")
        await execute("UPDATE user_levels SET xp = ?, level = ? WHERE guild_id = ? AND user_id = ?", (xp, level, message.guild.id, message.author.id))

async def setup(bot):
    await bot.add_cog(Leveling(bot))
