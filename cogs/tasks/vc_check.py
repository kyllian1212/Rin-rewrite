import discord
import asyncio
import random
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime

from main import db
from main import VERSION

class VcCheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(seconds=0.1)
    async def vccheck_task(self, interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if bot_voice_client.source == None or bot_voice_client.is_playing() == False:
            print("file is NOT playing")
            self.file_now_playing = None
            self.current_song_timestamp = 0
        elif bot_voice_client.is_paused():
            print("file is paused")
        else:
            print("file is playing")
            self.current_song_timestamp += 0.1
        print(self.current_song_timestamp)
        print(bot_voice_client.source)

async def setup(bot):
    await bot.add_cog(VcCheckCog(bot))