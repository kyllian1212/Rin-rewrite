import discord
import os
from datetime import timedelta
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime
from typing import Optional
from main import db
from main import VERSION
import traceback

#everything needs try excepts but im just playing around rn
#pitch stuff: `, options="-af asetrate=44100*0.9"` check https://stackoverflow.com/questions/53374590/ffmpeg-change-tone-frequency-keep-length-pitch-audio
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
        self.last_channel_interaction = ""



    @app_commands.command(name="connect", description="Connects the bot to the voice channel you are currently in")
    async def connect(self, interaction: discord.Interaction):
        try:
            voice_channel = interaction.user.voice.channel
            await voice_channel.connect()
            self.vccheck_task.start(interaction)
            await interaction.response.send_message(embed=discord.Embed(description=f"Successfully connected to <#{str(voice_channel.id)}>!", color=0x00aeff), ephemeral=True)
        except AttributeError as error:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="disconnect", description="Disconnects the bot from the voice channel it is currently in")
    async def disconnect(self, interaction: discord.Interaction):
        #needs a check to see if its not connected
        try:
            voice_channel = interaction.user.voice.channel
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            self.vccheck_task.cancel()
            await bot_voice_client.disconnect()
            await interaction.response.send_message(embed=discord.Embed(description=f"Successfully disconnected from <#{str(bot_voice_client.channel.id)}>!", color=0x00aeff), ephemeral=True)
        except AttributeError as error:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel, or the bot currently isn't in a voice channel!", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="play", description="Plays a file or link in the voice channel you are currently in, or adds it to the queue if its not ")
    @app_commands.describe(link="a link to an audio or video file. needs to be an actual file", verbose="show all metadata")
    async def play(self, interaction: discord.Interaction, attachment: Optional[discord.Attachment], link: Optional[str], verbose: Optional[bool] ):
        #needs a file extension check, a queue system, and some other checks i cant remember on top of my head at the time i commit this
        try:
            voice_channel = interaction.user.voice.channel
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            self.last_channel_interaction = interaction.channel_id
            #check if only one file/attachment is attached and if that file/attachment is correct
            filecheck = None
            ffmpegcheck = None
            file = None
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
            
            #if not file.endswith(".mp3"):
            #    print("not a valid file")
            if filecheck == 0:
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
                metadata = {}
                with open("metadata.txt",'r') as myfile:
                    lines = myfile.readlines()[1:]
                
                #convert lines to key-pair dic
                metabuild = []
                for i in lines:
                    key,value= i.split('=',1)
                    key = key.upper().strip()
                    value = value.strip()
                    metabuild.append([key,value])        
                
                metadata = dict(metabuild)
                
                dirname, fname = os.path.split(file)
                
                def ifkey(key):
                    return(f"{key.title()}: `{metadata.get(key).strip()}`\n ") if key and metadata.get(key) is not None else ""
                
                def metaout():
                    outstr = ""
                    for key in metadata:
                        outstr += ifkey(key)
                    return outstr
                
                if metadata.get('TITLE'):
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
                        print(vc.source)
                    else:
                        self.song_queue.append(qbuild)
                        bot_voice_client.play(discord.FFmpegOpusAudio(source=self.song_queue[0].get("file")))
                        
                    
                    await interaction.response.send_message(embed=discord.Embed(title =f"now playing `{title}`", description= desc +"\n", color=0x00aeff).set_footer(text = f"requested by {self.song_queue[0].get('user')}", icon_url = self.song_queue[0].get('user').avatar.url))
                elif bot_voice_client.is_playing() == True:
                    self.song_queue.append(qbuild)
                    await interaction.response.send_message(embed=discord.Embed(title=f"added `{title}` to queue", description= desc, color=0x00aeff).set_footer(text = f"requested by {self.song_queue[0].get('user')}", icon_url = self.song_queue[0].get('user').avatar.url))
        except AttributeError as error:
            await interaction.response.send_message(embed=discord.Embed(description="You are not connected to a voice channel!", color=0xff0000), ephemeral=True)
            raise
        except FileNotFoundError as error:
            await interaction.response.send_message(embed=discord.Embed(description="Invalid file or file corrupted.", color=0xff0000), ephemeral=True)
            raise
        except:
            await interaction.response.send_message(embed=discord.Embed(title="An error has occured while executing the command.", description="Please try again or contact the bot owner if you see this again.", color=0xff0000), ephemeral=True)
            raise
    
    @app_commands.command(name="seek", description="Sets the play position to the specified timestamp")
    @app_commands.describe(timestamp="(in seconds)")
    async def seek(self, interaction: discord.Integration, timestamp: float):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.source = discord.FFmpegOpusAudio(source=self.song_queue[0].get("file"), before_options=f"-ss {str(timestamp)}")
        self.current_song_timestamp = timestamp
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
    async def skip(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        bot_voice_client.stop()
        await interaction.response.send_message(embed=discord.Embed(description="File stopped.", color=0x00aeff))

    @app_commands.command(name="stop", description="Stops playing and clears the queue")
    async def stop(self, interaction: discord.Interaction):
        bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        self.song_queue.clear()
        bot_voice_client.stop()
        await interaction.response.send_message(embed=discord.Embed(description="File stopped and queue cleared.", color=0x00aeff))
    
    @app_commands.command(name="song", description="get info on a song")
    async def song(self, interaction: discord.Interaction, song_number: Optional[int], verbose: Optional[bool]):
        id = 0
        if song_number:
            if song_number > len(self.song_queue):
                interaction.response.send_message(embed=discord.Embed(description=f"{song_number} is outside of range", color=0xff0000))
            else: id = song_number
            
        if verbose:
            desc = f"**{self.song_queue[id].get('title')}** \n {self.song_queue[id].get('vdesc')}"
        else:
            desc = f"**{self.song_queue[id].get('title')}** \n {self.song_queue[id].get('desc')}"
                
        await interaction.response.send_message(embed=discord.Embed(description=desc, color=0x00aeff))
            
    @app_commands.command(name="queue", description="see the queue of songs")
    async def queue(self, interaction: discord.Interaction, page: Optional[int], verbose: Optional[bool]):
        pagelen = 5
        if not page or page < 1:
            page = 1
            
        page_m = pagelen * page
        
        if len(self.song_queue) == 0:
           await interaction.response.send_message(embed=discord.Embed(description="queue is empty", color=0x00aeff))
        else:
            queuebuild = discord.Embed(title="Queue",color=0x00aeff)
            i = page_m - pagelen
            while i < len(self.song_queue) and i < page_m:
                if i == 0:
                    queuebuild.add_field(name=f"Now Playing `{self.song_queue[i].get('title')}` \n", value=f"{self.song_queue[i].get('time_hms')}",inline=False)
                else:    
                    queuebuild.add_field(name=f"{i}. `{self.song_queue[i].get('title')}` \n", value=f"{self.song_queue[i].get('time_hms') }",inline=False)
                i+=1
            await interaction.response.send_message(embed=queuebuild)
            
    #constantly checks the vc instance
    #not sure if discord.utilis.get does an api request (i assume it does), might be an issue if too many requests are made but its only on 2 servers rn so idc
    @tasks.loop(seconds=0.5)
    async def vccheck_task(self, interaction):
        try:
            bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if bot_voice_client.is_paused():
                pass
            elif bot_voice_client.source == None or bot_voice_client.is_playing() == False:
                # print("file is NOT playing")
                self.current_song_timestamp = 0
                self.inactivity_check += 0.5
                if len(self.song_queue) > 1:
                    del self.song_queue[0]
                    print(self.song_queue[0])
                    bot_voice_client.play(discord.FFmpegOpusAudio(source=self.song_queue[0].get("file")))
                    await self.bot.get_channel(self.last_channel_interaction).send(embed=discord.Embed(title =f"now playing `{self.song_queue[0].get('title')}`", description=f"{self.song_queue[0].get('desc')} \n", color=0x00aeff).set_footer(text = f"requested by {self.song_queue[0].get('user')}", icon_url = self.song_queue[0].get('user').avatar.url))
            else:
                # print("file is playing")
                self.current_song_timestamp += 0.5
                print(self.current_song_timestamp)
            # print(bot_voice_client.source)
            #    print(self.song_queue)
                print(self.song_queue[0].get('file'))
        except:
            raise
            
async def setup(bot):
    await bot.add_cog(VcCog(bot))
