"""
Reactions Module
"""

from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get

from main import db

"""
figure it out later lol
FIX THE CODE BECAUSE OF THE FETCHES INSTEAD OF GET MEMBERS
class ModalTest(discord.ui.Modal, title="Report this message"):
    delete = discord.ui.Label(
        text="Delete this message?",
        component=discord.ui.Checkbox(default=True)
    )

    async def on_submit(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(ephemeral=True)
        log_channel_id = db.fetchone_singlecolumn(
            0,
            "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?",
            interaction.guild.id,
        )
        description = ""

        if self.delete.component is True:
            print("this is true")

        if log_channel_id is None:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="There are no log channel set for this server",
                    description="Please set a log channel with the /set_log_channel command",
                    color=0xFF0000,
                ),
            )
        elif interaction.user.bot == False:
            channel = await self.bot.fetch_channel(interaction.channel.id)
            reacted_message = message

            if (
                not interaction.user.id == reacted_message.author.id
            ):
                log_channel = await self.bot.fetch_channel(log_channel_id)
                now = str(
                    datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)")
                )
                message_creation_timestamp = int(reacted_message.created_at.timestamp())
                reacted_message_author_roles = None
                long_message = False
                is_member = True
                guild = self.bot.get_guild(interaction.guild.id)

                # check if user is a member of the server or not
                if guild.get_member(reacted_message.author.id) is None:
                    is_member = False
                    description += "\n*This user is currently not on the server.*"

                if is_member is True:
                    for role in reacted_message.author.roles:
                        if role.name != "@everyone":
                            if reacted_message_author_roles is None:
                                reacted_message_author_roles = str(role.mention)
                            else:
                                reacted_message_author_roles = (
                                    str(reacted_message_author_roles)
                                    + ", "
                                    + str(role.mention)
                                )

                reported_message_embed = discord.Embed(
                    title="Reported Message - ID: " + str(reacted_message.id),
                    description=description,
                    color=0xFF0000,
                )

                if reacted_message.author.avatar is None:
                    reported_message_embed.set_thumbnail(
                        url="https://cdn.discordapp.com/embed/avatars/0.png"
                    )
                else:
                    reported_message_embed.set_thumbnail(
                        url=reacted_message.author.avatar.url
                    )

                reported_message_embed.add_field(
                    name="Username", value=reacted_message.author.name, inline=True
                )

                if is_member is True:
                    reported_message_embed.add_field(
                        name="Nickname", value=reacted_message.author.nick, inline=True
                    )

                reported_message_embed.add_field(
                    name="User ID",
                    value="<@" + str(reacted_message.author.id) + ">",
                    inline=True,
                )
                reported_message_embed.add_field(
                    name="Channel",
                    value="<#" + str(reacted_message.channel.id) + ">",
                    inline=True,
                )

                if is_member is True:
                    reported_message_embed.add_field(
                        name="User Roles",
                        value=str(reacted_message_author_roles),
                        inline=True,
                    )
                reported_message_embed.add_field(
                    name="Message creation date/time",
                    value="<t:"
                    + str(message_creation_timestamp)
                    + ":D> - <t:"
                    + str(message_creation_timestamp)
                    + ":T>",
                    inline=True,
                )
                # if the message is too long
                if len(reacted_message.content) >= 900:
                    long_message = True
                    message_length = len(reacted_message.content)

                    reacted_message_content_part2 = reacted_message.content[
                        899:message_length
                    ]

                    reacted_message_content_part1 = reacted_message.content[0:899]

                    reported_message_embed.add_field(
                        name="Message",
                        value=reacted_message_content_part1,
                        inline=False,
                    )

                    reported_message_part2_embed = discord.Embed(
                        description="*The message is too long for a single Discord embed, so it has been split into 2 Discord embeds.*",
                        color=0xFF0000,
                    )

                    reacted_message_content_part2_with_jump_to = (
                        reacted_message_content_part2
                        + "\n"
                        + "[Jump to context]("
                        + reacted_message.jump_url
                        + ")"
                    )

                    reported_message_part2_embed.add_field(
                        name="Message (part 2)",
                        value=reacted_message_content_part2_with_jump_to,
                        inline=False,
                    )

                    reported_message_part2_embed.set_footer(
                        text="Reported by "
                        + str(interaction.user.name)
                        + "  •  "
                        + now,
                        icon_url=interaction.user.avatar.url,
                    )
                else:
                    # even if message is deleted, you can still jump to the context with jump_url
                    message = (
                        reacted_message.content
                        + "\n"
                        + "[Jump to context]("
                        + reacted_message.jump_url
                        + ")"
                    )

                    reported_message_embed.add_field(
                        name="Message", value=message, inline=False
                    )

                    reported_message_embed.set_footer(
                        text="Reported by "
                        + str(interaction.user.name)
                        + "  •  "
                        + now,
                        icon_url=interaction.user.avatar.url,
                    )

                files = []
                file_names = []

                for idx, attachment in enumerate(reacted_message.attachments):
                    # max # of files to attach to a message == 10
                    if idx > 10:
                        continue

                    files.append(await attachment.to_file(spoiler=True))
                    file_names.append(attachment.filename)

                if files:
                    reported_message_embed.add_field(
                        name="Attachments (reuploaded above this embed)", value="\n".join(file_names), inline=False
                    )

                if (
                    interaction.user.guild_permissions.administrator is True
                    or interaction.user.guild_permissions.manage_messages is True
                    or interaction.user.id == reacted_message.author.id
                ):
                    await reacted_message.delete()
                    description = "*The message has been deleted as it has been reported by an admin.*"

                await log_channel.send(embed=reported_message_embed, files=files)
                if long_message is True:
                    await log_channel.send(embed=reported_message_part2_embed)

                await interaction.followup.send(
                    embed=discord.Embed(
                        description="Message successfully reported!",
                        color=0x00AEFF,
                    ),
                )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="There was an error reporting the message. Please try again or contact the bot owner if you see this again",
                color=0xFF0000,
            ),
            ephemeral=True
        )
        raise
"""

class ReportCog(commands.Cog):
    """Class for handling raw reactions"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name='Report message',
            callback=self.report,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def report(self, interaction: discord.Interaction, message: discord.Message):
        """Handler for raw reactions"""
        try:
            await interaction.response.defer(ephemeral=True)
            log_channel_id = db.fetchone_singlecolumn(
                0,
                "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?",
                interaction.guild.id,
            )
            description = ""

            if log_channel_id is None:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="There are no log channel set for this server",
                        description="Please set a log channel with the /set_log_channel command",
                        color=0xFF0000,
                    ),
                )
            elif interaction.user.bot == False:
                #channel = await self.bot.fetch_channel(interaction.channel.id)
                guild = self.bot.get_guild(interaction.guild.id)
                reacted_message = message
                interaction_member = await guild.fetch_member(interaction.user.id)
                reacted_message_author = await guild.fetch_member(reacted_message.author.id)

                if (
                    not interaction_member.id == reacted_message_author.id
                ):
                    log_channel = await self.bot.fetch_channel(log_channel_id)
                    now = str(
                        datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)")
                    )
                    message_creation_timestamp = int(reacted_message.created_at.timestamp())
                    reacted_message_author_roles = None
                    long_message = False
                    is_member = True

                    # check if user is a member of the server or not
                    if await guild.fetch_member(reacted_message_author.id) is None:
                        is_member = False
                        description += "\n*This user is currently not on the server.*"

                    if is_member is True:
                        for role in reacted_message_author.roles:
                            if role.name != "@everyone":
                                if reacted_message_author_roles is None:
                                    reacted_message_author_roles = str(role.mention)
                                else:
                                    reacted_message_author_roles = (
                                        str(reacted_message_author_roles)
                                        + ", "
                                        + str(role.mention)
                                    )

                    reported_message_embed = discord.Embed(
                        title="Reported Message - ID: " + str(reacted_message.id),
                        description=description,
                        color=0xFF0000,
                    )

                    if reacted_message_author.avatar is None:
                        reported_message_embed.set_thumbnail(
                            url="https://cdn.discordapp.com/embed/avatars/0.png"
                        )
                    else:
                        reported_message_embed.set_thumbnail(
                            url=reacted_message_author.avatar.url
                        )

                    reported_message_embed.add_field(
                        name="Username", value=reacted_message_author.name, inline=True
                    )

                    if is_member is True:
                        reported_message_embed.add_field(
                            name="Nickname", value=reacted_message_author.nick, inline=True
                        )

                    reported_message_embed.add_field(
                        name="User ID",
                        value="<@" + str(reacted_message_author.id) + ">",
                        inline=True,
                    )
                    reported_message_embed.add_field(
                        name="Channel",
                        value="<#" + str(reacted_message.channel.id) + ">",
                        inline=True,
                    )

                    if is_member is True:
                        reported_message_embed.add_field(
                            name="User Roles",
                            value=str(reacted_message_author_roles),
                            inline=True,
                        )
                    reported_message_embed.add_field(
                        name="Message creation date/time",
                        value="<t:"
                        + str(message_creation_timestamp)
                        + ":D> - <t:"
                        + str(message_creation_timestamp)
                        + ":T>",
                        inline=True,
                    )
                    # if the message is too long
                    if len(reacted_message.content) >= 900:
                        long_message = True
                        message_length = len(reacted_message.content)

                        reacted_message_content_part2 = reacted_message.content[
                            899:message_length
                        ]

                        reacted_message_content_part1 = reacted_message.content[0:899]

                        reported_message_embed.add_field(
                            name="Message",
                            value=reacted_message_content_part1,
                            inline=False,
                        )

                        reported_message_part2_embed = discord.Embed(
                            description="*The message is too long for a single Discord embed, so it has been split into 2 Discord embeds.*",
                            color=0xFF0000,
                        )

                        reacted_message_content_part2_with_jump_to = (
                            reacted_message_content_part2
                            + "\n"
                            + "[Jump to context]("
                            + reacted_message.jump_url
                            + ")"
                        )

                        reported_message_part2_embed.add_field(
                            name="Message (part 2)",
                            value=reacted_message_content_part2_with_jump_to,
                            inline=False,
                        )

                        reported_message_part2_embed.set_footer(
                            text="Reported by "
                            + str(interaction_member.name)
                            + "  •  "
                            + now,
                            icon_url=interaction_member.avatar.url,
                        )
                    else:
                        # even if message is deleted, you can still jump to the context with jump_url
                        message = (
                            reacted_message.content
                            + "\n"
                            + "[Jump to context]("
                            + reacted_message.jump_url
                            + ")"
                        )

                        reported_message_embed.add_field(
                            name="Message", value=message, inline=False
                        )

                        reported_message_embed.set_footer(
                            text="Reported by "
                            + str(interaction_member.name)
                            + "  •  "
                            + now,
                            icon_url=interaction_member.avatar.url,
                        )

                    files = []
                    file_names = []

                    for idx, attachment in enumerate(reacted_message.attachments):
                        # max # of files to attach to a message == 10
                        if idx > 10:
                            continue

                        files.append(await attachment.to_file(spoiler=True))
                        file_names.append(attachment.filename)

                    if files:
                        reported_message_embed.add_field(
                            name="Attachments (reuploaded above this embed)", value="\n".join(file_names), inline=False
                        )

                    if (
                        interaction_member.guild_permissions.administrator is True
                        or interaction_member.guild_permissions.manage_messages is True
                        or interaction_member.id == reacted_message_author.id
                    ):
                        await reacted_message.delete()
                        reported_message_embed.description = "*The message has been deleted as it has been reported by an admin.*"

                    await log_channel.send(embed=reported_message_embed, files=files)
                    if long_message is True:
                        await log_channel.send(embed=reported_message_part2_embed)

                    await interaction.followup.send(
                        embed=discord.Embed(
                            description="Message successfully reported!",
                            color=0x00AEFF,
                        ),
                    )
        except:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="There was an error reporting the message. Please try again or contact the bot owner if you see this again",
                    color=0xFF0000,
                ),
            )
            raise


async def setup(bot):
    """Adds cog to bot"""
    await bot.add_cog(ReportCog(bot))
