import discord
from discord import app_commands
from discord.ext import commands

class BotAdminCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def say(self, ctx, *, arg):
        await ctx.message.delete()
        await ctx.channel.send(arg)

    @app_commands.command(name="test2", description="test2")
    async def my_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Hello from test2", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BotAdminCommandsCog(bot), guilds = [discord.Object(id = 849034525861740571)])