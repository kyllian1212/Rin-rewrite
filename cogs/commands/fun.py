"""Fun Module
"""

import random
import discord
from discord import app_commands
from discord.ext import commands
import templates.embeds as embeds

from main import db


class FunCog(commands.Cog):
    """Cog for all fun commands

    Args:
        commands (Cog): base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="fiftyfifty",
        description="Randomly chooses between 'Yes' or 'No', with an exact 50% probability on each side",
    )
    async def fiftyfifty(self, interaction: discord.Interaction):
        """Randomly chooses between 'Yes' or 'No', with an exact 50% probability on each side

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            random_variable = random.randint(0, 999)
            if 0 <= random_variable <= 499:
                await interaction.followup.send(content="50/50 choice: **YES**")
            if 500 <= random_variable <= 999:
                await interaction.followup.send(content="50/50 choice: **NO**")
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="roll", description="Rolls a dice (1d6 by default)")
    @app_commands.describe(
        number_of_dices="Min. 1 / Max. 100", number_of_sides="Min. 1 / Max. 100"
    )
    async def roll(
        self,
        interaction: discord.Interaction,
        number_of_dices: int = 1,
        number_of_sides: int = 6,
    ):
        """rolls a custom specified dice

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            number_of_dices (int, optional): Number of dice to roll. Defaults to 1.
            number_of_sides (int, optional): Number of sides on the dice. Defaults to 6.
        """
        try:
            await interaction.response.defer()
            if not 0 < number_of_dices < 101 or not 0 < number_of_sides < 101:
                await interaction.followup.send(
                    content="You cannot roll less than 1 dices and more than 100 dices, and the dices cannot have less than 1 side and more than 100 sides!",
                    ephemeral=True,
                )
            else:
                number_of_rolls = 0
                result = ""
                total = 0
                while number_of_rolls < number_of_dices:
                    if number_of_rolls >= 1:
                        result = result + " / "
                    random_variable = random.randint(1, number_of_sides)
                    result = result + str(random_variable)
                    total = total + random_variable
                    number_of_rolls += 1
                if number_of_dices == 1:
                    await interaction.followup.send(
                        "**"
                        + str(number_of_dices)
                        + "d"
                        + str(number_of_sides)
                        + " roll result: **"
                        + str(result)
                    )
                else:
                    await interaction.followup.send(
                        "**"
                        + str(number_of_dices)
                        + "d"
                        + str(number_of_sides)
                        + " roll result: **"
                        + str(result)
                        + "\n**Total: **"
                        + str(total)
                    )
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="october18", description="Rin")
    async def october18(self, interaction: discord.Interaction):
        """Mocks a message from the 'Dad' character from the shelter music video

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            dad_message_embed = discord.Embed(
                title="To: Rin", description="**From: Dad**", color=0x00AEFF
            )
            dad_message_embed.set_thumbnail(url=self.bot.user.avatar.url)
            dad_message_embed.add_field(
                name="Message",
                value="There was just so little time left after you were born. \nI don't know how much love I managed to pour into raising you after your mother died... \nBut your smile kept me going. (^_^) \n\nI would like to have come with you, but I couldn't. \nI wanted you to forget everything and move on... \nI knew you'd be alright. But you'll get lonely, and remember. \n\nI know you'll grow strong, and read this letter some day. \nI really wish we could have spent more time together. I'm sorry. \nYou were so young back then, too young to understand what they meant. So let me repeat... \n\nMy final words to you.",
                inline=False,
            )
            dad_message_embed.set_footer(text="19/10/2016 - 04:00:00 (JST)")
            await interaction.followup.send(embed=dad_message_embed)
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="irene", description="irene")
    async def irene(self, interaction: discord.Interaction):
        """Sends 'Irene' embed message

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            await interaction.followup.send(
                content="https://media.discordapp.net/attachments/186610204023062528/1036707347881525360/IMG_4366.jpg"
            )
        except:
            await embeds.error_executing_command(interaction)
            raise


async def setup(bot: commands.Bot):
    """initialize cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(FunCog(bot))
