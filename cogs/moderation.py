from datetime import datetime, timezone
import discord
from discord.ext import commands
from core.database import fetchall, execute

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send("❌ Debes indicar un número mayor a 0.")
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"🧹 Se borraron **{len(deleted)-1}** mensajes.")
        await msg.delete(delay=4)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Sin razón"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member} fue expulsado. Razón: {reason}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "Sin razón"):
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member} fue baneado. Razón: {reason}")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ {user} fue desbaneado.")

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        if seconds < 0 or seconds > 21600:
            return await ctx.send("❌ El slowmode debe estar entre 0 y 21600 segundos.")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"🐢 Slowmode configurado a **{seconds}s**.")

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Canal bloqueado.")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Canal desbloqueado.")

    @commands.command(name="warn")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "Sin razón"):
        await execute("INSERT INTO warnings (guild_id, user_id, moderator_id, reason, created_at) VALUES (?, ?, ?, ?, ?)", (ctx.guild.id, member.id, ctx.author.id, reason, datetime.now(timezone.utc).isoformat()))
        await ctx.send(f"⚠️ {member.mention} recibió una advertencia. Razón: {reason}")

    @commands.command(name="warnings")
    async def warnings(self, ctx, member: discord.Member):
        rows = await fetchall("SELECT moderator_id, reason, created_at FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC", (ctx.guild.id, member.id))
        if not rows:
            return await ctx.send(f"✅ {member.mention} no tiene advertencias.")
        embed = discord.Embed(title=f"⚠️ Warnings de {member}")
        for i, (moderator_id, reason, created_at) in enumerate(rows[:10], start=1):
            embed.add_field(name=f"#{i}", value=f"Moderador: <@{moderator_id}>\nRazón: {reason}\nFecha: {created_at}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="clearwarns")
    @commands.has_permissions(moderate_members=True)
    async def clearwarns(self, ctx, member: discord.Member):
        await execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        await ctx.send(f"🧽 Advertencias eliminadas para {member.mention}.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
