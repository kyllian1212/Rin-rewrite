import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import templates.embeds as embeds

from main import db
from main import VERSION

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Makes bot info appear")
    async def info(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            now = str(datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)"))
            kyllian_user = self.bot.get_user(171000921927581696)
            info_message_embed = discord.Embed(title="Rin • Bot by " + str(kyllian_user.name) + "#" + str(kyllian_user.discriminator), description="**bot version:** *" + VERSION + "*", url="https://github.com/kyllian1212/Rin-rewrite", color=0x00aeff)
            info_message_embed.set_thumbnail(url=kyllian_user.avatar.url)
            info_message_embed.set_footer(text=now + "  •  source code available by clicking the link above", icon_url=self.bot.user.avatar.url)
            await interaction.followup.send(embed=info_message_embed)
        except:
            await embeds.error_executing_command(interaction)
            raise

async def setup(bot):
    await bot.add_cog(InfoCog(bot))