from distutils.log import error
import discord
import templates.embeds as embeds
from discord import app_commands
from discord.ext import commands
import os
import traceback

from main import db

class RebuildDatabaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rebuild_database", description="Deletes the entire database and rebuilds it")
    @app_commands.checks.has_permissions(administrator=True)
    async def rebuild_database(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            if (interaction.user.id == 171000921927581696):
                view = RebuildDatabaseButtons()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Are you sure you want to rebuild the database?", 
                        description="This will cause the admin configuration of every server as well as the song library to be entirely destroyed, make sure to have a backup!! This cannot be undone", 
                        color=0xff0000),
                    ephemeral=True,
                    view=view)
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Only the bot owner can run this command!", 
                        color=0xff0000),
                    ephemeral=True)
        except:
            await embeds.error_executing_command(interaction)
            raise

    @rebuild_database.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await embeds.missing_permissions(interaction)

class RebuildDatabaseButtons(discord.ui.View):
    def __init__(self, *, timeout=60):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Rebuild database", style=discord.ButtonStyle.danger)
    async def rebuild_database_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        error = False
        button.disabled = True

        try:
            await interaction.followup.edit(embed=discord.Embed(
                    title="Rebuilding database...", 
                    description="This might take some time.", 
                    color=0xff0000),
                view = self)

            db.drop_all_tables()
            db.build_database()

            await interaction.followup.edit(embed=discord.Embed(
                    title="Database rebuilt successfully!", 
                    color=0xff0000),
                view = self)
        except Exception as err:
            error = True
            await interaction.followup.edit(embed=discord.Embed(
                    title="Fatal error while rebuilding database.", description="Bot will clear all tables and shutdown for safety, please restart the bot to reattempt to build the database.", 
                    color=0xff0000),
                view = self)
            if error == True:
                print(traceback.format_exc())
                os._exit(-1)
            

async def setup(bot):
    await bot.add_cog(RebuildDatabaseCog(bot))