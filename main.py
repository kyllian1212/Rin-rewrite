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
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from db import db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEST_ID = os.getenv('TEST_ID')
MADEON_ID = os.getenv('MADEON_ID')
PORTER_ID = os.getenv('PORTER_ID')
VERSION = os.getenv('VERSION')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!!", intents=intents, max_messages=10000, help_command=None)

@bot.event
async def on_ready():
    await bot.wait_until_ready()

    #build database if it's empty
    try:
        db.build_database()
    except Exception as err:
        print(str(err))
        print("please contact the bot owner. exiting...")
        print("------------------------------------")
        print(traceback.format_exc()) #debug
        os._exit(-1)

    bot.synced = False

    for filename in os.listdir("./cogs/commands"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.commands.{filename[:-3]}")

    for filename in os.listdir("./cogs/listeners"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.listeners.{filename[:-3]}")
    
    for filename in os.listdir("./cogs/tasks"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.tasks.{filename[:-3]}")

    if not bot.synced:
        await bot.tree.sync() #remove guild value for global slash command (takes longer to synchronize)
        bot.tree.copy_global_to(guild = discord.Object(id = 849034525861740571))
        bot.synced = True
    
    if not bot.user.name == "Rin | " + VERSION and not bot.user.id == 849410467507601459:
        await bot.user.edit(username="Rin | " + VERSION)

if __name__ == "__main__":
    try:
        bot.run(TOKEN, reconnect=True)
    except:
        raise