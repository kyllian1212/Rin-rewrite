"""Members Module
"""

from datetime import datetime
import discord
from discord.ext import commands

from main import db


class MembersCog(commands.Cog):
    """Members cog

    Args:
        commands (Cog): base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Waits for member ban and logs ban in log channel

        Args:
            guild (discord.Guild): the Discord Server (Servers are referred to as "Guilds")
            user (discord.User): the Discord user that has been banned
        """
        log_channel_id = db.fetchone_singlecolumn(
            0, "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?", guild.id
        )

        if log_channel_id is not None:
            log_channel = await self.bot.fetch_channel(log_channel_id)
            now = str(
                datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)")
            )

            banned_embed = discord.Embed(
                title="A member has been banned", color=0xFF0000
            )
            banned_embed.add_field(name="User tag:", value=f"<@{user.id}>")
            banned_embed.add_field(
                name="Username when banned:", value=f"{user.name}#{user.discriminator}"
            )
            banned_embed.set_thumbnail(url=user.avatar.url)
            banned_embed.set_footer(text=f"User ID: {str(user.id)}  •  {now}")

            await log_channel.send(embed=banned_embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Waits for member unban and logs unban in log channel

        Args:
            guild (discord.Guild): the Discord Server (Servers are referred to as "Guilds")
            user (discord.User): the Discord user that has been unbanned
        """
        log_channel_id = db.fetchone_singlecolumn(
            0, "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?", guild.id
        )

        if log_channel_id is not None:
            log_channel = await self.bot.fetch_channel(log_channel_id)
            now = str(
                datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)")
            )

            unbanned_embed = discord.Embed(
                title="A user has been unbanned", color=0x00AEFF
            )
            unbanned_embed.add_field(name="User tag:", value=f"<@{user.id}>")
            unbanned_embed.add_field(
                name="Username when unbanned:",
                value=f"{user.name}#{user.discriminator}",
            )
            unbanned_embed.set_thumbnail(url=user.avatar.url)
            unbanned_embed.set_footer(text=f"User ID: {str(user.id)}  •  {now}")

            await log_channel.send(embed=unbanned_embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Waits for member update and sends a log to log channel

        This is called when one or more of the following things change:

            * nickname

            * roles

            * pending

            * timeout

            * guild avatar

            * flags

        # Due to a Discord limitation, this event is not dispatched when a member's timeout expires.

        Args:
            before (discord.Member): the updated members old info
            after (discord.Member): the updated members new info
        """
        log_channel_id = db.fetchone_singlecolumn(
            0,
            "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?",
            after.guild.id,
        )

        if (
            log_channel_id is not None
            and before.timed_out_until != after.timed_out_until
            and after.timed_out_until is not None
        ):
            log_channel = await self.bot.fetch_channel(log_channel_id)
            now = str(
                datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)")
            )

            timeout_embed = discord.Embed(
                title="A member has been timed out", color=0xFF0000
            )
            timeout_embed.add_field(name="User tag:", value=f"<@{after.id}>")
            timeout_embed.add_field(
                name="Username when timed out:",
                value=f"{after.name}#{after.discriminator}",
            )
            timeout_embed.add_field(
                name="Timed out until:",
                value=f"<t:{int(after.timed_out_until.timestamp())}:D> - <t:{int(after.timed_out_until.timestamp())}:T>",
                inline=False,
            )
            timeout_embed.set_thumbnail(url=after.avatar.url)
            timeout_embed.set_footer(text=f"User ID: {str(after.id)}  •  {now}")

            await log_channel.send(embed=timeout_embed)


async def setup(bot: commands.Bot):
    """initializes the Member cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(MembersCog(bot))
