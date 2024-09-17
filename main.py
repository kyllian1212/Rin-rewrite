"""
Main
"""

import asyncio
import logging
import os
import pathlib
import sqlite3
import sys
import traceback
from datetime import datetime

import discord
import spotipy
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import bot
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

import cogs.tasks.song_presence as songp
from db import db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('DISCORD_COMMAND_PREFIX')
TEST_ID = os.getenv('TEST_ID')
MADEON_ID = os.getenv('MADEON_ID')
PORTER_ID = os.getenv('PORTER_ID')
VERSION = os.getenv('VERSION')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
OWNER_ID = os.getenv('OWNER_ID')
BOT_ID = os.getenv("BOT_ID")
QUEUE_PAGE_LEN = os.getenv("QUEUE_PAGE_LEN")

auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, max_messages=10000, help_command=None)

class MainCog(commands.Cog):
    """Cog for managing bot and other cogs 

    Args:
        commands (Cog): default base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot
        

    @app_commands.command(name="resync", description="resync slash commands")
    async def resync(self, interaction: discord.Interaction):
        if interaction.user.id == OWNER_ID:
                await bot.tree.sync(guild = discord.Object(id = TEST_ID)) #remove guild value for global slash command (takes longer to synchronize)
                bot.tree.copy_global_to(guild = discord.Object(id = MADEON_ID))
        else:
            discord.interaction.response.send_message(embed=discord.Embed(description="you can't use this command", color=0x00aeff), ephemeral=True)
    
    @app_commands.command(name="load_extention")
    async def load_extention(self, interaction: discord.Interaction, extention:str):
        await interaction.response.defer()
        try:
            bot.load_extension(name=extention)
            interaction.followup.send("loaded `" +extention+"`")
        except:
            interaction.followup.send("failed to load `"+extention+"`")   
    
    @app_commands.command(name="reload_extention")
    async def reload_extention(self, interaction: discord.Interaction, extention:str):
        await interaction.response.defer()
        try:
            bot.reload_extension(name=extention)
            interaction.followup.send("reloaded `" +extention+"`")
        except:
            interaction.followup.send("failed to reload `"+extention+"`")      
    
    
    @app_commands.command(name="unload_extention")
    async def unload_extention(self, interaction: discord.Interaction, extention:str):
        await interaction.response.defer()
        try:
            bot.unload_extension(name=extention)
            interaction.followup.send("unloaded `" +extention+"`")
        except:
            interaction.followup.send("failed to unload `"+extention+"`") 



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
    
    #load main cog
    await bot.add_cog(MainCog(bot))
    
    
    #get py files in in (current workinh directory)/cogs/
    cogs = pathlib.Path.cwd().joinpath("cogs")
    parentslen = len(cogs.parts)-1
    glob = list(cogs.rglob("*.py"))
    for i in glob:
        dotpath = '.'.join(i.with_suffix('').parts[parentslen:])
        await bot.load_extension(dotpath)
        print("loaded "+ dotpath)
    
    
    
    if not bot.synced:
        await bot.tree.sync() #remove guild value for global slash command (takes longer to synchronize)
        print("test id is: " + TEST_ID)
        bot.tree.copy_global_to(guild = discord.Object(id = TEST_ID))
        bot.synced = True
    
    if not bot.user.name == "Rin | " + VERSION and not bot.user.id == 849410467507601459:
        await bot.user.edit(username="Rin | " + VERSION)
    songp.SongPresenceCog(bot=bot).presence_task.start()
    
if __name__ == "__main__":
    try:
        bot.run(TOKEN, reconnect=True)
    except:
        raise