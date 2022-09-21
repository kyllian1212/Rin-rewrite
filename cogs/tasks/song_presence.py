import discord
import asyncio
import random
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime

from main import db
from main import VERSION

class SongPresenceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_task.start()
        self.count = 0

    @tasks.loop()
    async def presence_task(self):
        number_of_songs = db.fetchone_singlecolumn(0, "SELECT count(*) FROM bot_default_song_library")
        selected_song = db.fetchone_fullrow("SELECT * FROM bot_default_song_library WHERE id = ?", random.randint(1, number_of_songs))
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=str(selected_song[2]) + " by " + str(selected_song[1])))
        await asyncio.sleep(selected_song[4])

    @presence_task.before_loop
    async def before_presence(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(SongPresenceCog(bot))