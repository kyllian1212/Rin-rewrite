"""
Help module
"""
__version__ = "1.0.0"
__author__ = "kyllian1212"


import discord
from discord import app_commands
from discord.ext import commands
import templates.embeds as embeds
import pathlib



class HelpCog(commands.Cog):
    """Cog for bot help interface

    Args:
        commands (Cog): base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", 
        description="Displays help"
    )
    async def help(self, interaction: discord.Interaction):
        """displays the list of commands and arguments

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer(ephemeral=True)
            view = discord.ui.View()
            view.add_item(
                item=discord.ui.Button(
                    label="Help",
                    style=discord.ButtonStyle.blurple,
                    url="https://github.com/kyllian1212/Rin-rewrite/wiki/Command-List",
                )
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Click on the link below to display the list of commands!",
                    color=0x00AEFF,
                ),
                view=view,
            )
        except:
            await embeds.error_executing_command(interaction)
            raise


async def setup(bot: commands.Bot):
    """initialize cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(HelpCog(bot))