import discord
import asyncio
import os
from datetime import timedelta
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime
from typing import Optional
from main import db
from main import VERSION
import math
import traceback

#pitch stuff: `, options="-af asetrate=44100*0.9"` check https://stackoverflow.com/questions/53374590/ffmpeg-change-tone-frequency-keep-length-pitch-audio
#add volume/speed/pitch/equalizer/reverb/reverse/bitrate eventually

def sec_to_hms(seconds):
    seconds_round = round(seconds)
    min, sec = divmod(seconds_round, 60)
    hour, min = divmod(min, 60)
    if hour:
        h = f"{hour}:"
        m = f"{min:02d}"
    else:
        h = ''
        m = min
    return f"{h}{m}:{sec:02d}"

class VcCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
        self.current_song_timestamp = 0
        self.inactivity_check = 0
        self.max_inactivity = 300
        self.last_channel_interaction = ""
        self.supported_file_formats = ["aac", "aiff", "flac", "m4a", "mp3", "ogg", "wav", "wma", "avi", "mkv", "mov", "mp4"] #alphabetical order, audio formats followed by video formats

    @app_commands.command(name="connect", description="Connects the bot to the voice channel you are currently in")
    async def connect(self, interaction: discord.Interaction):
        try:
            voice_channel = interaction.user.voice.channel
            self.last_channel_interaction = interaction.channel_id
            await voice_channel.connect()
            self.vccheck_task.start(interaction)
            await interaction.response.send_message(embed=discord.Embed(description=f"Successfully connected to <#{str(voice_channel.id)}>!", color=0x00aeff), ephemeral=True)
        except AttributeError:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel it is currently in")
    async def disconnect(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer() #avoids the "The application did not respond" message if the command takes too long to respond

            voice_channel = interaction.user.voice.channel
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            self.vccheck_task.cancel()
            if bot_voice_client.source != None or bot_voice_client.is_playing() == True:
                bot_voice_client.stop()
                await asyncio.sleep(1.5) #allows the bot to properly end the file before disconnecting
            await bot_voice_client.disconnect()
            self.__init__(self.bot)
            await interaction.followup.send(embed=discord.Embed(description=f"Successfully disconnected from <#{str(bot_voice_client.channel.id)}>!", color=0x00aeff), ephemeral=True)
        except AttributeError:
            await interaction.followup.send(embed=discord.Embed(description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="play", description="Plays a file or link in the voice channel you are currently in, or adds it to the queue if its not ")
    @app_commands.describe(link="A link to an audio or video file. Needs to be an actual file", verbose="show all metadata")
    async def play(self, interaction: discord.Interaction, attachment: Optional[discord.Attachment], link: Optional[str], verbose: Optional[bool] ):
        try:
            await interaction.response.defer() #avoids the "The application did not respond" message if the command takes too long to respond

            voice_channel = interaction.user.voice.channel
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            self.last_channel_interaction = interaction.channel_id
            #check if only one file/attachment is attached and if that file/attachment is correct
            filecheck = None
            ffmpegcheck = None
            file = None
            if attachment and link:
                await interaction.followup.send(embed=discord.Embed(description="Please do not upload an attachment and a link at the same time.", color=0xff0000), ephemeral=True)
                filecheck = 1
            elif attachment:
                file = attachment.url
                filecheck = 0
            elif link:
                file = link
                filecheck = 0
            else:
                await interaction.followup.send(embed=discord.Embed(description="No media uploaded.", color=0xff0000), ephemeral=True)
                filecheck = 2
            
            #check if file format is supported
            if filecheck == 0:
                for format in self.supported_file_formats:
                    filecheck = 3
                    if file.endswith(f".{format}"):
                        filecheck = 0
                        break

            if filecheck == 3:
                await interaction.followup.send(embed=discord.Embed(description="File is not in a supported format!", color=0xff0000), ephemeral=True)
            elif filecheck == 0:
                #get song len
                ffmpegcheck = os.system(f'ffprobe -i {file} -show_entries format=duration -of csv="p=0" > time.txt')
                if ffmpegcheck == 1:
                    raise FileNotFoundError
                with open("time.txt",'r') as myfile:
                    time_sec = float(str(myfile.readlines()[0]).strip())    
                time_hms = sec_to_hms(time_sec)
                    
                print(f"song is {time_sec} secs long") 
                #get metadata
                os.system(f'ffmpeg -y -i {file} -f ffmetadata metadata.txt')
                await asyncio.sleep(2) #limit the "catch-up" effect as much as possible
                metadata = {}
                with open("metadata.txt",'r') as myfile:
                    lines = myfile.readlines()[1:]
                
                #convert lines to key-pair dic
                metabuild = []
                for i in lines:
                    try:
                        key,value= i.split('=',1)
                        key = key.upper().strip()
                        value = value.strip()
                        metabuild.append([key,value])
                    except:
                        print(f"\033[93mWARNING: Line {i.strip()} couldn't be built into metadata!\033[0m")
                
                metadata = dict(metabuild)
                
                dirname, fname = os.path.split(file)
                
                def ifkey(key):
                    return(f"{key.title()}: `{metadata.get(key).strip()}`\n ") if key and metadata.get(key) is not None else ""
                
                def metaout():
                    outstr = ""
                    for key in metadata:
                        outstr += ifkey(key)
                    return outstr
                
                if metadata.get('TITLE') and metadata.get('ARTIST'):
                    title = f"{metadata.get('ARTIST').strip()} - {metadata.get('TITLE').strip()}"
                    desc = f"{ifkey('ALBUM')} {ifkey('TRACK')} {ifkey('DATE')} Length: `{time_hms}`\n file name: `{fname}`"
                    qdesc = f"Length: `{time_hms}`"
                    vdesc = f" {metaout()} \n  Length: `{time_hms}` \n File Name: `{fname}`"
                else: 
                    title = fname
                    desc = f'Length: `{time_hms}`'
                    qdesc = desc
                    vdesc = f" {metaout()} \n  Length: `{time_hms}`"

                #make song dict
                qbuild = { "file": file, "metadata": metadata, "title": title, "desc": desc, "qdesc": qdesc, "vdesc": vdesc, "user": interaction.user, "time_sec": time_sec, "time_hms": time_hms}
                if verbose:
                    desc = vdesc

                #actually play stuff            
                if bot_voice_client == None or bot_voice_client.is_playing() == False:
                    if bot_voice_client == None:
                        vc = await voice_channel.connect()
                        self.song_queue.append(qbuild)
                        vc.play(discord.FFmpegOpusAudio(source=self.song_queue[0].get("file")))
                        self.vccheck_task.start(interaction)
                    else:
                        self.song_queue.append(qbuild)
                        bot_voice_client.play(discord.FFmpegOpusAudio(source=self.song_queue[0].get("file")))

                    await interaction.followup.send(embed=discord.Embed(title =f"Now playing `{title}`", description= desc +"\n", color=0x00aeff).set_footer(text = f"Requested by {self.song_queue[0].get('user')}", icon_url = self.song_queue[0].get('user').avatar.url))
                elif bot_voice_client.is_playing() == True:
                    self.song_queue.append(qbuild)
                    await interaction.followup.send(embed=discord.Embed(title=f"Added `{title}` to queue", description= desc, color=0x00aeff).set_footer(text = f"Requested by {self.song_queue[0].get('user')}", icon_url = self.song_queue[0].get('user').avatar.url))
        except AttributeError:
            await interaction.followup.send(embed=discord.Embed(description="You are not connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise
        except FileNotFoundError:
            await interaction.followup.send(embed=discord.Embed(description="Invalid file or file corrupted.", color=0xff0000), ephemeral=True)
            raise
        except:
            await interaction.followup.send(embed=discord.Embed(title="An error has occured while executing the command.", description="Please try again or contact the bot owner if you see this again.", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="seek", description="Sets the play position to the specified timestamp")
    @app_commands.describe(timestamp="(in seconds)")
    async def seek(self, interaction: discord.Integration, timestamp: float):
        try:
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            bot_voice_client.source = discord.FFmpegOpusAudio(source=self.song_queue[0].get("file"), before_options=f"-ss {str(timestamp)}")
            self.current_song_timestamp = timestamp
            await interaction.response.send_message(embed=discord.Embed(description=f"File seeked to position {sec_to_hms(timestamp)}", color=0x00aeff))
        except AttributeError:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="pause", description="Pauses the file")
    async def pause(self, interaction: discord.Interaction):
        try:
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            bot_voice_client.pause()
            await interaction.response.send_message(embed=discord.Embed(description="File paused.", color=0x00aeff))
        except AttributeError:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise

    @app_commands.command(name="resume", description="Resumes the file")
    async def resume(self, interaction: discord.Interaction):
        try:
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            bot_voice_client.resume()
            await interaction.response.send_message(embed=discord.Embed(description="File resumed.", color=0x00aeff))
        except AttributeError:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise

    @app_commands.command(name="skip", description="Skips the file")
    async def skip(self, interaction: discord.Interaction):
        try:
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            bot_voice_client.stop()
            await interaction.response.send_message(embed=discord.Embed(description="File stopped.", color=0x00aeff))
        except AttributeError:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise

    @app_commands.command(name="stop", description="Stops playing and clears the queue")
    async def stop(self, interaction: discord.Interaction):
        try:
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            self.song_queue.clear()
            bot_voice_client.stop()
            await interaction.response.send_message(embed=discord.Embed(description="File stopped and queue cleared.", color=0x00aeff))
        except AttributeError:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="song", description="get info on a song")
    @app_commands.describe(queue_position="(0 for the song currently playing)")
    async def song(self, interaction: discord.Interaction, queue_position: Optional[int], verbose: Optional[bool]):
        try:
            id = 0
            queue_position_err = 0
            if queue_position:
                if queue_position > len(self.song_queue)-1:
                    await interaction.response.send_message(embed=discord.Embed(description=f"Queue position {queue_position} doesn't exist.", color=0xff0000))
                    queue_position_err = 1
                else: id = queue_position
            
            if queue_position_err == 0:
                if verbose:
                    desc = f"**{self.song_queue[id].get('title')}** \n {self.song_queue[id].get('vdesc')}"
                else:
                    desc = f"**{self.song_queue[id].get('title')}** \n {self.song_queue[id].get('desc')}"

                song_embed = discord.Embed(description=desc, color=0x00aeff)
                song_embed.set_footer(text = f"Requested by {self.song_queue[id].get('user')}", icon_url = self.song_queue[id].get('user').avatar.url)

                if id == 0:
                    song_percentage = self.current_song_timestamp/self.song_queue[id].get('time_sec')
                    blue_squares = round(song_percentage*10)
                    white_squares = 10-blue_squares
                    display = f"🔷{'🟦'*blue_squares}{'⬜'*white_squares}🔷"

                    song_embed.add_field(name="Position", value=f"{display}\n{sec_to_hms(self.current_song_timestamp)}/{self.song_queue[id].get('time_hms')}")

                await interaction.response.send_message(embed=song_embed)
        except IndexError:
            await interaction.response.send_message(embed=discord.Embed(description=f"No song is currently playing.", color=0xff0000))
            raise
        except:
            await interaction.response.send_message(embed=discord.Embed(title="An error has occured while executing the command.", description="Please try again or contact the bot owner if you see this again.", color=0xff0000), ephemeral=True)
            raise
            
    @app_commands.command(name="queue", description="see the queue of songs")
    async def queue(self, interaction: discord.Interaction, page: Optional[int], verbose: Optional[bool]):
        try:
            pagelen = 5
            if not page or page < 1:
                page = 1
                
            page_m = pagelen * page
            max_page = math.ceil(len(self.song_queue)/pagelen)
            
            if len(self.song_queue) == 0:
                await interaction.response.send_message(embed=discord.Embed(description="Queue is currently empty.", color=0x00aeff))
            elif page > max_page:
                await interaction.response.send_message(embed=discord.Embed(description="Not enough songs in the queue to display this page.", color=0x00aeff))
            else:
                queuebuild = discord.Embed(title="Queue",color=0x00aeff)
                i = page_m - pagelen
                while i < len(self.song_queue) and i < page_m:
                    if i == 0:
                        queuebuild.add_field(name=f"Now playing `{self.song_queue[i].get('title')}` \n", value=f"{sec_to_hms(self.current_song_timestamp)}/{self.song_queue[i].get('time_hms')}", inline=False)
                    else:    
                        queuebuild.add_field(name=f"{i}. `{self.song_queue[i].get('title')}` \n", value=f"{self.song_queue[i].get('time_hms') }",inline=False)
                    i+=1

                queuebuild.set_footer(text=f"Page {page}/{max_page}")

                await interaction.response.send_message(embed=queuebuild)
        except:
            await interaction.response.send_message(embed=discord.Embed(title="An error has occured while executing the command.", description="Please try again or contact the bot owner if you see this again.", color=0xff0000), ephemeral=True)
            raise
            
    #constantly checks the vc instance
    #not sure if discord.utilis.get does an api request (i assume it does), might be an issue if too many requests are made but its only on 2 servers rn so idc
    @tasks.loop(seconds=0.5)
    async def vccheck_task(self, interaction):
        try:
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

            if bot_voice_client.is_paused():
                pass
            elif bot_voice_client.source == None or bot_voice_client.is_playing() == False:
                self.current_song_timestamp = 0
                self.inactivity_check += 0.5

                if len(self.song_queue) == 1:
                    del self.song_queue[0]
                elif len(self.song_queue) > 1:
                    del self.song_queue[0]
                    bot_voice_client.play(discord.FFmpegOpusAudio(source=self.song_queue[0].get("file")))
                    await self.bot.get_channel(self.last_channel_interaction).send(embed=discord.Embed(title =f"Now playing `{self.song_queue[0].get('title')}`", description=f"{self.song_queue[0].get('desc')} \n", color=0x00aeff).set_footer(text = f"Requested by {self.song_queue[0].get('user')}", icon_url = self.song_queue[0].get('user').avatar.url))
                
                #check if bot has been inactive for too long
                if self.inactivity_check > self.max_inactivity:
                    await bot_voice_client.disconnect()
                    await self.bot.get_channel(self.last_channel_interaction).send(embed=discord.Embed(description=f"Bot has been connected to the voice channel for too long and has been disconnected to avoid excessive bandwidth usage and requests to the Discord API.", color=0x00aeff))
                    self.__init__(self.bot)
                    self.vccheck_task.cancel()
            else:
                self.current_song_timestamp += 0.5
        except:
            raise
            
async def setup(bot):
    await bot.add_cog(VcCog(bot))
