from dis import disco
from os import remove
import string
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from datetime import timedelta

from main import db

class TimeoutKickBanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rin_timeout", description="Times out a member (for up to 28 days)")
    @app_commands.describe(member="The member that will be timed out", reason="The reason why the member has been timed out (no reason by default)", dm="Sets if the user will be DM'd about the timeout or not (No by default)")
    @app_commands.checks.has_permissions(administrator=True, moderate_members=True) #sort out error next time
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, timeout_length_days: int = 0, timeout_length_hours: int = 0, timeout_length_minutes: int = 0, reason: str = None, dm: bool = False):
        try:
            if timeout_length_minutes + timeout_length_hours + timeout_length_minutes == 0:
                await interaction.response.send_message(embed=discord.Embed(title="you cannot timeout someone for 0 minutes", color=0xff0000), ephemeral=True)
            else:
                timeout = timedelta(days=timeout_length_days, minutes=timeout_length_minutes, hours=timeout_length_hours)
                await member.timeout(timeout, reason=reason)
                await interaction.response.send_message(embed=discord.Embed(description="<@" + str(member.id) + "> successfully timed out!", color=0x00aeff), ephemeral=True)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="there was an error timing out the person. please try again or contact the bot owner if you see this again", description="(please note that it is not possible to timeout someone for more than 28 days due to an API limitation)", color=0xff0000), ephemeral=True)
            raise

async def setup(bot):
    await bot.add_cog(TimeoutKickBanCog(bot), guilds = [discord.Object(id = 849034525861740571)])