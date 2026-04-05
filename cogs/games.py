import random
from discord.ext import commands
from core.database import fetchone, execute

async def ensure_user(user_id: int):
    row = await fetchone("SELECT user_id FROM economy WHERE user_id = ?", (user_id,))
    if not row:
        await execute("INSERT INTO economy (user_id, balance, bank, last_daily) VALUES (?, ?, ?, ?)", (user_id, 1000, 0, None))

async def get_wallet(user_id: int) -> int:
    await ensure_user(user_id)
    row = await fetchone("SELECT balance FROM economy WHERE user_id = ?", (user_id,))
    return int(row[0])

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="coinflip")
    async def coinflip(self, ctx, eleccion: str = None):
        if eleccion is None:
            return await ctx.send("Usa `!coinflip cara` o `!coinflip cruz`.")
        eleccion = eleccion.lower().strip()
        if eleccion not in ("cara", "cruz"):
            return await ctx.send("❌ Solo puedes elegir `cara` o `cruz`.")
        resultado = random.choice(["cara", "cruz"])
        await ctx.send(f"🪙 Salió **{resultado}**. {'¡Ganaste!' if resultado == eleccion else 'Perdiste.'}")

    @commands.command(name="dice")
    async def dice(self, ctx):
        numero = random.randint(1, 6)
        await ctx.send(f"🎲 Salió el número **{numero}**")

    @commands.command(name="slot")
    async def slot(self, ctx):
        await ensure_user(ctx.author.id)
        wallet = await get_wallet(ctx.author.id)
        cost = 100
        if wallet < cost:
            return await ctx.send("❌ Necesitas al menos $100 para jugar slot.")
        await execute("UPDATE economy SET balance = ? WHERE user_id = ?", (wallet - cost, ctx.author.id))
        emojis = ["💀", "🔥", "💎", "⚡", "🪙"]
        roll = [random.choice(emojis) for _ in range(3)]
        display = " | ".join(roll)
        if len(set(roll)) == 1:
            reward = 600
            await execute("UPDATE economy SET balance = ? WHERE user_id = ?", (wallet - cost + reward, ctx.author.id))
            return await ctx.send(f"🎰 {display}\n**JACKPOT** ganaste **${reward}**.")
        if len(set(roll)) == 2:
            reward = 200
            await execute("UPDATE economy SET balance = ? WHERE user_id = ?", (wallet - cost + reward, ctx.author.id))
            return await ctx.send(f"🎰 {display}\nGanaste **${reward}**.")
        await ctx.send(f"🎰 {display}\nNo ganaste esta vez.")

async def setup(bot):
    await bot.add_cog(Games(bot))
