import discord
from discord.ext import commands

class QuickAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Estado", style=discord.ButtonStyle.blurple)
    async def estado(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot = interaction.client
        guilds = len(bot.guilds)
        users = sum(g.member_count or 0 for g in bot.guilds)
        embed = discord.Embed(title="💀 Estado Rápido")
        embed.add_field(name="Servidores", value=str(guilds), inline=True)
        embed.add_field(name="Usuarios", value=str(users), inline=True)
        embed.add_field(name="Latencia", value=f"{round(bot.latency * 1000)}ms", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Ayuda", style=discord.ButtonStyle.secondary)
    async def ayuda(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Comandos útiles: `!help`, `!ticketpanel`, `!balance`, `!daily`, `!shop`, `!rank`, `!giveaway`, `!suggest`", ephemeral=True)

class AdminPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel")
    @commands.has_permissions(administrator=True)
    async def panel(self, ctx):
        embed = discord.Embed(title="💀 Panel CalaveriiX", description="Panel rápido de administración.")
        embed.add_field(name="Setup recomendado", value="`!setwelcome` `!setlogs` `!setautorole` `!setstaffrole` `!ticketsetup` `!settranscripts` `!setsuggestions` `!toggleautomod`", inline=False)
        await ctx.send(embed=embed, view=QuickAdminView())

async def setup(bot):
    await bot.add_cog(AdminPanel(bot))
