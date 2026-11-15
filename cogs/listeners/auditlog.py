"""
Members Module
"""

from datetime import datetime
import discord
from discord.ext import commands

from main import db


class AuditLogCog(commands.Cog):
    """Audit Log cog

    Args:
        commands (Cog): base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot

    def check_setting(self, guild: discord.Guild):
        """Checks if the 'moderation_log' setting is enabled

        Args:
            guild (discord.Guild): the Discord Server (Servers are referred to as "Guilds")
        """
        return db.fetchone_singlecolumn(
                0, "SELECT setting_value FROM bot_settings WHERE setting_name = 'moderation_log' AND guild_id = ?", guild.id
            )

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        try:
            if self.check_setting(entry.guild) == "1":
                log_channel_id = db.fetchone_singlecolumn(
                    0,
                    "SELECT log_channel_id FROM bot_log_channel WHERE guild_id = ?",
                    entry.guild.id,
                )

                if (
                    log_channel_id is not None
                    and entry.action.name == "member_update"
                    and entry.before.timed_out_until != entry.after.timed_out_until
                    and entry.after.timed_out_until is not None
                ):
                    affected_member = await entry.guild.fetch_member(entry.target.id)
                    action_member = await entry.guild.fetch_member(entry.user_id)
                    log_channel = await self.bot.fetch_channel(log_channel_id)
                    now = str(
                        datetime.now().astimezone().strftime("%d/%m/%Y - %H:%M:%S (UTC%z)")
                    )

                    timeout_embed = discord.Embed(
                        title="A member has been timed out", color=0xFF0000
                    )
                    timeout_embed.add_field(name="User tag:", value=f"<@{affected_member.id}>")
                    timeout_embed.add_field(
                        name="Username when timed out:",
                        value=f"{affected_member.name}",
                    )
                    timeout_embed.add_field(
                        name="Timed out until:",
                        value=f"<t:{int(entry.after.timed_out_until.timestamp())}:D> - <t:{int(entry.after.timed_out_until.timestamp())}:T>",
                        inline=False,
                    )
                    timeout_embed.add_field(
                        name="Reason:",
                        value=f"{str(entry.reason)}",
                        inline=True,
                    )
                    if affected_member.avatar is None:
                        timeout_embed.set_thumbnail(
                            url="https://cdn.discordapp.com/embed/avatars/0.png"
                        )
                    else:
                        timeout_embed.set_thumbnail(url=affected_member.avatar.url)
                    timeout_embed.set_footer(
                        text=f"Issued by {str(action_member.name)} • User ID: {str(affected_member.id)}  •  {now}",
                        icon_url=action_member.avatar.url)

                    await log_channel.send(embed=timeout_embed)
        except:
            raise


async def setup(bot: commands.Bot):
    """initializes the Audit Log cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(AuditLogCog(bot))
