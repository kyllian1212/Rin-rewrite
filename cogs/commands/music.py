import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from main import db
from main import VERSION

#everything needs try excepts but im just playing around rn

class MusicCog(commands.Cog):
    def __init__(self, bot, song_queue):
        self.bot = bot
        self.song_queue = {}

    @app_commands.command(name="connect", description="Connects the bot to the voice channel you are currently in")
    async def connect(self, interaction: discord.Interaction):
        #needs a check to see if its already connected
        voice_channel = interaction.user.voice.channel
        await voice_channel.connect()
        await interaction.response.send_message(embed=discord.Embed(description="Successfully connected to <#" + str(voice_channel.id) + ">!", color=0x00aeff), ephemeral=True)
    
    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel it is currently in")
    async def disconnect(self, interaction: discord.Interaction):
        #needs a check to see if its not connected
        voice_channel = interaction.user.voice.channel
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        await bot_voice_client.disconnect()
        await interaction.response.send_message(embed=discord.Embed(description="Successfully disconnected from <#" + str(voice_channel.id) + ">!", color=0x00aeff), ephemeral=True)
    
    @app_commands.command(name="play", description="Plays a file in the voice channel you are currently in")
    async def play(self, interaction: discord.Interaction, attachment: discord.Attachment):
        #needs a file extension check, a queue system, and some other checks i cant remember on top of my head at the time i commit this
        voice_channel = interaction.user.voice.channel
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if bot_voice_client == None:
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegOpusAudio(source=attachment.url))
            print(vc.source)
        else:
            bot_voice_client.play(discord.FFmpegOpusAudio(source=attachment.url))
        await interaction.response.send_message(embed=discord.Embed(description="Playing uploaded file `" + attachment.filename + "`", color=0x00aeff))
    
    @app_commands.command(name="seek", description="seeks")
    async def seek(self, interaction: discord.Integration):
        #need to figure this out
        pass
    
    @app_commands.command(name="pause", description="Pauses the file")
    async def pause(self, interaction: discord.Interaction, attachment: discord.Attachment):
        #easy to do but doing later
        pass

    @app_commands.command(name="resume", description="Resumes the file")
    async def resume(self, interaction: discord.Interaction, attachment: discord.Attachment):
        #easy to do but doing later
        pass

    @app_commands.command(name="stop", description="Stops the file")
    async def resume(self, interaction: discord.Interaction, attachment: discord.Attachment):
        #easy to do but doing later
        pass
        
async def setup(bot):
    await bot.add_cog(MusicCog(bot))