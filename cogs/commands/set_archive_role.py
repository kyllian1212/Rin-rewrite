"""
The Archive Role Module
"""

import discord
from discord import app_commands
from discord.ext import commands
import templates.embeds as embeds

from main import db


class SetArchiveRoleCog(commands.Cog):
    """The archive role cog

    Args:
        commands (Cog): the base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="set_archive_role",
        description="Sets the role for which members will be able to see archived channels",
    )
    @app_commands.describe(role="The role for archived channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_archive_role(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        """Sets the archive role for archived channels

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            role (discord.Role): the archive role
        """
        try:
            await interaction.response.defer(ephemeral=True)
            archive_role_set = db.fetchone_singlecolumn(
                0,
                "SELECT archive_role_id FROM bot_archive_role WHERE guild_id = ?",
                interaction.guild_id,
            )
            if archive_role_set is None:
                db.update_db(
                    "INSERT INTO bot_archive_role VALUES(?,?)",
                    interaction.guild_id,
                    role.id,
                )
            else:
                db.update_db(
                    "UPDATE bot_archive_role SET archive_role_id = ? WHERE guild_id = ?",
                    role.id,
                    interaction.guild_id,
                )
            await interaction.followup.send(
                embed=discord.Embed(
                    description="Archive role successfully set to <@&"
                    + str(role.id)
                    + ">!",
                    color=0x00AEFF,
                ),
            )
        except:
            await embeds.error_executing_command(
                interaction, title_detail="setting or updating the archive role."
            )
            raise

    @set_archive_role.error
    async def error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """checks for missing permissions error

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            error (app_commands.AppCommandError): the error that has been thrown
        """
        if isinstance(error, app_commands.MissingPermissions):
            await embeds.missing_permissions(interaction)


async def setup(bot: commands.Bot):
    """initializes the set archive role cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(SetArchiveRoleCog(bot))
