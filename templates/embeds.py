import discord
from discord import app_commands
from discord.ext import commands

async def missing_permissions(interaction: discord.Interaction):
    await interaction.response.send_message(embed=discord.Embed(title="You do not have permission to use this command.", color=0xff0000), ephemeral=True)