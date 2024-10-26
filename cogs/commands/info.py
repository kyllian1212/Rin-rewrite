"""
Info Module
"""
__version__ = "1.0.0"
__author__ = "kyllian1212, Toxin_X"


from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
import templates.embeds as embeds

from main import VERSION
from main import get_cogs

class InfoCog(commands.Cog):
    """Cog for bot info

    Args:
        commands (Cog): default base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="info", 
        description="Makes bot info appear"
    )
    async def info(self, interaction: discord.Interaction):
        """displays the bot's metadata

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            now = str(
                datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)")
            )
            kyllian_user = self.bot.get_user(171000921927581696)
            info_message_embed = discord.Embed(
                title="Rin • Bot by "
                + str(kyllian_user.name),
                description="**bot version:** *" + VERSION + "*",
                url="https://github.com/kyllian1212/Rin-rewrite",
                color=0x00AEFF,
            )
            info_message_embed.set_thumbnail(url=kyllian_user.avatar.url)
            info_message_embed.set_footer(
                text=now + "  •  source code available by clicking the link above",
                icon_url=self.bot.user.avatar.url,
            )
            await interaction.followup.send(embed=info_message_embed)
        except:
            await embeds.error_executing_command(interaction)
            raise


    @app_commands.command(
        name="longinfo", 
        description="Makes bot info appear"
    )
    async def longinfo(self, interaction: discord.Interaction):
        """displays the bot's metadata

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            output = "**Extentions:**\n"
            extentions = self.bot.extensions
            for i in extentions:
                extention = extentions[i]
                output = output + f'-# **Name:** `{extention.__doc__.replace("\n", "")}`, **Path:** `{extention.__name__}`, **Author**: `{extention.__author__}` **Version:** `{extention.__version__}`\n'
                
            
            
            
            now = str(
                datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)")
            )
            kyllian_user = self.bot.get_user(171000921927581696)
            info_message_embed = discord.Embed(
                title="Rin • Bot by "
                + str(kyllian_user.name),
                description="**bot version:** *" + VERSION + "*\n" + output,
                url="https://github.com/kyllian1212/Rin-rewrite",
                color=0x00AEFF,
            )
            info_message_embed.set_thumbnail(url=kyllian_user.avatar.url)
            info_message_embed.set_footer(
                text=now + "  •  source code available by clicking the link above",
                icon_url=self.bot.user.avatar.url,
            )
            await interaction.followup.send(embed=info_message_embed)
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="detect_extentions", description="detects extentions (part of the info cog)")
    async def detect_extentions(self, interaction: discord.Interaction):
        extentions = self.bot.extensions
        msg= ""
        k = "❌"
        cogs = await get_cogs()
        for i in cogs:
            if i in extentions:
                k = "✅"
            else:
                k = "❌"
            msg += f"`{i}`{k}\n"
        await interaction.response.defer()
        try:

            
            await interaction.followup.send(f"detected extentions:\n{msg}")
        except:
            await interaction.followup.send("failed to detect extentions") 
                
async def setup(bot: commands.Bot):
    """initialize cog

    Args:
        bot (command.Bot): the discord bot
    """
    await bot.add_cog(InfoCog(bot))
