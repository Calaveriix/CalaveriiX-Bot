from datetime import datetime, timezone
import discord
from discord.ext import commands
from core.database import fetchone, fetchall, execute

DAILY_AMOUNT = 300

async def ensure_user(user_id: int):
    row = await fetchone("SELECT user_id FROM economy WHERE user_id = ?", (user_id,))
    if not row:
        await execute(
            "INSERT INTO economy (user_id, balance, bank, last_daily) VALUES (?, ?, ?, ?)",
            (user_id, 1000, 0, None),
        )

async def get_wallet_bank(user_id: int):
    await ensure_user(user_id)
    row = await fetchone("SELECT balance, bank FROM economy WHERE user_id = ?", (user_id,))
    return int(row[0]), int(row[1])

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="balance")
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        wallet, bank = await get_wallet_bank(member.id)
        embed = discord.Embed(title="💰 Balance")
        embed.add_field(name="Usuario", value=member.mention, inline=False)
        embed.add_field(name="Billetera", value=f"${wallet}", inline=True)
        embed.add_field(name="Banco", value=f"${bank}", inline=True)
        embed.add_field(name="Total", value=f"${wallet + bank}", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily(self, ctx):
        await ensure_user(ctx.author.id)
        row = await fetchone("SELECT balance, last_daily FROM economy WHERE user_id = ?", (ctx.author.id,))
        balance, last_daily = int(row[0]), row[1]
        now = datetime.now(timezone.utc)
        if last_daily:
            last_dt = datetime.fromisoformat(last_daily)
            elapsed = (now - last_dt).total_seconds()
            if elapsed < 86400:
                remaining = int((86400 - elapsed) // 3600)
                return await ctx.send(f"⏳ Ya reclamaste tu daily. Vuelve en aproximadamente **{max(1, remaining)}h**.")
        balance += DAILY_AMOUNT
        await execute("UPDATE economy SET balance = ?, last_daily = ? WHERE user_id = ?", (balance, now.isoformat(), ctx.author.id))
        await ctx.send(f"🎁 {ctx.author.mention}, recibiste **${DAILY_AMOUNT}** monedas. Tu balance ahora es **${balance}**.")

    @commands.command(name="give")
    async def give(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("❌ El monto debe ser mayor a 0.")
        await ensure_user(ctx.author.id)
        await ensure_user(member.id)
        author_wallet, _ = await get_wallet_bank(ctx.author.id)
        target_wallet, _ = await get_wallet_bank(member.id)
        if author_wallet < amount:
            return await ctx.send("❌ No tienes saldo suficiente en la billetera.")
        await execute("UPDATE economy SET balance = ? WHERE user_id = ?", (author_wallet - amount, ctx.author.id))
        await execute("UPDATE economy SET balance = ? WHERE user_id = ?", (target_wallet + amount, member.id))
        await ctx.send(f"✅ {ctx.author.mention} transfirió **${amount}** a {member.mention}.")

    @commands.command(name="deposit")
    async def deposit(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send("❌ Debe ser mayor a 0.")
        wallet, bank = await get_wallet_bank(ctx.author.id)
        if wallet < amount:
            return await ctx.send("❌ No tienes esa cantidad en la billetera.")
        await execute("UPDATE economy SET balance = ?, bank = ? WHERE user_id = ?", (wallet - amount, bank + amount, ctx.author.id))
        await ctx.send(f"🏦 Depositaste **${amount}** al banco.")

    @commands.command(name="withdraw")
    async def withdraw(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send("❌ Debe ser mayor a 0.")
        wallet, bank = await get_wallet_bank(ctx.author.id)
        if bank < amount:
            return await ctx.send("❌ No tienes esa cantidad en el banco.")
        await execute("UPDATE economy SET balance = ?, bank = ? WHERE user_id = ?", (wallet + amount, bank - amount, ctx.author.id))
        await ctx.send(f"💸 Retiraste **${amount}** del banco.")

    @commands.command(name="shop")
    async def shop(self, ctx):
        items = await fetchall("SELECT item_name, price, description FROM shop_items WHERE guild_id = ? ORDER BY price ASC", (ctx.guild.id,))
        if not items:
            return await ctx.send("🛒 La tienda está vacía. Usa `!additem` para agregar productos.")
        embed = discord.Embed(title="🛒 Tienda del servidor")
        for name, price, desc in items[:20]:
            embed.add_field(name=f"{name} - ${price}", value=desc or "Sin descripción", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="additem")
    @commands.has_permissions(administrator=True)
    async def additem(self, ctx, name: str, price: int, *, description: str = "Sin descripción"):
        if price <= 0:
            return await ctx.send("❌ El precio debe ser mayor a 0.")
        await execute(
            "INSERT OR REPLACE INTO shop_items (guild_id, item_name, price, description) VALUES (?, ?, ?, ?)",
            (ctx.guild.id, name.lower(), price, description),
        )
        await ctx.send(f"✅ Item agregado: **{name.lower()}** por **${price}**.")

    @commands.command(name="removeitem")
    @commands.has_permissions(administrator=True)
    async def removeitem(self, ctx, name: str):
        await execute("DELETE FROM shop_items WHERE guild_id = ? AND item_name = ?", (ctx.guild.id, name.lower()))
        await ctx.send(f"🗑️ Item eliminado: **{name.lower()}**.")

    @commands.command(name="buy")
    async def buy(self, ctx, name: str, quantity: int = 1):
        if quantity <= 0:
            return await ctx.send("❌ La cantidad debe ser mayor a 0.")
        item = await fetchone("SELECT item_name, price FROM shop_items WHERE guild_id = ? AND item_name = ?", (ctx.guild.id, name.lower()))
        if not item:
            return await ctx.send("❌ Ese item no existe en la tienda.")
        item_name, price = item
        cost = int(price) * quantity
        wallet, _ = await get_wallet_bank(ctx.author.id)
        if wallet < cost:
            return await ctx.send("❌ No tienes monedas suficientes.")
        await execute("UPDATE economy SET balance = ? WHERE user_id = ?", (wallet - cost, ctx.author.id))
        inv = await fetchone("SELECT quantity FROM user_inventory WHERE guild_id = ? AND user_id = ? AND item_name = ?", (ctx.guild.id, ctx.author.id, item_name))
        if inv:
            await execute("UPDATE user_inventory SET quantity = ? WHERE guild_id = ? AND user_id = ? AND item_name = ?", (int(inv[0]) + quantity, ctx.guild.id, ctx.author.id, item_name))
        else:
            await execute("INSERT INTO user_inventory (guild_id, user_id, item_name, quantity) VALUES (?, ?, ?, ?)", (ctx.guild.id, ctx.author.id, item_name, quantity))
        await ctx.send(f"✅ Compraste **{quantity}x {item_name}** por **${cost}**.")

    @commands.command(name="inventory")
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        items = await fetchall("SELECT item_name, quantity FROM user_inventory WHERE guild_id = ? AND user_id = ? ORDER BY item_name ASC", (ctx.guild.id, member.id))
        if not items:
            return await ctx.send(f"🎒 {member.mention} no tiene items.")
        embed = discord.Embed(title=f"🎒 Inventario de {member.display_name}")
        for item_name, quantity in items[:25]:
            embed.add_field(name=item_name, value=f"Cantidad: {quantity}", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
