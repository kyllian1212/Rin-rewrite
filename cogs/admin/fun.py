import discord
from discord import app_commands
from discord.ext import commands
import random

from main import db

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fiftyfifty", description="Randomly chooses between 'Yes' or 'No', with an exact 50% probability on each side")
    async def fiftyfifty(self, interaction: discord.Interaction):
        random_variable = random.randint(0, 999)
        if 0 <= random_variable <= 499:
            await interaction.response.send_message(content="50/50 choice: **YES**")
        if 500 <= random_variable <= 999:
            await interaction.response.send_message(content="50/50 choice: **NO**")
    
    @app_commands.command(name="roll", description="Rolls a dice (1d6 by default)")
    async def roll(self, interaction: discord.Interaction, number_of_dice: int = 1, number_of_sides: int = 6):
        number_of_rolls = 0
        results = []
        while number_of_rolls < number_of_dice:
            results.append(random_variable = random.randint(1, number_of_sides))
            number_of_rolls += 1
        await interaction.response.send_message(number_of_dice + "d" + number_of_sides + " roll result: **" + str(random_variable) + "**")

async def setup(bot):
    await bot.add_cog(FunCog(bot), guilds = [discord.Object(id = 849034525861740571)])