import discord
from discord.ext import commands

from main import db

class OnRawReactionAddCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = await self.bot.fetch_channel(payload.channel_id)
        reacted_message = await channel.fetch_message(payload.message_id)

        if payload.member.bot == False and payload.emoji.name == '🚫':
            log_channel_id = db.fetchone("SELECT log_channel_id FROM bot_log_channel WHERE server_id = ?", payload.guild_id)

            if log_channel_id == None:
                await channel.send(
                    embed=discord.Embed(
                        title="there are no log channel set for this server", 
                        description="please set a log channel with the /set_log_channel command", 
                        color=0xff0000),
                    delete_after=10)
            elif payload.user_id == reacted_message.author.id:
                await reacted_message.delete()
            elif payload.member.guild_permissions.administrator == True or payload.member.guild_permissions.manage_messages == True:
                await channel.send(content="that person has the right perms so it should delete", delete_after=5)
            else:
                await channel.send(content="that person doesn't have the right perms so it shouldn't delete", delete_after=5)
                

            



async def setup(bot):
    await bot.add_cog(OnRawReactionAddCog(bot))