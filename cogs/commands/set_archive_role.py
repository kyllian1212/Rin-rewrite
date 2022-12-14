import discord
import templates.embeds as embeds
from discord import app_commands
from discord.ext import commands

from main import db

class SetArchiveRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_archive_role", description="Sets the role for which members will be able to see archived channels")
    @app_commands.describe(role='The role for archived channels')
    @app_commands.checks.has_permissions(administrator=True) 
    async def set_archive_role(self, interaction: discord.Interaction, role: discord.Role):
        try:
            archive_role_set = db.fetchone_singlecolumn(0, "SELECT archive_role_id FROM bot_archive_role WHERE server_id = ?", interaction.guild_id)
            if archive_role_set == None:
                db.update_db("INSERT INTO bot_archive_role VALUES(?,?)", interaction.guild_id, role.id)
            else:
                db.update_db("UPDATE bot_archive_role SET archive_role_id = ? WHERE server_id = ?", role.id, interaction.guild_id)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="There was an error setting or updating the archive role. Please try again or contact the bot owner if you see this again", color=0xff0000), ephemeral=True)
            raise
        await interaction.response.send_message(embed=discord.Embed(description="Archive role successfully set to <@&" + str(role.id) + ">!", color=0x00aeff), ephemeral=True)
    
    @set_archive_role.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await embeds.missing_permissions(interaction)

async def setup(bot):
    await bot.add_cog(SetArchiveRoleCog(bot))