import discord
from discord import app_commands
from discord.ext import commands

from main import db

class SetLogChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_log_channel", description="Sets the channel in which reported messages will go to")
    @app_commands.describe(channel='The channel in which reported messages will go to')
    @app_commands.checks.has_permissions(administrator=True) #sort out error next time
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            db.update_db("INSERT INTO bot_log_channel VALUES(?,?)", interaction.guild_id, channel.id)
        except:
            raise
        await interaction.response.send_message(content="test", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SetLogChannelCog(bot), guilds = [discord.Object(id = 849034525861740571)])