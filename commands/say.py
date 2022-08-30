import discord
from discord.ext import commands
from discord.ext.commands import bot

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!!", intents=intents)

@bot.command()
async def say(ctx, *, arg):
    await ctx.message.delete()
    await ctx.channel.send(arg)
