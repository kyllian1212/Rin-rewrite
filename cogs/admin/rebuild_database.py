from distutils.log import error
import discord
from discord import app_commands
from discord.ext import commands

from main import db

class RebuildDatabaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rebuild_database", description="Deletes the entire database and rebuilds it")
    @app_commands.checks.has_permissions(administrator=True)
    async def rebuild_database(self, interaction: discord.Interaction):
        if (interaction.user.id == 171000921927581696):
            view = RebuildDatabaseButtons()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="are you sure you want to rebuild the database?", 
                    description="this will cause the admin configuration of every server as well as the song library to be entirely destroyed, make sure to have a backup!! this cannot be undone", 
                    color=0xff0000),
                ephemeral=True,
                view=view)
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="only the bot owner can run this command!", 
                    color=0xff0000),
                ephemeral=True)

class RebuildDatabaseButtons(discord.ui.View):
    def __init__(self, *, timeout=60):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="rebuild database", style=discord.ButtonStyle.danger)
    async def rebuild_database_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(
                title="rebuilding database...", 
                description="this might take some time.", 
                color=0xff0000),
            view = self)

        db.drop_all_tables()
        db.build_database()

        await interaction.edit_original_response(embed=discord.Embed(
                title="database rebuilt successfully!", 
                color=0xff0000),
            view = self)

async def setup(bot):
    await bot.add_cog(RebuildDatabaseCog(bot), guilds = [discord.Object(id = 849034525861740571)])