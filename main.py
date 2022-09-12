# main.py
# dont forget second sky countdown
# archive channel function

import os
import sys

import discord
from discord.ext import commands
from discord.ext.commands import bot
from dotenv import load_dotenv
from datetime import datetime
import os
import sys
import asyncio
import traceback

from cogs import botcommands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEST_ID = os.getenv('TEST_ID')
MADEON_ID = os.getenv('MADEON_ID')
PORTER_ID = os.getenv('PORTER_ID')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!!", intents=intents, max_messages=10000, help_command=None)

@bot.event
async def on_ready():
    await bot.wait_until_ready()

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

if __name__ == "__main__":
    try:
        bot.run(TOKEN, reconnect=True)
    except:
        raise
