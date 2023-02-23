import discord
import os
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime
from typing import Optional
from main import db
from main import VERSION

#everything needs try excepts but im just playing around rn
#pitch stuff: `, options="-af asetrate=44100*0.9"` check https://stackoverflow.com/questions/53374590/ffmpeg-change-tone-frequency-keep-length-pitch-audio

class VcCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
        self.file_now_playing = None
        self.current_song_timestamp = 0

    @app_commands.command(name="connect", description="Connects the bot to the voice channel you are currently in")
    async def connect(self, interaction: discord.Interaction):
        #needs a check to see if its already connected
        voice_channel = interaction.user.voice.channel
        await voice_channel.connect()
        self.vccheck_task.start(interaction)
        await interaction.response.send_message(embed=discord.Embed(description="Successfully connected to <#" + str(voice_channel.id) + ">!", color=0x00aeff), ephemeral=True)
    
    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel it is currently in")
    async def disconnect(self, interaction: discord.Interaction):
        #needs a check to see if its not connected
        voice_channel = interaction.user.voice.channel
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        self.vccheck_task.cancel()
        await bot_voice_client.disconnect()
        await interaction.response.send_message(embed=discord.Embed(description="Successfully disconnected from <#" + str(voice_channel.id) + ">!", color=0x00aeff), ephemeral=True)
    
    @app_commands.command(name="play", description="Plays a file or link in the voice channel you are currently in, or adds it to the queue if its not ")
    async def play(self, interaction: discord.Interaction, attachment: Optional[discord.Attachment], link: Optional[str] ):
        #needs a file extension check, a queue system, and some other checks i cant remember on top of my head at the time i commit this
        voice_channel = interaction.user.voice.channel
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        #check if only one file/attachment is attached
        file = "0"
        if attachment and link:
            await interaction.response.send_message(embed=discord.Embed(description="please do not upload an attachment and link at the same"), ephemeral=True)
            filecheck = 1
        elif attachment:
            file = attachment.url
            filecheck = 0
        elif link:
            file = link
            filecheck = 0
        else:
            await interaction.response.send_message(embed=discord.Embed(description="no media uploaded"), ephemeral=True)
            filecheck = 2
            
        #actually play stuff
        #i know what to fix in this whole if/elif but waiting for tox commit
        if filecheck == 0 and bot_voice_client == None or bot_voice_client.is_playing() == False:
            if bot_voice_client == None:
                vc = await voice_channel.connect()
                vc.play(discord.FFmpegOpusAudio(source=file))
                self.vccheck_task.start(interaction)
                print(vc.source)
            else:
                bot_voice_client.play(discord.FFmpegOpusAudio(source=file))
            
            self.file_now_playing = file
            
            os.system(f'ffmpeg -y -i {file} -f ffmetadata metadata.txt')
            myvars = {}
            with open("metadata.txt",'r') as myfile:
                lines = myfile.readlines()[1:]
            myvars = dict(s.split('=',1) for s in lines)
        
            dirname, fname = os.path.split(file)
            if myvars.get('TITLE'):
                title =  myvars.get('ARTIST').strip() + ' - ' + myvars.get('TITLE').strip()
                desc = myvars.get('ALBUM').strip()
            else: 
                title = ''
            await interaction.response.send_message(embed=discord.Embed(title = title, description= "album: " + myvars.get('ALBUM') + "filename: `"+ fname + "`" +"\n", color=0x00aeff))
        elif bot_voice_client.is_playing() == True:
            self.song_queue.append(file)
            await interaction.response.send_message(embed=discord.Embed(title="added to queue", color=0x00aeff))
    
    @app_commands.command(name="seek", description="Sets the play position to the specified timestamp")
    @app_commands.describe(timestamp="(in seconds)")
    async def seek(self, interaction: discord.Integration, timestamp: str):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.source = discord.FFmpegOpusAudio(source=self.file_now_playing, before_options="-ss " + timestamp)
        await interaction.response.send_message(embed=discord.Embed(description="seeked placeholder", color=0x00aeff))
    
    @app_commands.command(name="pause", description="Pauses the file")
    async def pause(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.pause()
        await interaction.response.send_message(embed=discord.Embed(description="File paused.", color=0x00aeff))

    @app_commands.command(name="resume", description="Resumes the file")
    async def resume(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.resume()
        await interaction.response.send_message(embed=discord.Embed(description="File resumed.", color=0x00aeff))

    @app_commands.command(name="skip", description="Skips the file")
    async def stop(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.stop()
        await interaction.response.send_message(embed=discord.Embed(description="File stopped.", color=0x00aeff))
        #do stuff to go to next song in queue here

    @app_commands.command(name="stop", description="Stops playing and clears the queue")
    async def stop(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.stop()
        await interaction.response.send_message(embed=discord.Embed(description="File stopped and queue cleared.", color=0x00aeff))
        #do stuff to clear queue here

    #constantly checks the vc instance
    #not sure if discord.utilis.get does an api request (i assume it does), might be an issue if too many requests are made but its only on 2 servers rn so idc
    @tasks.loop(seconds=0.1)
    async def vccheck_task(self, interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if bot_voice_client.source == None or bot_voice_client.is_playing() == False:
            print("file is NOT playing")
            self.file_now_playing = None
            self.current_song_timestamp = 0
            if len(self.song_queue) == 0:
                print("there is nothing in that list")
            else:
                print("there is something in that list")
        elif bot_voice_client.is_paused():
            print("file is paused")
        else:
            print("file is playing")
            self.current_song_timestamp += 0.1
        print(self.current_song_timestamp)
        print(bot_voice_client.source)
        print(self.song_queue)

async def setup(bot):
    await bot.add_cog(VcCog(bot))