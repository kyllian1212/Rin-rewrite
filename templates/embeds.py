import discord
from discord import app_commands
from discord.ext import commands

async def missing_permissions(interaction: discord.Interaction):
    await interaction.followup.send(embed=discord.Embed(title="You do not have permission to use this command.", color=0xff0000), ephemeral=True)

async def error_executing_command(interaction: discord.Interaction, edit: bool = False, title_detail: str = "while executing the command.", extra_error_detail: str = ""):
    err_embed = discord.Embed(title=f"An error has occured {title_detail}", description=f"Please try again or contact the bot owner if you see this again. {extra_error_detail}", color=0xff0000)
    await interaction.followup.send(embed=err_embed, ephemeral=True) if edit == False else await interaction.followup.edit(embed=err_embed, ephemeral=True)