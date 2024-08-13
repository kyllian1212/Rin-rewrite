"""
Threads Module
"""

# location and time stuff
from functools import lru_cache
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from timezonefinder import TimezoneFinder
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing import Optional
import dictdiffer
import os.path
import pickle

# https://developers.google.com/sheets/api/quickstart/python
# https://googleapis.github.io/google-api-python-client/docs/dyn/sheets_v4.spreadsheets.html#get
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]

# The ID and range of a sample spreadsheet.
sheet_range = "shows!A3:Z"

# dict of server ids and their forum/sheets
sdict = {
    "1001619464401457253": {  # testing server
        "forum": 1269823631106510991,
        "sheet": "10M3FRfDYWAj95O6eGvQ1y6kRRRfES0jpHIhBje9Uf78",
    },
    "250710137671516161": {  # madeon
        "forum": 1047182249361145886,
        "sheet": "1-IQNkChiKwopuxCwMZEXIqWMpTieGZiVcxGIj2aC_Ac",
    },
    "186610204023062528": {  # porter
        "forum": 997913478608199890,
        "sheet": "1Mv027gksrVJhriB8fxmio6uW2RK1LSWgi8oJ2Ns8J2U",
    },
}


class ThreadsCog(commands.Cog):
    """Members cog

    Args:
        commands (Cog): base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot

    # if i want to convert to buttons: https://gist.github.com/lykn/bac99b06d45ff8eed34c2220d86b6bf4
    @commands.Cog.listener()
    async def on_reaction_add(reaction, user):
        if (
            reaction.message.channel.parent_id
            == sdict[reaction.message.channel.server.id]["forum"]
            and reaction.message.id == reaction.message.channel.id
            and reaction.emoji == "🎫"
        ):
            user.add_roles(reaction.message.role_mentions)

    @commands.Cog.listener()
    async def on_reaction_remove(reaction, user):
        if (
            reaction.message.channel.parent_id
            == sdict[reaction.message.channel.server.id]["forum"]
            and reaction.message.id == reaction.message.channel.id
            and reaction.emoji == "🎫"
        ):
            user.remove_roles(reaction.message.role_mentions)

    async def sheets_sync(server_id):
        server = discord.Client.get_guild(server_id)
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("google_token.json"):
            creds = Credentials.from_authorized_user_file("google_token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "google_credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("google_token.json", "w") as token:
                token.write(creds.to_json())

        try:
            service = build("sheets", "v4", credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.get(
                spreadsheetId=sdict[server_id]["sheet"],
                includeGridData=True,
                ranges=["shows!A3:Z"],
            ).execute()

            # get and cache cities time zones
            @lru_cache(maxsize=128)
            def citytoloc(input):
                # initialize Nominatim API
                geolocator = Nominatim(user_agent="rinbot")

                # get location from name
                geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
                return geocode(input)

            def loctotz(input):

                # get tz from location
                obj = TimezoneFinder()
                try:
                    return obj.timezone_at(lng=input.longitude, lat=input.latitude)
                except:  # if timezone isnt found
                    return "UTC"

            rows = result["sheets"][0]["data"][0]["rowData"]
            shows = {}
            shows2 = {}

            def clean(input):
                return " ".join(input.split())

            def setrow(v, column, content):
                if column < len(v):
                    if content in v[column]:
                        return clean(v[column][content])
                else:
                    return ""

            for row in rows:
                show = {}
                v = row["values"]

                show["type"] = setrow(v, 0, "formattedValue")
                show["date"] = setrow(v, 1, "formattedValue")
                show["venue"] = setrow(v, 2, "formattedValue")
                show["city"] = setrow(v, 3, "formattedValue")
                show["country"] = setrow(v, 4, "formattedValue")

                if "formattedValue" in v[5]:
                    if "note" in v[5]:
                        if clean(v[5]["formattedValue"]) == (
                            "Check lineup in attached note"
                        ):
                            show["support"] = clean(v[5]["note"])
                        else:
                            show["support"] = (
                                f'{clean(v[5]["formattedValue"])}({clean(v[5]["note"])})'
                            )
                    else:
                        show["support"] = clean(v[5]["formattedValue"])
                else:
                    show["support"] = ""

                show["version"] = setrow(v, 6, "formattedValue")
                show["age"] = setrow(v, 7, "formattedValue")
                show["notes"] = setrow(v, 8, "formattedValue")
                show["status"] = setrow(v, 9, "formattedValue")
                show["tickets"] = setrow(v, 10, "hyperlink")
                show["thread"] = setrow(v, 11, "hyperlink")
                show["time"] = setrow(v, 12, "formattedValue")
                show["role"] = setrow(v, 13, "formattedValue")

                # the role is also the key
                if show["role"]:
                    shows[show["role"]] = show
                # if no role, make the id of the role be now
                else:
                    shows[str(datetime.now())] = show

                # load and diff the pickle for the server

            for show in shows:
                # split date ranges into two days
                datesplit = show["date"].split("-")
                if len(datesplit) == 2:  # if there are two days
                    datesplit[1] = datesplit[1].replace(",", "")
                    d1 = datesplit[0].split()
                    d2 = datesplit[1].split()
                    month1 = d1[0]
                    day1 = d1[1]
                    year2 = d2[-1]

                    if len(d2) == 3:  # if the 2nd day has the month
                        month2 = d2[0]
                        day2 = d2[1]
                        if (
                            len(d1) == 3
                        ):  # if the first day has the year (new years week shows)
                            year1 = d1[2]
                        else:
                            year1 = year2
                    else:
                        month2 = month1
                        day2 = d2[0]
                        year1 = year2

                        dates = [
                            f"{month1} {day1}, {year1}",
                            f"{month2} {day2}, {year2}",
                        ]
                else:
                    dates = [show["date"]]
                # convert to datetime in local time zone
                dates_datetimes = []
                for i, j in enumerate(dates):
                    tz = loctotz(citytoloc(f"{show['city']}, {show['country']}"))
                    t = datetime.strptime(j, "%A %-d, %Y")
                    dt = t.replace(tzinfo=tz)
                    dates_datetimes[i] = dt

                # if date is more than 2 weeks old
                if dates_datetimes[-1] < datetime.now + timedelta(weeks=2):
                    # delete role and lock thread
                    server.get_role(show["role"]).delete()
                    server.get_channel_or_thread(show["thread"]).edit(locked=True)

                try:
                    start = datetime.strptime(show["time"], "%-I:%m %p")
                except:
                    start = timedelta(
                        hours=20
                    )  # asumes the show starts at 8pm for sake of countdown

                # convert dates to datetimes
                countdown = dates_datetimes[0] + start

                role_name = f"{show['city']}|{show['date']}"
                # creates role
                if not show["role"]:
                    role = await discord.create_role(name=role_name, mentionable=True)
                    show["role"] = role.id
                else:
                    server.get_role(show["role"]).edit(name=role_name)

                # convert datetime keys to role keys once role is created
                for key, show in shows.items():
                    if key != show["role"] and show["role"] != None:
                        shows2[show["role"]] = shows[key]
                    else:
                        shows2[key] = shows[key]
                shows = shows2

                if show["status"]:
                    status = "[SOLD OUT]"
                elif show["status"].contains("cancel"):
                    status = "[CANCELED]"
                else:
                    status = ""
                title = f'{status}|{show["date"]}|{show["city"]}|{show["country"]}|{show["venue"]}'

                body = f"Countdown: <t:{round(countdown.timestamp())}:R>\n"
                body += f"Location: {show['venue']}\n"
                body += f"Type: {show['type']}\n"
                if show["time"]:
                    body += f"Start time: {show['time']} (doors may be earlier)\n"
                if show["age"]:
                    body += f"Ages: {show['age']}\n"
                if show["tickets"]:
                    body += f"[Tickets](<{show['tickets']}>)\n"
                if show["notes"]:
                    body += f"Notes: {show['notes']}\n"
                body += f"if you would like a message pinned please ask a mod\n"
                body += f"react with 🎫 to add or remove the <@{show['role']}> role (use /threadping to mention this role in this channel)"

                # creates/edits thread and message
                if not show["thread"]:
                    thread = await server.get_channel(
                        sdict[server_id]["forum"]
                    ).create_thread(name=role_name, content=body)
                else:
                    server.get_channel_or_thread(show["thread"]).edit(name=title)
                    server.get_channel_or_thread(show["thread"]).get_partial_message(
                        show["thread"]
                    ).edit(content=body)

            # load and diff the pickle for the server
            if os.path.exists(f"{server_id}.pickle"):
                with open(f"{server_id}.pickle", "rb") as handle:
                    old = pickle.load(handle)
                    changedict = {}
                    result = list(dictdiffer.diff(old, shows))
                    for i in result:
                        if i[0] == "change":
                            id, key = i[1].split(".")
                            print(id, key)
                            if i[2][0] == None:
                                change = f"{i[2][1]} added\n"
                            elif i[2][1] == None:
                                change = f"{i[2][1]} removed\n"
                            else:
                                change = f"{i[2][0]} changed to {i[2][1]}\n"
                            if id in changedict:
                                changedict[id] += change
                            else:
                                changedict[id] = change
                    for key, change in changedict.items():
                        server.get_channel_or_thread(show["thread"]).send(
                            content=f"<@{key}> {change}"
                        )

            with open(f"{server_id}.pickle", "wb") as handle:
                pickle.dump(shows, handle, protocol=pickle.HIGHEST_PROTOCOL)

        except Exception as err:
            raise(err)

    @app_commands.command(name="pingthread")
    async def pingthread(self, interaction: discord.Interaction, message: str):
        await interaction.followup.send(
            content=f"<@{interaction.channel.get_partial_message(interaction.channel_id).rolementions[0]}> interaction.user.mention says: \n>>>{message}"
        )

    @app_commands.command(name="threadsync")
    async def threadsync(self, interaction: discord.Interaction):
        await self.sheet_sync(interaction.guild.id)
        await interaction.followup.send(content=f"Sheet synced")

    looptime = time(hour=3, tzinfo=ZoneInfo("America/Los_Angeles"))

    @tasks.loop(time=looptime)
    async def refresh_task(self):
        for key in sdict.keys():
            await self.sheet_sync(key)

    # TODO:
    # add/remove role buttons
    # tags - need to figure out how to get continents from loc
    # actually format the class


async def setup(bot: commands.Bot):
    """initializes the Member cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(ThreadsCog(bot))
