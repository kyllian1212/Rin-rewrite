from distutils.log import error
import discord
from discord import app_commands
from discord.ext import commands

from main import db

class SongLibraryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rebuild_song_library", description="Deletes the entire song library and rebuilds it")
    @app_commands.checks.has_permissions(administrator=True)
    async def rebuild_song_library(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message(embed=discord.Embed(
                    title="rebuilding song library...", 
                    description="this might take some time.", 
                    color=0xff0000), ephemeral=True)
            db.clear_song_library()
            db.create_song_library()
            await interaction.edit_original_response(embed=discord.Embed(
                    title="song library rebuilt successfully!", 
                    color=0xff0000))
        except:
            await interaction.edit_original_response(embed=discord.Embed(
                    title="ERROR THE BOT IS GOING TO EXPLODE (jk)", 
                    color=0xff0000))
            raise


async def setup(bot):
    await bot.add_cog(SongLibraryCog(bot), guilds = [discord.Object(id = 849034525861740571)])