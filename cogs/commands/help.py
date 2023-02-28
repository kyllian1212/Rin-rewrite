import discord
from discord import app_commands
from discord.ext import commands
import templates.embeds as embeds
import random

from main import db

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Displays help")
    async def help(self, interaction: discord.Interaction):
        try:
            interaction.response.defer()
            view = discord.ui.View()
            view.add_item(item=discord.ui.Button(label="Help", style=discord.ButtonStyle.blurple, url="https://github.com/kyllian1212/Rin-rewrite/wiki/Command-List"))
            await interaction.followup.send(embed=discord.Embed(title="Click on the link below to display the list of commands!", color=0x00aeff), ephemeral=True, view=view)
        except:
            await embeds.error_executing_command(interaction)
            raise

async def setup(bot):
    await bot.add_cog(HelpCog(bot))