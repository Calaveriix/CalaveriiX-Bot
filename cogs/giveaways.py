import asyncio
import random
from discord.ext import commands

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="giveaway")
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx, seconds: int, *, prize: str):
        if seconds <= 0:
            return await ctx.send("❌ Debes indicar segundos mayores a 0.")
        msg = await ctx.send(f"🎉 **SORTEO INICIADO** 🎉\nPremio: **{prize}**\nDuración: **{seconds} segundos**\nReacciona con 🎉 para participar.")
        await msg.add_reaction("🎉")
        await asyncio.sleep(seconds)
        msg = await ctx.channel.fetch_message(msg.id)
        users = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user)
                break
        if not users:
            return await ctx.send("😢 Nadie participó en el sorteo.")
        winner = random.choice(users)
        await ctx.send(f"🏆 Ganador de **{prize}**: {winner.mention}")

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
