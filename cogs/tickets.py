import io
import discord
from discord.ext import commands
from core.database import fetchone, execute

async def ensure_ticket_counter(guild_id: int):
    row = await fetchone("SELECT guild_id FROM ticket_counter WHERE guild_id = ?", (guild_id,))
    if not row:
        await execute("INSERT INTO ticket_counter (guild_id, last_number) VALUES (?, ?)", (guild_id, 0))

async def next_ticket_number(guild_id: int) -> int:
    await ensure_ticket_counter(guild_id)
    row = await fetchone("SELECT last_number FROM ticket_counter WHERE guild_id = ?", (guild_id,))
    current = int(row[0]) + 1
    await execute("UPDATE ticket_counter SET last_number = ? WHERE guild_id = ?", (current, guild_id))
    return current

async def get_staff_role(guild_id: int):
    row = await fetchone("SELECT staff_role_id FROM guild_config WHERE guild_id = ?", (guild_id,))
    return row[0] if row and row[0] else None

async def get_ticket_category(guild_id: int):
    row = await fetchone("SELECT category_id FROM ticket_config WHERE guild_id = ?", (guild_id,))
    return row[0] if row and row[0] else None

async def get_transcript_channel(guild_id: int):
    row = await fetchone("SELECT transcript_channel_id FROM ticket_config WHERE guild_id = ?", (guild_id,))
    return row[0] if row and row[0] else None

class TicketManageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.secondary, custom_id="calaveriix_ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        if not channel.name.startswith("cerrado-"):
            await channel.edit(name=f"cerrado-{channel.name}")
        await interaction.response.send_message("🔒 Ticket cerrado. Usa eliminar para borrarlo.", ephemeral=True)

    @discord.ui.button(label="Eliminar", style=discord.ButtonStyle.danger, custom_id="calaveriix_ticket_delete")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        guild = interaction.guild
        messages = []
        async for msg in channel.history(limit=300, oldest_first=True):
            content = msg.content or ""
            messages.append(f"[{msg.created_at}] {msg.author}: {content}")
        transcript_text = "\n".join(messages) if messages else "Sin mensajes."
        transcript_file = discord.File(io.BytesIO(transcript_text.encode("utf-8")), filename=f"{channel.name}_transcript.txt")
        transcript_channel_id = await get_transcript_channel(guild.id)
        if transcript_channel_id:
            tchan = guild.get_channel(int(transcript_channel_id))
            if tchan:
                try:
                    await tchan.send(content=f"🧾 Transcript guardado del ticket eliminado por {interaction.user.mention}", file=transcript_file)
                except Exception:
                    pass
        await interaction.response.send_message("🗑️ Eliminando ticket...", ephemeral=True)
        await channel.delete(reason=f"Ticket eliminado por {interaction.user}")

class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, custom_id="calaveriix_ticket_open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        existing = None
        for channel in guild.text_channels:
            if channel.topic and f"ticket_owner:{member.id}" in channel.topic:
                existing = channel
                break
        if existing:
            return await interaction.response.send_message(f"Ya tienes un ticket abierto: {existing.mention}", ephemeral=True)
        number = await next_ticket_number(guild.id)
        staff_role_id = await get_staff_role(guild.id)
        category_id = await get_ticket_category(guild.id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True),
        }
        if staff_role_id:
            role = guild.get_role(int(staff_role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        category = guild.get_channel(int(category_id)) if category_id else None
        channel = await guild.create_text_channel(
            name=f"ticket-{number:04d}",
            category=category if isinstance(category, discord.CategoryChannel) else None,
            overwrites=overwrites,
            topic=f"ticket_owner:{member.id}",
            reason=f"Ticket abierto por {member}"
        )
        embed = discord.Embed(title="🎫 Ticket Abierto", description=f"{member.mention}, describe tu problema o solicitud.\n\nUsa los botones para cerrar o eliminar.")
        await channel.send(content=member.mention, embed=embed, view=TicketManageView())
        await interaction.response.send_message(f"✅ Ticket creado: {channel.mention}", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketControls())
        self.bot.add_view(TicketManageView())

    @commands.command(name="ticketpanel")
    @commands.has_permissions(manage_channels=True)
    async def ticketpanel(self, ctx):
        embed = discord.Embed(title="🎟️ Soporte CalaveriiX", description="Pulsa el botón para abrir un ticket privado.")
        await ctx.send(embed=embed, view=TicketControls())

    @commands.command(name="ticketsetup")
    @commands.has_permissions(administrator=True)
    async def ticketsetup(self, ctx, category: discord.CategoryChannel = None):
        row = await fetchone("SELECT guild_id FROM ticket_config WHERE guild_id = ?", (ctx.guild.id,))
        category_id = category.id if category else None
        if row:
            await execute("UPDATE ticket_config SET category_id = ? WHERE guild_id = ?", (category_id, ctx.guild.id))
        else:
            await execute("INSERT INTO ticket_config (guild_id, category_id, transcript_channel_id) VALUES (?, ?, ?)", (ctx.guild.id, category_id, None))
        await ctx.send("✅ Categoría de tickets guardada.")

    @commands.command(name="setstaffrole")
    @commands.has_permissions(administrator=True)
    async def setstaffrole(self, ctx, role: discord.Role):
        row = await fetchone("SELECT guild_id FROM guild_config WHERE guild_id = ?", (ctx.guild.id,))
        if row:
            await execute("UPDATE guild_config SET staff_role_id = ? WHERE guild_id = ?", (role.id, ctx.guild.id))
        else:
            await execute("INSERT INTO guild_config (guild_id, welcome_channel_id, log_channel_id, staff_role_id, autorole_id, leveling_enabled, suggestion_channel_id, automod_enabled, automod_log_channel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ctx.guild.id, None, None, role.id, None, 1, None, 0, None))
        await ctx.send(f"✅ Rol de staff configurado: {role.mention}")

    @commands.command(name="settranscripts")
    @commands.has_permissions(administrator=True)
    async def settranscripts(self, ctx, channel: discord.TextChannel):
        row = await fetchone("SELECT guild_id FROM ticket_config WHERE guild_id = ?", (ctx.guild.id,))
        if row:
            await execute("UPDATE ticket_config SET transcript_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        else:
            await execute("INSERT INTO ticket_config (guild_id, category_id, transcript_channel_id) VALUES (?, ?, ?)", (ctx.guild.id, None, channel.id))
        await ctx.send(f"✅ Canal de transcripts configurado: {channel.mention}")

async def setup(bot):
    await bot.add_cog(Tickets(bot))
