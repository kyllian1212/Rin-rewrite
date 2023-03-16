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

            banned_embed = discord.Embed(title="A member has been banned", color=0xff0000)
            banned_embed.add_field(name="User tag:", value=f"<@{user.id}>")
            banned_embed.add_field(name="Username when banned:", value=f"{user.name}#{user.discriminator}")
            banned_embed.set_thumbnail(url=user.avatar.url)
            banned_embed.set_footer(text=f"User ID: {str(user.id)}  •  {now}")

            await log_channel.send(embed=banned_embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        log_channel_id = db.fetchone_singlecolumn(0, "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?", guild.id)

        if log_channel_id != None:
            log_channel = await self.bot.fetch_channel(log_channel_id)
            now = str(datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)"))

            unbanned_embed = discord.Embed(title="A user has been unbanned", color=0x00aeff)
            unbanned_embed.add_field(name="User tag:", value=f"<@{user.id}>")
            unbanned_embed.add_field(name="Username when unbanned:", value=f"{user.name}#{user.discriminator}")
            unbanned_embed.set_thumbnail(url=user.avatar.url)
            unbanned_embed.set_footer(text=f"User ID: {str(user.id)}  •  {now}")

            await log_channel.send(embed=unbanned_embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        log_channel_id = db.fetchone_singlecolumn(0, "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?", after.guild.id)

        if log_channel_id != None and before.timed_out_until != after.timed_out_until and after.timed_out_until is not None:
            log_channel = await self.bot.fetch_channel(log_channel_id)
            now = str(datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)"))

            timeout_embed = discord.Embed(title="A member has been timed out", color=0xff0000)
            timeout_embed.add_field(name="User tag:", value=f"<@{after.id}>")
            timeout_embed.add_field(name="Username when timed out:", value=f"{after.name}#{after.discriminator}")
            timeout_embed.add_field(name="Timed out until:", value=f"<t:{int(after.timed_out_until.timestamp())}:D> - <t:{int(after.timed_out_until.timestamp())}:T>", inline=False)
            timeout_embed.set_thumbnail(url=after.avatar.url)
            timeout_embed.set_footer(text=f"User ID: {str(after.id)}  •  {now}")

            await log_channel.send(embed=timeout_embed)

async def setup(bot):
    await bot.add_cog(MembersCog(bot))