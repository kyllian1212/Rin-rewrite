import discord
from discord import app_commands
from discord.ext import commands

from main import db

class SetArchiveRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_archive_role", description="Sets the role for which members will be able to see archived channels")
    @app_commands.describe(role='The role for archived channels')
    @app_commands.checks.has_permissions(administrator=True) #sort out error next time
    async def set_archive_role(self, interaction: discord.Interaction, role: discord.Role):
        try:
            log_channel_set = db.fetchone("SELECT archive_role_id FROM bot_archive_role WHERE server_id = ?", interaction.guild_id)
            if log_channel_set == None:
                db.update_db("INSERT INTO bot_archive_role VALUES(?,?)", interaction.guild_id, role.id)
            else:
                db.update_db("UPDATE bot_archive_role SET archive_role_id = ? WHERE server_id = ?", role.id, interaction.guild_id)
        except:
            interaction.response.send_message(embed=discord.Embed(title="there was an error setting or updating the archive role. please try again or contact the bot owner if you see this again", color=0xff0000), ephemeral=True)
            raise
        await interaction.response.send_message(embed=discord.Embed(title="log channel successfully set to @" + role.name, color=0x00aeff), ephemeral=True)

async def setup(bot):
    await bot.add_cog(SetArchiveRoleCog(bot), guilds = [discord.Object(id = 849034525861740571)])