from dis import disco
from os import remove
import string
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from datetime import timedelta
import asyncio

from main import db

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #timeout
    @app_commands.command(name="rin_timeout", description="Times out a member (for up to 28 days) and DMs them (or not)")
    @app_commands.describe(member="The member that will be timed out", reason="The reason why the member has been timed out (no reason by default)", dm="Sets if the user will be DM'd about the timeout or not (No by default)")
    @app_commands.checks.has_permissions(administrator=True, moderate_members=True) #sort out error next time
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, timeout_length_days: int = 0, timeout_length_hours: int = 0, timeout_length_minutes: int = 0, reason: str = None, dm: bool = False):
        try:
            if timeout_length_minutes + timeout_length_hours + timeout_length_minutes == 0:
                await interaction.response.send_message(embed=discord.Embed(title="you cannot timeout someone for 0 minutes", color=0xff0000), ephemeral=True)
            else:
                timeout = timedelta(days=timeout_length_days, minutes=timeout_length_minutes, hours=timeout_length_hours)
                dm_block = False

                if dm == True:
                    try:
                        title = ""
                        description = ""
                        if reason == None:
                            title = "You have been timed out from " + interaction.guild.name + "!"
                            description = "Please make sure to follow the server rules to not get another timeout."
                        else:
                            title = "You have been timed out from " + interaction.guild.name + " for the following reason:"
                            description = "```" + reason + "```\nPlease make sure to follow the server rules to not get another timeout."
                        await member.send(embed=discord.Embed(title=title, description=description, color=0xff0000))
                    except discord.errors.Forbidden:
                        view = DMErrorTimeoutButton(user_timeout_length=timeout, member=member, reason=reason)
                        extra = ""
                        if not reason == None:
                            extra = "\n\nif you want to dm manually, here's the reason that was given: ```" + reason + "```"
                        await interaction.response.send_message(embed=discord.Embed(title="this member cannot be DM'd", description="this member either has dms disabled for unknown people, or has the bot blocked (less likely). do you want to timeout anyways without dming?" + extra, color=0xff0000), ephemeral=True, view=view)
                        dm_block = True

                if dm_block == False:
                    await member.timeout(timeout, reason=reason)
                    await interaction.response.send_message(embed=discord.Embed(description="<@" + str(member.id) + "> successfully timed out!", color=0x00aeff), ephemeral=True)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="there was an error timing out the person. please try again or contact the bot owner if you see this again", description="(please note that it is not possible to timeout someone for more than 28 days due to an API limitation)", color=0xff0000), ephemeral=True)
            raise
    
    #kick
    @app_commands.command(name="rin_kick", description="Kicks a member and DMs them (or not)")
    @app_commands.describe(member="The member that will be kicked", reason="The reason why the member has been kicked (no reason by default)", dm="Sets if the user will be DM'd about the timeout or not (No by default)")
    @app_commands.checks.has_permissions(administrator=True, kick_members=True) #sort out error next time
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None, dm: bool = False):
        try:
            dm_block = False

            if dm == True:
                try:
                    title = ""
                    description = ""
                    if reason == None:
                        title = "You have been kicked from " + interaction.guild.name + "!"
                        description = "Please make sure to follow the server rules or the moderators will take further action."
                    else:
                        title = "You have been kicked from " + interaction.guild.name + " for the following reason:"
                        description = "```" + reason + "```\nPlease make sure to follow the server rules or the moderators will take further action."
                    await member.send(embed=discord.Embed(title=title, description=description, color=0xff0000))
                    await asyncio.sleep(0.5) #small sleep period to make sure the dm is sent before kicking
                except discord.errors.Forbidden:
                    view = DMErrorKickButton(member=member, reason=reason)
                    extra = ""
                    if not reason == None:
                        extra = "\n\nif you want to dm manually, here's the reason that was given: ```" + reason + "```"
                    await interaction.response.send_message(embed=discord.Embed(title="this member cannot be DM'd", description="this member either has dms disabled for unknown people, or has the bot blocked (less likely). do you want to timeout anyways without dming?" + extra, color=0xff0000), ephemeral=True, view=view)
                    dm_block = True

            if dm_block == False:
                await member.kick(reason=reason)
                await interaction.response.send_message(embed=discord.Embed(description="<@" + str(member.id) + "> successfully kicked!", color=0x00aeff), ephemeral=True)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="there was an error kicking the person. please try again or contact the bot owner if you see this again", color=0xff0000), ephemeral=True)
            raise

    #ban
    @app_commands.command(name="rin_ban", description="Bans a member and DMs them (or not)")
    @app_commands.describe(member="The member that will be banned", reason="The reason why the member has been banned (no reason by default)", dm="Sets if the user will be DM'd about the timeout or not (No by default)", delete_message_days="Sets that messages less than x days will be deleted (by default 0 (none), max 7)")
    @app_commands.checks.has_permissions(administrator=True, ban_members=True) #sort out error next time
    async def ban(self, interaction: discord.Interaction, member: discord.Member, delete_message_days: int = 0, reason: str = None, dm: bool = False):
        try:
            dm_block = False

            if delete_message_days > 7 or delete_message_days < 0:
                await interaction.response.send_message(embed=discord.Embed(title="you cannot delete message for less than 0 days or more than 7 days", color=0xff0000), ephemeral=True)
            else:
                if dm == True:
                    try:
                        title = ""
                        description = ""
                        if reason == None:
                            title = "You have been banned from " + interaction.guild.name + "!"
                            description = "No reason has been given; you have either broken too many rules or done something really bad."
                        else:
                            title = "You have been Banned from " + interaction.guild.name + " for the following reason:"
                            description = "```" + reason + "```\n"
                        await member.send(embed=discord.Embed(title=title, description=description, color=0xff0000))
                        await asyncio.sleep(0.5) #small sleep period to make sure the dm is sent before kicking
                    except discord.errors.Forbidden:
                        view = DMErrorBanButton(member=member, reason=reason, delete_message_days=delete_message_days)
                        extra = ""
                        if not reason == None:
                            extra = "\n\nif you want to dm manually, here's the reason that was given: ```" + reason + "```"
                        await interaction.response.send_message(embed=discord.Embed(title="this member cannot be DM'd", description="this member either has dms disabled for unknown people, or has the bot blocked (less likely). do you want to timeout anyways without dming?" + extra, color=0xff0000), ephemeral=True, view=view)
                        dm_block = True

                if dm_block == False:
                    await member.ban(delete_message_days=delete_message_days, reason=reason)
                    await interaction.response.send_message(embed=discord.Embed(description="<@" + str(member.id) + "> successfully banned!", color=0x00aeff), ephemeral=True)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="there was an error banning the person. please try again or contact the bot owner if you see this again", color=0xff0000), ephemeral=True)
            raise

class DMErrorTimeoutButton(discord.ui.View):
    def __init__(self, *, timeout=300, user_timeout_length: timedelta, member: discord.Member, reason: string):
        super().__init__(timeout=timeout)
        self.user_timeout_length = user_timeout_length
        self.member = member
        self.reason = reason

    @discord.ui.button(label="timeout anyways", style=discord.ButtonStyle.green)
    async def timeout_anyways_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        button.disabled = True
        try:
            await interaction.response.edit_message(embed=discord.Embed(description="<@" + str(self.member.id) + "> successfully timed out!", color=0x00aeff), view=self)
            await self.member.timeout(self.user_timeout_length, reason=self.reason)
        except:
            raise

class DMErrorKickButton(discord.ui.View):
    def __init__(self, *, timeout=300, member: discord.Member, reason: string):
        super().__init__(timeout=timeout)
        self.member = member
        self.reason = reason

    @discord.ui.button(label="kick anyways", style=discord.ButtonStyle.green)
    async def kick_anyways_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        button.disabled = True
        try:
            await interaction.response.edit_message(embed=discord.Embed(description="<@" + str(self.member.id) + "> successfully kicked!", color=0x00aeff), view=self)
            await self.member.kick(reason=self.reason)
        except:
            raise

class DMErrorBanButton(discord.ui.View):
    def __init__(self, *, timeout=300, member: discord.Member, reason: string, delete_message_days: int):
        super().__init__(timeout=timeout)
        self.member = member
        self.reason = reason
        self.delete_message_days = delete_message_days

    @discord.ui.button(label="ban anyways", style=discord.ButtonStyle.green)
    async def kick_anyways_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        button.disabled = True
        try:
            await interaction.response.edit_message(embed=discord.Embed(description="<@" + str(self.member.id) + "> successfully banned!", color=0x00aeff), view=self)
            await self.member.ban(delete_message_days=self.delete_message_days, reason=self.reason)
        except:
            raise

async def setup(bot):
    await bot.add_cog(ModerationCog(bot), guilds = [discord.Object(id = 849034525861740571)])