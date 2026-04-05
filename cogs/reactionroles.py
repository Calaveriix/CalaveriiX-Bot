import discord
from discord.ext import commands
from core.database import fetchone, execute

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rrcreate")
    @commands.has_permissions(administrator=True)
    async def rrcreate(self, ctx, channel: discord.TextChannel, emoji: str, role: discord.Role, *, content: str):
        if "|" in content:
            title, description = [x.strip() for x in content.split("|", 1)]
        else:
            title, description = "Roles", content.strip()

        embed = discord.Embed(title=title, description=description)
        embed.add_field(name="Emoji", value=emoji, inline=True)
        embed.add_field(name="Rol", value=role.mention, inline=True)

        msg = await channel.send(embed=embed)
        await msg.add_reaction(emoji)
        await execute(
            "INSERT OR REPLACE INTO reaction_roles (guild_id, channel_id, message_id, emoji, role_id) VALUES (?, ?, ?, ?, ?)",
            (ctx.guild.id, channel.id, msg.id, emoji, role.id),
        )
        await ctx.send(f"✅ Reaction role creado en {channel.mention}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None or payload.user_id == self.bot.user.id:
            return
        row = await fetchone(
            "SELECT role_id FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (payload.guild_id, payload.message_id, str(payload.emoji)),
        )
        if not row:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(int(row[0]))
        if member and role:
            try:
                await member.add_roles(role, reason="Reaction role")
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None:
            return
        row = await fetchone(
            "SELECT role_id FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (payload.guild_id, payload.message_id, str(payload.emoji)),
        )
        if not row:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(int(row[0]))
        if member and role:
            try:
                await member.remove_roles(role, reason="Reaction role")
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
