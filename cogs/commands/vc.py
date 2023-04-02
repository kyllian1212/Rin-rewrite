"""_summary_

Raises:
    FileNotFoundError: _description_

Returns:
    _type_: _description_
"""
import asyncio
import os
from typing import Optional
import math
import json

import discord
from discord import app_commands
from discord.ext import commands, tasks

import cogs.tasks.song_presence as songp
import templates.embeds as embeds

from main import BOT_ID

# pitch stuff: `, options="-af asetrate=44100*0.9"` check https://stackoverflow.com/questions/53374590/ffmpeg-change-tone-frequency-keep-length-pitch-audio
# add volume/speed/pitch/equalizer/reverb/reverse/bitrate eventually


def sec_to_hms(seconds: int) -> str:
    """converts seconds to hours, seconds, and minutes

    Args:
        seconds (int): number of seconds

    Returns:
        str: returns seconds to a formatted string that is formatted by hours, minutes, and seconds
    """
    seconds_round = round(seconds)
    minute, second = divmod(seconds_round, 60)
    hour, minute = divmod(minute, 60)
    if hour:
        h_str = f"{hour}:"
        m_str = f"{minute:02d}"
    else:
        h_str = ""
        m_str = minute
    return f"{h_str}{m_str}:{second:02d}"

def mmss_to_sec(mmss):
    try:
        m,s = mmss.split(":")
        return((int(m) * 60)+ int(s))
    except:
        return(f"{mmss} is not a number")

class VcCog(commands.Cog):
    """Cog that handles voice channel interactions

    Args:
        commands (Cog): base class used for all cogs
    """

    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
        self.queue_position = -1
        self.current_song_timestamp = 0
        self.inactivity_check = 0
        self.max_inactivity = 300
        self.last_channel_interaction = ""
        self.supported_file_formats = [
            "aac",
            "aiff",
            "flac",
            "m4a",
            "mp3",
            "ogg",
            "wav",
            "wma",
            "avi",
            "mkv",
            "mov",
            "mp4",
        ]  # alphabetical order, audio formats followed by video formats
        self.tracklist_channel_id = None
        self.played_tracks = []

    @app_commands.command(
        name="connect",
        description="Connects the bot to the voice channel you are currently in",
    )
    async def connect(self, interaction: discord.Interaction):
        """connects to a voice channel

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            voice_channel = interaction.user.voice.channel
            self.last_channel_interaction = interaction.channel_id
            guild = self.bot.get_guild(voice_channel.guild.id)
            bot_member = await guild.fetch_member(BOT_ID)

            await voice_channel.connect()

            # tasks
            self.vc_check_task.start(interaction)
            self.tracklisting.start()
            songp.SongPresenceCog.presence_task.stop()
            await self.bot.change_presence(activity=None)

            # check if bot is in a stage channel instead of a voice channel and if so, let it speak
            if (
                voice_channel.type.name == "stage_voice"
                and bot_member.voice.suppress is True
            ):
                await bot_member.edit(suppress=False)

            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"Successfully connected to <#{str(voice_channel.id)}>!",
                    color=0x00AEFF,
                ),
                ephemeral=True,
            )
        except AttributeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="You are not connected to a voice channel!",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(
        name="disconnect",
        description="Disconnects the bot from the voice channel it is currently in",
    )
    async def disconnect(self, interaction: discord.Interaction):
        """disconnects from the voice channel

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            bot_voice_client = discord.utils.get(
                self.bot.voice_clients, guild=interaction.guild
            )

            # tasks
            self.vc_check_task.cancel()
            self.tracklisting.cancel()
            songp.SongPresenceCog.presence_task.start()

            if (
                bot_voice_client.source is not None
                or bot_voice_client.is_playing() is True
            ):
                bot_voice_client.stop()
                await asyncio.sleep(
                    1.5
                )  # allows the bot to properly end the file before disconnecting
            await bot_voice_client.disconnect()
            self.__init__(
                self.bot
            )  # TODO: we shouldn't instantiate here. handle refresh elsewhere
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"Successfully disconnected from <#{str(bot_voice_client.channel.id)}>!",
                    color=0x00AEFF,
                ),
                ephemeral=True,
            )
        except AttributeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(
        name="play",
        description="Plays a file or link in the voice channel you are currently in, or adds it to the queue if its not",
    )
    @app_commands.describe(
        link="A link to an audio or video file. Needs to be an actual file",
        verbose="show all metadata",
    )
    async def play(
        self,
        interaction: discord.Interaction,
        attachment: Optional[discord.Attachment],
        link: Optional[str],
        tracklist: Optional[discord.Attachment],
        verbose: Optional[bool],
    ) -> str:
        """Plays a file or link in the voice channel that you are currently in, or adds it to the queue if its not

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            attachment (Optional[discord.Attachment]): File that should be played or queued
            link (Optional[str]): link to a song that should be played or queued
            verbose (Optional[bool]): flag to show verbose logs

        Raises:
            FileNotFoundError: raised if file is not found or is corrupted

        Returns:
            str: the message that is sent when the file is added correctly
        """
        try:
            await interaction.response.defer()  # avoids the "The application did not respond" message if the command takes too long to respond

            voice_channel = interaction.user.voice.channel
            bot_voice_client = discord.utils.get(
                self.bot.voice_clients, guild=interaction.guild
            )
            self.last_channel_interaction = interaction.channel_id
            guild = self.bot.get_guild(voice_channel.guild.id)
            bot_member = await guild.fetch_member(BOT_ID)

            # check if only one file/attachment is attached and if that file/attachment is correct
            file_check = None
            ffmpeg_check = None
            file = None
            if attachment and link:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="Please do not upload an attachment and a link at the same time.",
                        color=0xFF0000,
                    ),
                    ephemeral=True,
                )
                file_check = 1
            elif attachment:
                file = attachment.url
                file_check = 0
            elif link:
                file = link
                file_check = 0
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="No media uploaded.", color=0xFF0000
                    ),
                    ephemeral=True,
                )
                file_check = 2

            # check if tracklist is json
            if not tracklist.filename.endswith(".json"):
                tracklist = None

            # check if file format is supported
            if file_check == 0:
                for file_format in self.supported_file_formats:
                    file_check = 3
                    if file.endswith(f".{file_format}"):
                        file_check = 0
                        break

            if file_check == 3:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="File is not in a supported format!", color=0xFF0000
                    ),
                    ephemeral=True,
                )
            elif file_check == 0:
                # get song len
                ffmpeg_check = os.system(
                    f'ffprobe -i {file} -show_entries format=duration -of csv="p=0" > time.txt'
                )
                if ffmpeg_check == 1:
                    raise FileNotFoundError
                with open(
                    "time.txt",
                    "r",
                ) as myfile:
                    time_sec = float(str(myfile.readlines()[0]).strip())
                time_hms = sec_to_hms(time_sec)

                print(f"song is {time_sec} secs long")
                # get metadata
                os.system(f"ffmpeg -y -i {file} -f ffmetadata metadata.txt")
                await asyncio.sleep(
                    2
                )  # limit the "catch-up" effect as much as possible
                metadata = {}
                with open("metadata.txt", "r") as myfile:
                    lines = myfile.readlines()[1:]

                # convert lines to key-pair dic
                metabuild = []
                for i in lines:
                    try:
                        key, value = i.split("=", 1)
                        key = key.upper().strip()
                        value = value.strip()
                        metabuild.append([key, value])
                    except:
                        print(
                            f"\033[93mWARNING: Line {i.strip()} couldn't be built into metadata!\033[0m"
                        )

                metadata = dict(metabuild)

                dirname, fname = os.path.split(file)

                def ifkey(key):
                    return (
                        (f"{key.title()}: `{metadata.get(key).strip()}`\n ")
                        if key and metadata.get(key) is not None
                        else ""
                    )

                def metaout():
                    outstr = ""
                    for key in metadata:
                        outstr += ifkey(key)
                    return outstr

                if metadata.get("TITLE") and metadata.get("ARTIST"):
                    title = f"{metadata.get('ARTIST').strip()} - {metadata.get('TITLE').strip()}"
                    desc = f"{ifkey('ALBUM')} {ifkey('TRACK')} {ifkey('DATE')} Length: `{time_hms}`\n file name: `{fname}`"
                    qdesc = f"Length: `{time_hms}`"
                    vdesc = (
                        f" {metaout()} \n  Length: `{time_hms}` \n File Name: `{fname}`"
                    )
                else:
                    title = fname
                    desc = f"Length: `{time_hms}`"
                    qdesc = desc
                    vdesc = f" {metaout()} \n  Length: `{time_hms}`"

                # make song dict
                qbuild = {
                    "file": file,
                    "metadata": metadata,
                    "title": title,
                    "desc": desc,
                    "qdesc": qdesc,
                    "vdesc": vdesc,
                    "user": interaction.user,
                    "time_sec": time_sec,
                    "time_hms": time_hms,
                    "tracklist": tracklist
                }
                if verbose:
                    desc = vdesc

                # actually play stuff
                if bot_voice_client is None or bot_voice_client.is_playing() is False:
                    if bot_voice_client is None:
                        vc = await voice_channel.connect()
                        self.song_queue.append(qbuild)

                        # check if bot is in a stage channel instead of a voice channel and if so, let it speak
                        if (
                            voice_channel.type.name == "stage_voice"
                            and bot_member.voice.suppress is True
                        ):
                            await bot_member.edit(suppress=False)

                        vc.play(
                            discord.FFmpegOpusAudio(
                                source=self.song_queue[0].get("file")
                            )
                        )

                        # tasks
                        self.vc_check_task.start(interaction)
                        self.tracklisting.start()
                        songp.SongPresenceCog.presence_task.stop()
                        await self.bot.change_presence(activity=None)
                    else:
                        self.song_queue.append(qbuild)
                        # check if bot is in a stage channel instead of a voice channel and if so, let it speak
                        if (
                            voice_channel.type.name == "stage_voice"
                            and bot_member.voice.suppress is True
                        ):
                            await bot_member.edit(suppress=False)
                        bot_voice_client.play(
                            discord.FFmpegOpusAudio(
                                source=self.song_queue[0].get("file")
                            )
                        )

                    await interaction.followup.send(
                        embed=discord.Embed(
                            title=f"Now playing `{title}`",
                            description=desc + "\n",
                            color=0x00AEFF,
                        ).set_footer(
                            text=f"Requested by {self.song_queue[0].get('user')}",
                            icon_url=self.song_queue[0].get("user").avatar.url,
                        )
                    )
                elif bot_voice_client.is_playing() is True:
                    self.song_queue.append(qbuild)
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title=f"Added `{title}` to queue",
                            description=desc,
                            color=0x00AEFF,
                        ).set_footer(
                            text=f"Requested by {self.song_queue[0].get('user')}",
                            icon_url=self.song_queue[0].get("user").avatar.url,
                        )
                    )
        except AttributeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="You are not connected to a voice channel!",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            raise
        except FileNotFoundError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="Invalid file or file corrupted.", color=0xFF0000
                ),
                ephemeral=True,
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(
        name="seek", description="Sets the play position to the specified timestamp"
    )
    @app_commands.describe(timestamp="(in seconds)")
    async def seek(self, interaction: discord.Interaction, timestamp: float):
        """sets the play position to the specified timestamp

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            timestamp (float): the timestamp of the song in seconds
        """
        try:
            await interaction.response.defer()
            bot_voice_client = discord.utils.get(
                self.bot.voice_clients, guild=interaction.guild
            )
            bot_voice_client.source = discord.FFmpegOpusAudio(
                source=self.song_queue[0].get("file"),
                before_options=f"-ss {str(timestamp)}",
            )
            self.current_song_timestamp = timestamp
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"File sought to position {sec_to_hms(timestamp)}",
                    color=0x00AEFF,
                )
            )
        except AttributeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="pause", description="Pauses the file")
    async def pause(self, interaction: discord.Interaction):
        """pauses the current playing file

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            bot_voice_client = discord.utils.get(
                self.bot.voice_clients, guild=interaction.guild
            )
            bot_voice_client.pause()
            await interaction.followup.send(
                embed=discord.Embed(description="File paused.", color=0x00AEFF)
            )
        except AttributeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="resume", description="Resumes the file")
    async def resume(self, interaction: discord.Interaction):
        """resumes the current playing file

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            bot_voice_client = discord.utils.get(
                self.bot.voice_clients, guild=interaction.guild
            )
            bot_voice_client.resume()
            await interaction.followup.send(
                embed=discord.Embed(description="File resumed.", color=0x00AEFF)
            )
        except AttributeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="skip", description="Skips the file")
    async def skip(self, interaction: discord.Interaction):
        """skips the current playing file

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            bot_voice_client = discord.utils.get(
                self.bot.voice_clients, guild=interaction.guild
            )
            bot_voice_client.stop()
            await interaction.followup.send(
                embed=discord.Embed(description="File stopped.", color=0x00AEFF)
            )
        except AttributeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="stop", description="Stops playing and clears the queue")
    async def stop(self, interaction: discord.Interaction):
        """stops playing the file and clears the queue

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            await interaction.response.defer()
            bot_voice_client = discord.utils.get(
                self.bot.voice_clients, guild=interaction.guild
            )
            self.song_queue.clear()
            bot_voice_client.stop()
            await interaction.followup.send(
                embed=discord.Embed(
                    description="File stopped and queue cleared.", color=0x00AEFF
                )
            )
        except AttributeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="You are not connected to a voice channel, or the bot currently isn't connected to a voice channel!",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="song", description="get info on a song")
    @app_commands.describe(queue_position="(0 for the song currently playing)")
    async def song(
        self,
        interaction: discord.Interaction,
        queue_position: Optional[int],
        verbose: Optional[bool],
    ):
        """gets the info on the current playing song

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            queue_position (Optional[int]): the position of the requested file in the queue
            verbose (Optional[bool]): flag to toggle verbose logs
        """
        try:
            await interaction.response.defer()
            queue_id = 0
            queue_position_err = 0
            if queue_position:
                if queue_position > len(self.song_queue) - 1:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            description=f"Queue position {queue_position} doesn't exist.",
                            color=0xFF0000,
                        )
                    )
                    queue_position_err = 1
                else:
                    queue_id = queue_position

            if queue_position_err == 0:
                if verbose:
                    desc = f"**{self.song_queue[queue_id].get('title')}** \n {self.song_queue[queue_id].get('vdesc')}"
                else:
                    desc = f"**{self.song_queue[queue_id].get('title')}** \n {self.song_queue[queue_id].get('desc')}"

                song_embed = discord.Embed(description=desc, color=0x00AEFF)
                song_embed.set_footer(
                    text=f"Requested by {self.song_queue[queue_id].get('user')}",
                    icon_url=self.song_queue[queue_id].get("user").avatar.url,
                )

                if queue_id == 0:
                    song_percentage = self.current_song_timestamp / self.song_queue[
                        queue_id
                    ].get("time_sec")
                    blue_squares = round(song_percentage * 10)
                    white_squares = 10 - blue_squares
                    display = f"🔷{'🟦'*blue_squares}{'⬜'*white_squares}🔷"

                    song_embed.add_field(
                        name="Position",
                        value=f"{display}\n{sec_to_hms(self.current_song_timestamp)}/{self.song_queue[queue_id].get('time_hms')}",
                    )

                await interaction.followup.send(embed=song_embed)
        except IndexError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="No song is currently playing.", color=0xFF0000
                )
            )
            raise
        except:
            await embeds.error_executing_command(interaction)
            raise

    @app_commands.command(name="queue", description="see the queue of songs")
    async def queue(
        self,
        interaction: discord.Interaction,
        page: Optional[int],
    ):
        """retrieves the queue of songs

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            page (Optional[int]): the page number of the queue
            verbose (Optional[bool]): flag to toggle verbose logs
        """
        try:
            await interaction.response.defer()
            page_len = 5
            if not page or page < 1:
                page = 1

            page_m = page_len * page
            max_page = math.ceil(len(self.song_queue) / page_len)

            if len(self.song_queue) == 0:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="Queue is currently empty.", color=0x00AEFF
                    )
                )
            elif page > max_page:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="Not enough songs in the queue to display this page.",
                        color=0x00AEFF,
                    )
                )
            else:
                queue_build = discord.Embed(title="Queue", color=0x00AEFF)
                i = page_m - page_len
                while i < len(self.song_queue) and i < page_m:
                    if i == 0:
                        queue_build.add_field(
                            name=f"Now playing `{self.song_queue[i].get('title')}` \n",
                            value=f"{sec_to_hms(self.current_song_timestamp)}/{self.song_queue[i].get('time_hms')}",
                            inline=False,
                        )
                    else:
                        queue_build.add_field(
                            name=f"{i}. `{self.song_queue[i].get('title')}` \n",
                            value=f"{self.song_queue[i].get('time_hms') }",
                            inline=False,
                        )
                    i += 1

                queue_build.set_footer(text=f"Page {page}/{max_page}")

                await interaction.followup.send(embed=queue_build)
        except:
            await embeds.error_executing_command(interaction)
            raise
 
    @app_commands.command(
            name="loop", 
            description="see the queue of songs"
            )
    @app_commands.choices(queue_setting=[
        app_commands.Choice(name="Disabled", value="disabled"),
        app_commands.Choice(name="Queue", value="queue"),
        app_commands.Choice(name="Song", value="song"),
    ])
    async def loop(
        self,
        interaction: discord.Interaction,
        queue_setting: app_commands.Choice[str]
    ):
        """loop

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            page (Optional[int]): the page number of the queue
            verbose (Optional[bool]): flag to toggle verbose logs
        """
        if (queue_setting.value == 'disabled'):
            pass
        elif (queue_setting.value == 'queue'):
            pass
        elif (queue_setting.value == "song"):
            pass

    @app_commands.command(
            name="set_tracklist_channel", 
            description="Sets the channel in which tracklists will be sent"
            )
    @app_commands.describe(channel="The channel in which the tracklists will be sent")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_tracklist_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        """Sets the channel in which tracklists will be sent

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
            channel (discord.Channel): The channel in which the tracklists will be sent
        """
        try:
            await interaction.response.defer(ephemeral=True)
            self.tracklist_channel_id = channel.id
            await interaction.followup.send(embed=discord.Embed(
                description=f"Tracklisting channel successfully set to <#{channel.id}>!",
                color=0x00AEFF
                ),
                ephemeral=True
            )
        except:
            await embeds.error_executing_command(interaction)
            raise

    # constantly checks the vc instance
    # not sure if discord.utilis.get does an api request (i assume it does), might be an issue if too many requests are made but its only on 2 servers rn so idc
    @tasks.loop(seconds=0.5)
    async def vc_check_task(self, interaction: discord.Interaction):
        """checks the vc instance

        Args:
            interaction (discord.Interaction): Discord interaction. Occurs when user does notifiable action (e.g. slash commands)
        """
        try:
            voice_channel = interaction.user.voice.channel
            bot_voice_client = discord.utils.get(
                self.bot.voice_clients, guild=interaction.guild
            )

            if bot_voice_client.is_paused():
                pass
            elif (
                bot_voice_client.source is None
                or bot_voice_client.is_playing() is False
            ):
                guild = self.bot.get_guild(voice_channel.guild.id)
                bot_member = await guild.fetch_member(BOT_ID)

                self.current_song_timestamp = 0
                self.inactivity_check += 0.5
                self.played_tracks = []

                if len(self.song_queue) == 1:
                    del self.song_queue[0]
                elif len(self.song_queue) > 1:
                    del self.song_queue[0]

                    # check if bot is in a stage channel instead of a voice channel and if so, let it speak
                    if (
                        voice_channel.type.name == "stage_voice"
                        and bot_member.voice.suppress is True
                    ):
                        await bot_member.edit(suppress=False)

                    bot_voice_client.play(
                        discord.FFmpegOpusAudio(source=self.song_queue[0].get("file"))
                    )

                    songp.SongPresenceCog.presence_task.stop()
                    await self.bot.get_channel(self.last_channel_interaction).send(
                        embed=discord.Embed(
                            title=f"Now playing `{self.song_queue[0].get('title')}`",
                            description=f"{self.song_queue[0].get('desc')} \n",
                            color=0x00AEFF,
                        ).set_footer(
                            text=f"Requested by {self.song_queue[0].get('user')}",
                            icon_url=self.song_queue[0].get("user").avatar.url,
                        )
                    )

                # check if bot has been inactive for too long
                if self.inactivity_check > self.max_inactivity:
                    await bot_voice_client.disconnect()
                    await self.bot.get_channel(self.last_channel_interaction).send(
                        embed=discord.Embed(
                            description="Bot has been connected to the voice channel for too long and has been disconnected to avoid excessive bandwidth usage and requests to the Discord API.",
                            color=0x00AEFF,
                        )
                    )
                    self.__init__(
                        self.bot
                    )  # TODO: we shouldn't instantiate here. handle refresh elsewhere

                    # tasks
                    self.vc_check_task.cancel()
                    self.tracklisting.cancel()
                    songp.SongPresenceCog.presence_task.start()
            else:
                songp.SongPresenceCog.presence_task.stop()
                self.current_song_timestamp += 0.5
        except:
            self.vc_check_task.stop()
            self.tracklisting.cancel()
            songp.SongPresenceCog.presence_task.start()
            raise

    # tracklist task (wip)
    @tasks.loop(seconds=0.5)
    async def tracklisting(self):
        try:
            if (
                self.song_queue
                and self.song_queue[0].get("tracklist")
                and self.tracklist_channel_id
                is not None
            ):
                await self.song_queue[0].get("tracklist").save('/tracklist.json')
                with open('/tracklist.json', 'r') as json_file:
                    tracklist = json.load(json_file)
                    for i in tracklist.get("tracks"):
                        track_timestamp = mmss_to_sec(tracklist.get("tracks").get(i).get("timestamp"))
                        if (not i in self.played_tracks):
                            track = tracklist.get("tracks").get(i)
                            if self.current_song_timestamp > float(track_timestamp):
                                self.played_tracks.append(i)

                                title = f"Now playing `{track.get('artist')} - {track.get('title')}`"
                                desc = f"Performed by `{tracklist.get('performer')}` \n {sec_to_hms(self.current_song_timestamp)}/{self.song_queue[0].get('time_hms')}"
                                color_hold = tracklist.get('color')     
                                color = int(color_hold[1:], 16)
                                await self.bot.get_channel(self.tracklist_channel_id).send(embed=discord.Embed(title = title, description=desc, color = color))
                                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{track.get('artist')} - {track.get('title')}"))
        except Exception as e:
            raise


async def setup(bot: commands.Bot):
    """initializes the voice channel cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(VcCog(bot))
