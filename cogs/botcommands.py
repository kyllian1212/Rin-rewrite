import discord
from discord.ext import commands

class BotCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def say(self, ctx, *, arg):
        await ctx.message.delete()
        await ctx.channel.send(arg)

async def setup(bot):
    await bot.add_cog(BotCommandsCog(bot))