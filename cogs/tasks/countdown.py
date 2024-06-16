import discord
import asyncio
import random
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime

from main import db
from main import VERSION

class SmileCountdownCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.smile_countdown_task.start()
        self.count = 0

    async def days_to_smile_auto(self):
        now = datetime.now()
        d1 = datetime.now()
        d2 = datetime(2024, 7, 26, 6, 0, 0)
        diff = d2-d1
        diffd = int((diff.total_seconds())/60/60/24)+1
        diffh = int((diff.total_seconds()+1)/60/60)
        diffm = int((diff.total_seconds()+1)/60)
        diffs = int((diff.total_seconds()+1))
        diffs_float = float((diff.total_seconds()+1))
        if diffs_float <= 1:
            smile_message_embed = discord.Embed(title="SMILE! :D is out!!", color=0x00aeff)
            smile_message_embed.add_field(name="placeholder to change before release", value=":3c", inline=False)
        elif diffm <= 1:
            smile_message_embed = discord.Embed(title="There are " + str(diffs) + " seconds left before SMILE! :D is released", color=0x00aeff)
        elif diffh <= 2:
            smile_message_embed = discord.Embed(title="There are " + str(diffm) + " minutes (" + str(diffs) + " seconds) left before SMILE! :D is released", color=0x00aeff)
        elif diffh < 100:
            smile_message_embed = discord.Embed(title="There are " + str(diffh) + " hours (" + str(diffm) + " minutes, " + str(diffs) + " seconds) left before SMILE! :D is released", color=0x00aeff)
        elif diffh >= 100:
            smile_message_embed = discord.Embed(title="There are " + str(diffd) + " days (" + str(diffh) + " hours, " + str(diffm) + " minutes, " + str(diffs) + " seconds) left before SMILE! :D is released", color=0x00aeff)
        smile_message_embed.set_thumbnail(url="https://pbs.twimg.com/media/GL3gAGUa4AAScOx?format=jpg&name=large")
        smile_message_embed.set_footer(text=str(now.strftime("%d/%m/%Y - %H:%M:%S")))
        await self.bot.get_guild(186610204023062528).get_channel(671792848135389184).send(embed=smile_message_embed) #will send in prd's #smile channel

    @tasks.loop(seconds=0.5)
    async def smile_countdown_task(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        dc1 = datetime.now()
        dc2 = datetime(2024, 7, 26, 6, 0, 0)
        diffc = dc2-dc1
        diffch = int((diffc.total_seconds()+1)/60/60)
        SMILE_TIME_DICT=[
            "00:00:00", "01:00:00", "02:00:00",
            "03:00:00", "04:00:00", "05:00:00",
            "06:00:00", "07:00:00", "08:00:00",
            "09:00:00", "10:00:00", "11:00:00",
            "12:00:00", "13:00:00", "14:00:00",
            "15:07:00", "16:00:00", "17:00:00",
            "18:00:00", "19:00:00", "20:00:00",
            "21:00:00", "22:00:00", "23:00:00"
        ]
        if diffch < 24:
            if current_time in SMILE_TIME_DICT:
                await SmileCountdownCog.days_to_smile_auto(self)
                await asyncio.sleep(1.5)
        elif diffch < 72:
            if current_time == SMILE_TIME_DICT[0] or current_time == SMILE_TIME_DICT[3] or current_time == SMILE_TIME_DICT[6] or current_time == SMILE_TIME_DICT[9] or current_time == SMILE_TIME_DICT[12] or current_time == SMILE_TIME_DICT[15] or current_time == SMILE_TIME_DICT[18] or current_time == SMILE_TIME_DICT[21]:
                await SmileCountdownCog.days_to_smile_auto(self)
                await asyncio.sleep(1.5)
        elif diffch < 168:
            if current_time == SMILE_TIME_DICT[0] or current_time == SMILE_TIME_DICT[6] or current_time == SMILE_TIME_DICT[12] or current_time == SMILE_TIME_DICT[18]:
                await SmileCountdownCog.days_to_smile_auto(self)
                await asyncio.sleep(1.5)
        elif diffch >= 168:
            if current_time == SMILE_TIME_DICT[0] or current_time == SMILE_TIME_DICT[12]:
                await SmileCountdownCog.days_to_smile_auto(self)
                await asyncio.sleep(1.5)
        pass

    @smile_countdown_task.before_loop
    async def before_smile_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(SmileCountdownCog(bot))