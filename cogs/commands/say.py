import discord
from discord import app_commands
from discord.ext import commands

class SayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, *, arg):
        await ctx.message.delete()
        await ctx.channel.send(arg)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def saytts(self, ctx, *, arg):
        await ctx.message.delete()
        await ctx.channel.send(arg, tts=True)

async def setup(bot):
    await bot.add_cog(SayCog(bot), guilds = [discord.Object(id = 849034525861740571)])