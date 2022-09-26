from os import remove
import discord
import templates.embeds as embeds
from discord import app_commands
from discord.ext import commands

from main import db

class ArchiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="archive", description="Archives this channel and puts it in the category of your choice")
    @app_commands.describe(category='The category in which the channel will be moved to')
    @app_commands.checks.has_permissions(administrator=True, manage_channels=True) 
    async def archive(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        try:
            archive_role_id = db.fetchone_singlecolumn(0, "SELECT archive_role_id FROM bot_archive_role WHERE server_id = ?", interaction.guild_id)

            if archive_role_id == None:
                await interaction.response.send_message(embed=discord.Embed(title="There are no archive role set for this server", description="Please set an archive role with the /set_archive_role command", color=0xff0000), ephemeral=True)
            else:
                archive_role = interaction.guild.get_role(int(archive_role_id))
                channel = interaction.channel
                
                permission_overwrite = discord.PermissionOverwrite()
                permission_overwrite.view_channel = True
                permission_overwrite.manage_channels = False
                permission_overwrite.manage_permissions = False
                permission_overwrite.manage_webhooks = False
                permission_overwrite.create_instant_invite = False
                permission_overwrite.send_messages = False
                permission_overwrite.send_messages_in_threads = False
                permission_overwrite.create_public_threads = False
                permission_overwrite.create_private_threads = False
                permission_overwrite.embed_links = False
                permission_overwrite.attach_files = False
                permission_overwrite.use_external_emojis = False
                permission_overwrite.use_external_stickers = False
                permission_overwrite.mention_everyone = False
                permission_overwrite.manage_messages = False
                permission_overwrite.manage_threads = False
                permission_overwrite.read_message_history = True
                permission_overwrite.send_tts_messages = False
                permission_overwrite.use_application_commands = False
                permission_overwrite.add_reactions = False

                await channel.set_permissions(target=interaction.guild.default_role, view_channel=False)
                await channel.set_permissions(target=archive_role, overwrite=permission_overwrite)
                await channel.move(beginning=True, category=category, sync_permissions=False, reason="Archive")

                await interaction.response.send_message(embed=discord.Embed(description="Channel <#" + str(interaction.channel.id) + "> successfully archived!", color=0x00aeff), ephemeral=True)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="There was an error archiving the channel. Please try again or contact the bot owner if you see this again", description="(Make sure to check the channel permissions just incase the bot has done something wrong)", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="unarchive", description="Unarchives this channel and puts it in the category of your choice")
    @app_commands.describe(category='The category in which the channel will be moved to')
    @app_commands.checks.has_permissions(administrator=True, manage_channels=True)
    async def unarchive(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        try:
            archive_role_id = db.fetchone_singlecolumn(0, "SELECT archive_role_id FROM bot_archive_role WHERE server_id = ?", interaction.guild_id)

            if archive_role_id == None:
                await interaction.response.send_message(embed=discord.Embed(title="There are no archive role set for this server", description="Please set an archive role with the /set_archive_role command", color=0xff0000), ephemeral=True)
            else:
                archive_role = interaction.guild.get_role(int(archive_role_id))
                channel = interaction.channel

                await channel.set_permissions(target=interaction.guild.default_role, view_channel=None)
                await channel.set_permissions(target=archive_role, overwrite=None)
                await channel.move(end=True, category=category, sync_permissions=False, reason="Unarchive")

                await interaction.response.send_message(embed=discord.Embed(description="Channel <#" + str(interaction.channel.id) + "> successfully unarchived!", color=0x00aeff), ephemeral=True)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="There was an error unarchiving the channel. Please try again or contact the bot owner if you see this again", description="(Make sure to check the channel permissions just incase the bot has done something wrong)", color=0xff0000), ephemeral=True)
            raise

    @archive.error
    @unarchive.error
    async def error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await embeds.missing_permissions(interaction)

async def setup(bot):
    await bot.add_cog(ArchiveCog(bot))