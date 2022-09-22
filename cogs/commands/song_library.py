from distutils.log import error
from operator import inv
import discord
from discord import app_commands
from discord.ext import commands
import spotipy

from main import db
from main import sp

class SongLibraryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rebuild_song_library", description="Deletes the entire song library and rebuilds it")
    @app_commands.checks.has_permissions(administrator=True)
    async def rebuild_song_library(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message(embed=discord.Embed(
                    title="rebuilding song library...", 
                    description="this might take some time.", 
                    color=0xff0000), ephemeral=True)
            db.clear_song_library()
            db.create_song_library()
            await interaction.edit_original_response(embed=discord.Embed(
                    title="song library rebuilt successfully!", 
                    color=0xff0000))
        except:
            await interaction.edit_original_response(embed=discord.Embed(
                    title="ERROR THE BOT IS GOING TO EXPLODE (jk)", 
                    color=0xff0000))
            raise

    @app_commands.command(name="add_song_to_presence_queue", description="Adds a song in the presence queue for Rin to listen to")
    @app_commands.describe(url="URL of the song (Spotify only, single tracks only. No albums or playlists)")
    async def add_song_to_presence_queue(self, interaction: discord.Interaction, url: str):
        if "open.spotify.com/track/" in url:
            try:
                user_id = interaction.user.id
                artists = ""
                artist_count = 0
                for artist in sp.track(url)['album']['artists']:
                    artist_count += 1
                    if artist_count == 1:
                        artists = artist['name']
                    else:
                        artists = artists + ", " + artist['name']
                song_title = sp.track(url)['name']
                album = sp.track(url)['album']['name']
                length_in_seconds = int(sp.track(url)['duration_ms']/1000)

                song_order = db.fetchone_singlecolumn(0, "SELECT song_order FROM bot_user_song_library ORDER BY song_order DESC LIMIT 1")
                if song_order == None:
                    db.update_db("INSERT INTO bot_user_song_library(user_id, artist, song_title, album, length_in_seconds, song_order) VALUES (?, ?, ?, ?, ?, 1)", user_id, artists, song_title, album, length_in_seconds)
                else:
                    db.update_db("INSERT INTO bot_user_song_library(user_id, artist, song_title, album, length_in_seconds, song_order) VALUES (?, ?, ?, ?, ?, ?)", user_id, artists, song_title, album, length_in_seconds, song_order+1)
                await interaction.response.send_message(embed=discord.Embed(title="Song successfully added to queue!", description="**" + song_title + "** by " + artists + "\nfrom album *" + album + "*", color=0x00aeff), ephemeral=True)
            except spotipy.exceptions.SpotifyException as err:
                description = ""
                match err.http_status:
                    case 400:
                        description = "Invalid track ID (" + str(err.http_status) + ")"
                    case 403:
                        description = "Forbidden (" + str(err.http_status) + ")."
                    case 404:
                        description = "Track was not found (" + str(err.http_status) + ")"
                    case 429:
                        description = "Rate limit exceeded (" + str(err.http_status) + "), wait a few minutes and try again. If you see this again, please contact <@171000921927581696>!"
                    case 500:
                        description = "Internal server error (" + str(err.http_status) + "). That's on Spotify's side, sorry :("
                    case 502:
                        description = "Bad Gateway (" + str(err.http_status) + "). That's on Spotify's side, sorry :("
                    case _:
                        description = "An error has occurred (" + str(err.http_status) + "). If you see this, please contact <@171000921927581696>!"
                await interaction.response.send_message(embed=discord.Embed(title="An error has occurred while retrieving the song", description=description, color=0xff0000), ephemeral=True)
                raise
        else:
            await interaction.response.send_message(embed=discord.Embed(title="URL is invalid!", description="Make sure to only use a correct Spotify link and only single tracks (no playlists or albums!)", color=0xff0000), ephemeral=True)

async def setup(bot):
    await bot.add_cog(SongLibraryCog(bot), guilds = [discord.Object(id = 849034525861740571)])