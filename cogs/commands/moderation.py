"""
Moderation Module
"""

from datetime import timedelta
import string
import asyncio
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
import templates.embeds as embeds

from main import db


class ModerationCog(commands.Cog):
    """Cog for all moderation commands

    Args:
        commands (Cog): default base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot
        self.interaction_webhook = None

    # enable moderation logging
    @app_commands.command(
        name="toggle_moderation_log",
        description="Toggles bans and timeouts showing up in the log channel.",
    )
    @app_commands.default_permissions(administrator=True)
    async def toggle_moderation_log(self, interaction: discord.Interaction):
        """Toggles bans and timeouts showing up in the log channel.

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer(ephemeral=True)
            moderation_log_set = db.fetchone_fullrow(
                "SELECT * FROM bot_settings WHERE guild_id = ? AND setting_name = 'moderation_log'",
                interaction.guild_id,
            )
            description = "Moderation log successfully enabled!"

            if moderation_log_set is None:
                db.update_db(
                    "INSERT INTO bot_settings VALUES (?,?,?)",
                    interaction.guild_id,
                    "moderation_log",
                    "1",
                )
            elif moderation_log_set[2] == "1":
                db.update_db(
                    "UPDATE bot_settings SET setting_value = ? WHERE guild_id = ? AND setting_name = 'moderation_log'",
                    "0",
                    interaction.guild_id,
                )
                description = "Moderation log successfully disabled!"
            elif moderation_log_set[2] == "0":
                db.update_db(
                    "UPDATE bot_settings SET setting_value = ? WHERE guild_id = ? AND setting_name = 'moderation_log'",
                    "1",
                    interaction.guild_id,
                )

            await interaction.followup.send(
                embed=discord.Embed(description=description, color=0x00AEFF),
            )
        except:
            await embeds.error_executing_command(
                interaction, title_detail="toggling the moderation log."
            )
            raise

    # timeout
    @app_commands.command(
        name="rin_timeout",
        description="Times out a member (for up to 28 days) and DMs them (or not)",
    )
    @app_commands.describe(
        member="The member that will be timed out",
        reason="The reason why the member has been timed out (no reason by default)",
        dm="Sets if the user will be DM'd about the timeout or not (No by default)",
    )
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        timeout_length_days: int = 0,
        timeout_length_hours: int = 0,
        timeout_length_minutes: int = 0,
        reason: str = None,
        dm: bool = False,
    ):
        """Times out a member (for up to 28 days) and DMs them (or not)

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            member (discord.Member): the Discord Member info
            timeout_length_days (int, optional): timeout duration in days. Defaults to 0.
            timeout_length_hours (int, optional): timeout duration in hours. Defaults to 0.
            timeout_length_minutes (int, optional): timeout duration in minutes. Defaults to 0.
            reason (str, optional): optional reason for timeout. Defaults to None.
            dm (bool, optional): specifies whether a DM will be sent to the user being timed out. Defaults to False.
        """
        try:
            await interaction.response.defer(ephemeral=True)
            if timeout_length_minutes + timeout_length_hours + timeout_length_days == 0:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="You cannot timeout someone for 0 minutes", color=0xFF0000
                    )
                )
            else:
                timeout = timedelta(
                    days=timeout_length_days,
                    minutes=timeout_length_minutes,
                    hours=timeout_length_hours,
                )
                dm_block = False
                user_dmd = ""

                if dm is True:
                    try:
                        title = ""
                        description = ""
                        if reason is None:
                            title = (
                                "You have been timed out from "
                                + interaction.guild.name
                                + "!"
                            )
                            description = "Please make sure to follow the server rules to not get another timeout."
                        else:
                            title = (
                                "You have been timed out from "
                                + interaction.guild.name
                                + " for the following reason:"
                            )
                            description = (
                                "```"
                                + reason
                                + "```\nPlease make sure to follow the server rules to not get another timeout."
                            )
                        await member.send(
                            embed=discord.Embed(
                                title=title, description=description, color=0xFF0000
                            )
                        )
                        user_dmd = "\nPlease note that the user has been DM'd so you will have to manually timeout!"
                    except discord.errors.Forbidden:
                        view = DMErrorTimeoutButton(
                            user_timeout_length=timeout,
                            member=member,
                            reason=reason,
                            mod_self=self,
                        )
                        extra = ""
                        if not reason is None:
                            extra = (
                                "\n\nIf you want to DM manually, here's the reason that was given: ```"
                                + reason
                                + "```"
                            )
                        self.interaction_webhook = await interaction.followup.send(
                            embed=discord.Embed(
                                title="This member cannot be DM'd",
                                description="This member either has DMs disabled for unknown people, or has the bot blocked (less likely). Do you want to timeout anyways without DMing?"
                                + extra,
                                color=0xFF0000,
                            ),
                            view=view,
                            wait=True,
                        )
                        dm_block = True

                if dm_block is False:
                    await member.timeout(timeout, reason=reason)
                    await interaction.followup.send(
                        embed=discord.Embed(
                            description="<@"
                            + str(member.id)
                            + "> successfully timed out!",
                            color=0x00AEFF,
                        )
                    )
        except:
            await embeds.error_executing_command(
                interaction,
                title_detail="timing out the person.",
                extra_error_detail=f"(Maybe the Rin role is under a role that the user you want to time out has? Please note that it is not possible to timeout someone for more than 28 days due to an API limitation.){user_dmd}",
            )
            raise

    # kick
    @app_commands.command(
        name="rin_kick", description="Kicks a member and DMs them (or not)"
    )
    @app_commands.describe(
        member="The member that will be kicked",
        reason="The reason why the member has been kicked (no reason by default)",
        dm="Sets if the user will be DM'd about the kick or not (No by default)",
    )
    @app_commands.default_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = None,
        dm: bool = False,
    ):
        """Kicks a member and DMs them (or not)

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            member (discord.Member): the Discord member info
            reason (str, optional): The kick reason. Defaults to None.
            dm (bool, optional): specifies whether a DM will be sent to the user being timed out. Defaults to False.
        """
        try:
            await interaction.response.defer(ephemeral=True)
            dm_block = False
            user_dmd = ""

            if dm is True:
                try:
                    title = ""
                    description = ""
                    if reason is None:
                        title = (
                            "You have been kicked from " + interaction.guild.name + "!"
                        )
                        description = "Please make sure to follow the server rules or the moderators will take further action."
                    else:
                        title = (
                            "You have been kicked from "
                            + interaction.guild.name
                            + " for the following reason:"
                        )
                        description = (
                            "```"
                            + reason
                            + "```\nPlease make sure to follow the server rules or the moderators will take further action."
                        )
                    await member.send(
                        embed=discord.Embed(
                            title=title, description=description, color=0xFF0000
                        )
                    )
                    user_dmd = "\nPlease note that the user has been DM'd so you will have to manually kick!"
                    await asyncio.sleep(
                        0.5
                    )  # small sleep period to make sure the dm is sent before kicking
                except discord.errors.Forbidden:
                    view = DMErrorKickButton(
                        member=member, reason=reason, mod_self=self
                    )
                    if not reason is None:
                        extra = (
                            "\n\nIf you want to DM manually, here's the reason that was given: ```"
                            + reason
                            + "```"
                        )
                    self.interaction_webhook = await interaction.followup.send(
                        embed=discord.Embed(
                            title="This member cannot be DM'd",
                            description="This member either has DMs disabled for unknown people, or has the bot blocked (less likely). Do you want to kick anyways without DMing?"
                            + extra,
                            color=0xFF0000,
                        ),
                        view=view,
                    )
                    dm_block = True

            if dm_block is False:
                await member.kick(reason=reason)
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="<@" + str(member.id) + "> successfully kicked!",
                        color=0x00AEFF,
                    ),
                )
        except:
            await embeds.error_executing_command(
                interaction,
                title_detail="kicking the person.",
                extra_error_detail=f"(Maybe the Rin role is under a role that the user you want to kick has?){user_dmd}",
            )
            raise

    # ban
    @app_commands.command(
        name="rin_ban", description="Bans a member and DMs them (or not)"
    )
    @app_commands.describe(
        member="The member that will be banned",
        reason="The reason why the member has been banned (no reason by default)",
        dm="Sets if the user will be DM'd about the ban or not (No by default)",
        delete_message_days="Sets that messages less than x days will be deleted (by default 0 (none), max 7)",
    )
    @app_commands.default_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        delete_message_days: int = 0,
        reason: str = None,
        dm: bool = False,
    ):
        """Bans a member and DMs them (or not)

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            member (discord.Member): the Discord member info
            delete_message_days (int, optional): Deletes all messages in the last x days. Defaults to 0. Max 7.
            reason (str, optional): The ban reason. Defaults to None.
            dm (bool, optional): specifies whether a DM will be sent to the user being banned. Defaults to False.
        """
        try:
            await interaction.response.defer(ephemeral=True)
            dm_block = False
            user_dmd = ""

            if delete_message_days > 7 or delete_message_days < 0:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="You cannot delete messages for less than 0 days or more than 7 days",
                        color=0xFF0000,
                    ),
                )
            else:
                if dm is True:
                    try:
                        title = ""
                        description = ""
                        if reason is None:
                            title = (
                                "You have been banned from "
                                + interaction.guild.name
                                + "!"
                            )
                            description = "No reason has been given; you have either broken too many rules or done something really bad."
                        else:
                            title = (
                                "You have been banned from "
                                + interaction.guild.name
                                + " for the following reason:"
                            )
                            description = "```" + reason + "```\n"
                        await member.send(
                            embed=discord.Embed(
                                title=title, description=description, color=0xFF0000
                            )
                        )
                        user_dmd = "\nPlease note that the user has been DM'd so you will have to manually ban!"
                        await asyncio.sleep(
                            0.5
                        )  # small sleep period to make sure the dm is sent before banning
                    except discord.errors.Forbidden:
                        view = DMErrorBanButton(
                            member=member,
                            reason=reason,
                            delete_message_days=delete_message_days,
                            mod_self=self,
                        )
                        extra = ""
                        if not reason is None:
                            extra = (
                                "\n\nIf you want to dm manually, here's the reason that was given: ```"
                                + reason
                                + "```"
                            )
                        self.interaction_webhook = await interaction.followup.send(
                            embed=discord.Embed(
                                title="This member cannot be DM'd",
                                description="This member either has DMs disabled for unknown people, or has the bot blocked (less likely). Do you want to ban anyways without DMing?"
                                + extra,
                                color=0xFF0000,
                            ),
                            view=view,
                        )
                        dm_block = True

                if dm_block is False:
                    await member.ban(
                        delete_message_days=delete_message_days, reason=reason
                    )
                    await interaction.followup.send(
                        embed=discord.Embed(
                            description="<@"
                            + str(member.id)
                            + "> successfully banned!",
                            color=0x00AEFF,
                        ),
                    )
        except:
            await embeds.error_executing_command(
                interaction,
                title_detail="banning the person.",
                extra_error_detail=f"(Maybe the Rin role is under a role that the user you want to ban has?){user_dmd}",
            )
            raise

    # rename channel
    @app_commands.command(
        name="rename_channel",
        description="Renames the selected channel, or the channel you're in if none is selected",
    )
    @app_commands.describe(
        text_channel="The channel you want to rename",
        channel_name="The new channel name",
    )
    @app_commands.default_permissions(manage_channels=True)
    async def rename_channel(
        self,
        interaction: discord.Interaction,
        text_channel: Optional[discord.TextChannel],
        channel_name: str,
    ):
        """Renames the selected channel, or the channel you're in if none is selected.

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            text_channel (Optional[discord.TextChannel]): The text channel to rename
            channel_name (str): the new channel name
        """
        try:
            await interaction.response.defer(ephemeral=True)
            # defer (incl. on missing perm embed) to avoid api errors if rate limited
            if text_channel is None:
                text_channel = interaction.channel
            text_channel_old_name = f"#{text_channel.name}"
            await text_channel.edit(name=channel_name)
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"Channel {text_channel_old_name} successfully renamed to <#{text_channel.id}>",
                    color=0x00AEFF,
                ),
            )
        except:
            await embeds.error_executing_command(
                interaction, title_detail="renaming the channel."
            )
            raise

    @timeout.error
    @kick.error
    @ban.error
    @rename_channel.error
    async def error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """checks for missing permissions on an error

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            error (app_commands.AppCommandError): the error object that has been thrown
        """
        if isinstance(error, app_commands.MissingPermissions):
            await embeds.missing_permissions(interaction)


class DMErrorTimeoutButton(discord.ui.View):
    def __init__(
        self,
        *,
        timeout=300,
        user_timeout_length: timedelta,
        member: discord.Member,
        reason: string,
        mod_self: ModerationCog,
    ):
        """initializes the time out button

        Args:
            user_timeout_length (timedelta): the length of the user timeout
            member (discord.Member): the Discord member info
            reason (string): the timeout reason
            mod_self (ModerationCog): The cog containing moderation logic
            timeout (int, optional): the UI timeout counter. Defaults to 300.
        """
        super().__init__(timeout=timeout)
        self.user_timeout_length = user_timeout_length
        self.member = member
        self.reason = reason
        self.mod_self = mod_self

    @discord.ui.button(label="Timeout anyways", style=discord.ButtonStyle.green)
    async def timeout_anyways_button(self, interaction: discord.Interaction, button:discord.ui.Button):
        """Timeout button UI element

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await self.member.timeout(self.user_timeout_length, reason=self.reason)
            await self.mod_self.interaction_webhook.edit(
                embed=discord.Embed(
                    description="<@"
                    + str(self.member.id)
                    + "> successfully timed out!",
                    color=0x00AEFF,
                ),
                view=None,
            )
        except:
            await embeds.error_executing_command(interaction, edit=True)
            raise


class DMErrorKickButton(discord.ui.View):
    def __init__(
        self,
        *,
        timeout=300,
        member: discord.Member,
        reason: string,
        mod_self: ModerationCog,
    ):
        """initializes the kick button

        Args:
            member (discord.Member): the Discord member info
            reason (string): the kick reason
            mod_self (ModerationCog): the moderation logic
            timeout (int, optional): the UI timeout counter. Defaults to 300.
        """
        super().__init__(timeout=timeout)
        self.member = member
        self.reason = reason
        self.mod_self = mod_self

    @discord.ui.button(label="Kick anyways", style=discord.ButtonStyle.green)
    async def kick_anyways_button(self, interaction: discord.Interaction, button:discord.ui.Button):
        """Kick button UI element

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await self.member.kick(reason=self.reason)
            await self.mod_self.interaction_webhook.edit(
                embed=discord.Embed(
                    description="<@" + str(self.member.id) + "> successfully kicked!",
                    color=0x00AEFF,
                ),
                view=None,
            )
        except:
            await embeds.error_executing_command(interaction, edit=True)
            raise


class DMErrorBanButton(discord.ui.View):
    def __init__(
        self,
        *,
        timeout=300,
        member: discord.Member,
        reason: string,
        delete_message_days: int,
        mod_self: ModerationCog,
    ):
        """initializes the ban button

        Args:
            member (discord.Member): the Discord member info
            reason (string): the ban reason
            delete_message_days (int): the number of days in the past to delete messages from banned user
            mod_self (ModerationCog): the moderation logic
            timeout (int, optional): the UI timeout counter. Defaults to 300.
        """
        super().__init__(timeout=timeout)
        self.member = member
        self.reason = reason
        self.delete_message_days = delete_message_days
        self.mod_self = mod_self

    @discord.ui.button(label="Ban anyways", style=discord.ButtonStyle.green)
    async def ban_anyways_button(self, interaction: discord.Interaction, button:discord.ui.Button):
        """Ban button UI element

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await self.member.ban(
                delete_message_days=self.delete_message_days, reason=self.reason
            )
            await self.mod_self.interaction_webhook.edit(
                embed=discord.Embed(
                    description="<@" + str(self.member.id) + "> successfully banned!",
                    color=0x00AEFF,
                ),
                view=None,
            )
        except:
            await embeds.error_executing_command(interaction, edit=True)
            raise


async def setup(bot: commands.Bot):
    """initializes the moderation cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(ModerationCog(bot))
