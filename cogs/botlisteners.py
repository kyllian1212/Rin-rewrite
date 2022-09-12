import discord
from discord.ext import commands

class BotListenersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = bot.get_guild(payload.guild_id)
        channel = payload.channel_id

        #unfinished lol

async def setup(bot):
    await bot.add_cog(BotListenersCog(bot))