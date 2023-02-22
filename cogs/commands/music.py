import discord
from ..tasks import vc_check
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from main import db
from main import VERSION

#everything needs try excepts but im just playing around rn

class VcCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.song_playing = False
        self.file_now_playing = None
        self.current_song_timestamp = 0

    async def song_finished(self):
        self.song_playing = False

    @app_commands.command(name="connect", description="Connects the bot to the voice channel you are currently in")
    async def connect(self, interaction: discord.Interaction):
        #needs a check to see if its already connected
        voice_channel = interaction.user.voice.channel
        await voice_channel.connect()
        vc_check.VcCheckCog.vccheck_task.start(self, interaction)
        await interaction.response.send_message(embed=discord.Embed(description="Successfully connected to <#" + str(voice_channel.id) + ">!", color=0x00aeff), ephemeral=True)
    
    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel it is currently in")
    async def disconnect(self, interaction: discord.Interaction):
        #needs a check to see if its not connected
        voice_channel = interaction.user.voice.channel
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        vc_check.VcCheckCog.vccheck_task.cancel()
        await bot_voice_client.disconnect()
        await interaction.response.send_message(embed=discord.Embed(description="Successfully disconnected from <#" + str(voice_channel.id) + ">!", color=0x00aeff), ephemeral=True)
    
    @app_commands.command(name="play", description="Plays a file in the voice channel you are currently in")
    async def play(self, interaction: discord.Interaction, attachment: discord.Attachment):
        #needs a file extension check, a queue system, and some other checks i cant remember on top of my head at the time i commit this
        voice_channel = interaction.user.voice.channel
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if bot_voice_client == None:
            vc = await voice_channel.connect()
            vc_check.VcCheckCog.vccheck_task.start(self, interaction)
            self.song_playing=True
            vc.play(source=discord.FFmpegOpusAudio(source=attachment.url), after=await self.song_finished())
        else:
            self.song_playing=True
            bot_voice_client.play(discord.FFmpegOpusAudio(source=attachment.url), after=await self.song_finished())
        self.file_now_playing=attachment.url
        await interaction.response.send_message(embed=discord.Embed(description="Playing uploaded file `" + attachment.filename + "`", color=0x00aeff))
    
    @app_commands.command(name="seek", description="seeks")
    async def seek(self, interaction: discord.Integration, timestamp: str):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.source = discord.FFmpegOpusAudio(source=self.file_now_playing, before_options="-ss " + timestamp)
    
    @app_commands.command(name="pause", description="Pauses the file")
    async def pause(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.pause()

    @app_commands.command(name="resume", description="Resumes the file")
    async def resume(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.resume()

    @app_commands.command(name="stop", description="Stops the file")
    async def stop(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.stop()
    
    @app_commands.command(name="read", description="reads")
    async def read(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        print(bot_voice_client.source.read().decode("utf-8", errors="replace"))

async def setup(bot):
    await bot.add_cog(VcCog(bot))