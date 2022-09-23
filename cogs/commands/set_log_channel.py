import discord
import templates.embeds as embeds
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
            log_channel_set = db.fetchone_singlecolumn(0, "SELECT log_channel_id FROM bot_log_channel WHERE server_id = ?", interaction.guild_id)
            if log_channel_set == None:
                db.update_db("INSERT INTO bot_log_channel VALUES(?,?)", interaction.guild_id, channel.id)
            else:
                db.update_db("UPDATE bot_log_channel SET log_channel_id = ? WHERE server_id = ?", channel.id, interaction.guild_id)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="there was an error setting or updating the log channel. please try again or contact the bot owner if you see this again", color=0xff0000), ephemeral=True)
            raise
        await interaction.response.send_message(embed=discord.Embed(description="log channel successfully set to <#" + str(channel.id) + ">!", color=0x00aeff), ephemeral=True)

    @set_log_channel.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await embeds.missing_permissions(interaction)

async def setup(bot):
    await bot.add_cog(SetLogChannelCog(bot))