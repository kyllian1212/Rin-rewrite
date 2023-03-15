from operator import truediv
import discord
from discord.ext import commands
from discord.utils import get
from datetime import datetime

from main import db

class MembersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        log_channel_id = db.fetchone_singlecolumn(0, "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?", guild.id)

        if log_channel_id != None:
            log_channel = await self.bot.fetch_channel(log_channel_id)
            now = str(datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)"))
            guild = self.bot.get_guild(guild.id)

            banned_embed = discord.Embed(title="A member has been banned", description=f"**User tag:** <@{user.id}>\n**Username when banned:** {user.name}#{user.discriminator}", color=0xff0000)
            banned_embed.set_thumbnail(url=user.avatar.url)
            banned_embed.set_footer(text=f"User ID: {str(user.id)}  •  {now}")

            await log_channel.send(embed=banned_embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        log_channel_id = db.fetchone_singlecolumn(0, "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?", guild.id)

        if log_channel_id != None:
            log_channel = await self.bot.fetch_channel(log_channel_id)
            now = str(datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)"))
            guild = self.bot.get_guild(guild.id)

            banned_embed = discord.Embed(title="A user has been unbanned", description=f"**User tag:** <@{user.id}>\n**Username when unbanned:** {user.name}#{user.discriminator}", color=0x00aeff)
            banned_embed.set_thumbnail(url=user.avatar.url)
            banned_embed.set_footer(text=f"User ID: {str(user.id)}  •  {now}")

            await log_channel.send(embed=banned_embed)

async def setup(bot):
    await bot.add_cog(MembersCog(bot))