import discord
from discord.ext import commands

from main import MADEON_ID

class BotListenersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        if payload.member.bot == False:
            print()

async def setup(bot):
    await bot.add_cog(BotListenersCog(bot))