"""
Song Presence task
"""

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
        self.count = 0

    @tasks.loop()
    async def presence_task(self):
        if (
            not db.fetchone_singlecolumn(1, "SELECT * FROM bot_user_song_library")
            == None
        ):
            user_selected_song = db.fetchone_fullrow(
                "SELECT * FROM bot_user_song_library ORDER BY id ASC LIMIT 1"
            )
            db.update_db(
                "INSERT INTO bot_user_song_library_archive (user_id, artist, song_title, album, length_in_seconds) VALUES (?, ?, ?, ?, ?)",
                user_selected_song[1],
                user_selected_song[2],
                user_selected_song[3],
                user_selected_song[4],
                user_selected_song[5],
            )
            db.update_db(
                "DELETE FROM bot_user_song_library WHERE id = ?", user_selected_song[0]
            )
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=str(user_selected_song[3])
                    + " by "
                    + str(user_selected_song[2]),
                )
            )
            await asyncio.sleep(user_selected_song[5])
        else:
            number_of_songs = db.fetchone_singlecolumn(
                0, "SELECT count(*) FROM bot_default_song_library"
            )
            if not number_of_songs == 0:
                default_selected_song = db.fetchone_fullrow(
                    "SELECT * FROM bot_default_song_library WHERE id = ?",
                    random.randint(1, number_of_songs),
                )
                await self.bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.listening,
                        name=str(default_selected_song[2])
                        + " by "
                        + str(default_selected_song[1]),
                    )
                )
                await asyncio.sleep(default_selected_song[4])
            else:
                await self.bot.change_presence(activity=None)
                await asyncio.sleep(10)

    @presence_task.before_loop
    async def before_presence(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(SongPresenceCog(bot))
