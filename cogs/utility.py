import discord
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send(f"🏓 Pong! `{round(self.bot.latency * 1000)}ms`")

    @commands.command(name="status")
    async def status(self, ctx):
        guilds = len(self.bot.guilds)
        users = sum(g.member_count or 0 for g in self.bot.guilds)
        embed = discord.Embed(title="💀 Estado del Bot", description="CalaveriiX Bot está funcionando.")
        embed.add_field(name="Servidores", value=str(guilds), inline=True)
        embed.add_field(name="Usuarios", value=str(users), inline=True)
        embed.add_field(name="Latencia", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        g = ctx.guild
        embed = discord.Embed(title=f"📊 {g.name}")
        embed.add_field(name="ID", value=str(g.id), inline=True)
        embed.add_field(name="Miembros", value=str(g.member_count), inline=True)
        embed.add_field(name="Canales", value=str(len(g.channels)), inline=True)
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"👤 {member}")
        embed.add_field(name="ID", value=str(member.id), inline=False)
        embed.add_field(name="Cuenta creada", value=discord.utils.format_dt(member.created_at, style="F"), inline=False)
        embed.add_field(name="Entró al servidor", value=discord.utils.format_dt(member.joined_at, style="F") if member.joined_at else "Desconocido", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"🖼️ Avatar de {member}")
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, text: str):
        await ctx.message.delete()
        await ctx.send(text)

    @commands.command(name="poll")
    @commands.has_permissions(manage_messages=True)
    async def poll(self, ctx, *, question: str):
        embed = discord.Embed(title="📊 Encuesta", description=question)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @commands.command(name="help")
    async def help_command(self, ctx):
        p = ctx.prefix
        embed = discord.Embed(title="💀 CalaveriiX Bot MAX", description="Pack completo de comandos.")
        embed.add_field(name="Utilidad", value=f"`{p}ping` `{p}status` `{p}serverinfo` `{p}userinfo` `{p}avatar` `{p}say` `{p}poll` `{p}panel`", inline=False)
        embed.add_field(name="Economía", value=f"`{p}balance` `{p}daily` `{p}give` `{p}deposit` `{p}withdraw` `{p}shop` `{p}buy` `{p}inventory`", inline=False)
        embed.add_field(name="Admin economía", value=f"`{p}additem` `{p}removeitem`", inline=False)
        embed.add_field(name="Juegos", value=f"`{p}coinflip cara/cruz` `{p}dice` `{p}slot`", inline=False)
        embed.add_field(name="Tickets", value=f"`{p}ticketpanel` `{p}ticketsetup` `{p}setstaffrole` `{p}settranscripts`", inline=False)
        embed.add_field(name="Moderación", value=f"`{p}purge` `{p}kick` `{p}ban` `{p}unban` `{p}warn` `{p}warnings` `{p}clearwarns` `{p}slowmode` `{p}lock` `{p}unlock`", inline=False)
        embed.add_field(name="Config", value=f"`{p}setwelcome` `{p}setlogs` `{p}setautorole` `{p}togglelevels` `{p}setsuggestions` `{p}toggleautomod` `{p}setautomodlogs`", inline=False)
        embed.add_field(name="Niveles", value=f"`{p}rank` `{p}leaderboard`", inline=False)
        embed.add_field(name="Sorteos", value=f"`{p}giveaway segundos premio`", inline=False)
        embed.add_field(name="Ideas", value=f"`{p}suggest texto`", inline=False)
        embed.add_field(name="Roles por reacción", value=f"`{p}rrcreate #canal 😎 @Rol Título | descripción`", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
