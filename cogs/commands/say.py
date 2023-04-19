"""
Say Module
"""
from discord.ext import commands


class SayCog(commands.Cog):
    """Cog to send a message from the bot

    Args:
        commands (Cog): base class for all Cogs
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def say(self, ctx: commands.Context, *, arg: str):
        """Sends a message in a selected channel

        Args:
            ctx (commands.Context): the context from the command's executor (location, message, etc.)
            arg (str): the message to be sent
        """
        await ctx.message.delete()
        await ctx.channel.send(arg)

    @commands.command(name="saytts")
    @commands.has_permissions(administrator=True)
    async def say_tts(self, ctx: commands.Context, *, arg: str):
        """Sends a message in a selected channel with text to speech

        Args:
            ctx (commands.Context): the context from the command's executor (location, message, etc.)
            arg (str): the message to be sent
        """
        await ctx.message.delete()
        await ctx.channel.send(arg, tts=True)


async def setup(bot: commands.Bot):
    """initializes the Say cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(SayCog(bot))
