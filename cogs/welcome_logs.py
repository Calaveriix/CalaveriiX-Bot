import discord
from discord.ext import commands
from core.database import fetchone, execute

async def ensure_guild_row(guild_id: int):
    row = await fetchone("SELECT guild_id FROM guild_config WHERE guild_id = ?", (guild_id,))
    if not row:
        await execute("INSERT INTO guild_config (guild_id, welcome_channel_id, log_channel_id, staff_role_id, autorole_id, leveling_enabled, suggestion_channel_id, automod_enabled, automod_log_channel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (guild_id, None, None, None, None, 1, None, 0, None))

class WelcomeLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel):
        await ensure_guild_row(ctx.guild.id)
        await execute("UPDATE guild_config SET welcome_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        await ctx.send(f"✅ Canal de bienvenida configurado: {channel.mention}")

    @commands.command(name="setlogs")
    @commands.has_permissions(administrator=True)
    async def setlogs(self, ctx, channel: discord.TextChannel):
        await ensure_guild_row(ctx.guild.id)
        await execute("UPDATE guild_config SET log_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        await ctx.send(f"✅ Canal de logs configurado: {channel.mention}")

    @commands.command(name="setautorole")
    @commands.has_permissions(administrator=True)
    async def setautorole(self, ctx, role: discord.Role):
        await ensure_guild_row(ctx.guild.id)
        await execute("UPDATE guild_config SET autorole_id = ? WHERE guild_id = ?", (role.id, ctx.guild.id))
        await ctx.send(f"✅ Autorole configurado: {role.mention}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await ensure_guild_row(member.guild.id)
        row = await fetchone("SELECT welcome_channel_id, autorole_id FROM guild_config WHERE guild_id = ?", (member.guild.id,))
        if row:
            welcome_channel_id, autorole_id = row
            if autorole_id:
                role = member.guild.get_role(int(autorole_id))
                if role:
                    try:
                        await member.add_roles(role, reason="Autorole CalaveriiX")
                    except Exception:
                        pass
            if welcome_channel_id:
                channel = member.guild.get_channel(int(welcome_channel_id))
                if channel:
                    embed = discord.Embed(title="💀 Bienvenido/a", description=f"{member.mention} se unió a **{member.guild.name}**")
                    embed.set_thumbnail(url=member.display_avatar.url)
                    await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        row = await fetchone("SELECT log_channel_id FROM guild_config WHERE guild_id = ?", (member.guild.id,))
        if row and row[0]:
            channel = member.guild.get_channel(int(row[0]))
            if channel:
                await channel.send(f"📤 {member} salió del servidor.")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
        row = await fetchone("SELECT log_channel_id FROM guild_config WHERE guild_id = ?", (message.guild.id,))
        if row and row[0]:
            channel = message.guild.get_channel(int(row[0]))
            if channel and channel != message.channel:
                content = message.content[:1500] if message.content else "(sin texto)"
                embed = discord.Embed(title="🗑️ Mensaje eliminado", description=content)
                embed.add_field(name="Autor", value=str(message.author), inline=False)
                embed.add_field(name="Canal", value=message.channel.mention, inline=False)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return
        row = await fetchone("SELECT log_channel_id FROM guild_config WHERE guild_id = ?", (before.guild.id,))
        if row and row[0]:
            channel = before.guild.get_channel(int(row[0]))
            if channel and channel != before.channel:
                embed = discord.Embed(title="✏️ Mensaje editado")
                embed.add_field(name="Autor", value=str(before.author), inline=False)
                embed.add_field(name="Canal", value=before.channel.mention, inline=False)
                embed.add_field(name="Antes", value=(before.content or "(sin texto)")[:1000], inline=False)
                embed.add_field(name="Después", value=(after.content or "(sin texto)")[:1000], inline=False)
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeLogs(bot))
