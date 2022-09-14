# main.py
# dont forget second sky countdown
# archive channel function

import os
import sqlite3
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
import logging

from cogs import botadmincommands
from cogs import botlisteners

from db import db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEST_ID = os.getenv('TEST_ID')
MADEON_ID = os.getenv('MADEON_ID')
PORTER_ID = os.getenv('PORTER_ID')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!!", intents=intents, max_messages=10000, help_command=None)

VERSION = "alpha"

@bot.event
async def on_ready():
    await bot.wait_until_ready()

    #build database if it's empty
    try:
        db.build_database()
    except Exception as err:
        print("database file not found! it probably hasn't been created automatically for some reason. please contact the bot owner. exiting...")
        os._exit(-1)

    bot.synced = False

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

    if not bot.synced:
        await bot.tree.sync(guild = discord.Object(id = 849034525861740571)) #remove guild value for global slash command (takes longer to synchronize)
        bot.synced = True

if __name__ == "__main__":
    try:
        bot.run(TOKEN, reconnect=True)
    except:
        raise
