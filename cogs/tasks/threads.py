"""
Threads Module
"""
__version__ = "beta-2"
__author__ = "Toxin_X"


# TODO:
# add/remove role buttons
# tags - need to figure out how to get continents from loc
# detect and deal with merged cells
# dont create sets added after they happened

# location and time stuff
from functools import lru_cache
from datetime import datetime, timedelta, time, date
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
from dotenv import load_dotenv


# https://developers.google.com/sheets/api/quickstart/python
# https://googleapis.github.io/google-api-python-client/docs/dyn/sheets_v4.spreadsheets.html#get
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

# If modifying these scopes, delete the file google_auth_tokens.json
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
sheet_name = "shows!"
sheet_range = sheet_name + "A3:Z"

# dict of server ids and their forum/sheets
sdict = {
    "1280169949767405651": {  # testing server
        "forum": 1281341776057339914,
        "sheet": "1jXR207pgnwobPjave6fM78gg8z-TGkkxzgO66GhFoYM",
    },
    "1059727841937334313": {  # hmm
        "forum": 1276933222604996650,
        "sheet": "10M3FRfDYWAj95O6eGvQ1y6kRRRfES0jpHIhBje9Uf78",
    },
    "250710137671516161": {  # madeon
        "forum": 1047182249361145886,
        "sheet": "1-IQNkChiKwopuxCwMZEXIqWMpTieGZiVcxGIj2aC_Ac",
    },  # ,
    # "186610204023062528": {  # porter
    #     "forum": 997913478608199890,
    #     "sheet": "1Mv027gksrVJhriB8fxmio6uW2RK1LSWgi8oJ2Ns8J2U",
    # },
}

#when to autosync, its stupid to put this here but decorators cant access self sooooooo
looptime = time(hour=3, tzinfo=ZoneInfo("America/Los_Angeles")) 


class ThreadsCog(commands.Cog):
    """Members cog

    Args:
        commands (Cog): base class for all cogs
    """

    def __init__(self, bot):
        self.bot = bot
        self.emote = "🎫"
        self.autosync = True
    # if i want to convert to buttons: https://gist.github.com/lykn/bac99b06d45ff8eed34c2220d86b6bf4

    # react add/remove

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if (
            reaction.message_id == reaction.channel_id
            and reaction.emoji.name == self.emote
        ):
            try:
                channel = await self.bot.fetch_channel(reaction.channel_id)
                reacted_message: discord.Message = await channel.fetch_message(
                    reaction.message_id
                )

                role = reacted_message.role_mentions[0]
                if not role.permissions.manage_messages:
                    await reaction.member.add_roles(reacted_message.role_mentions[0])
            except Exception:
                with open(f"{datetime.now()}.debug", "w") as file:
                    file.write(Exception)
                    file.write("\n")
                    file.write(reaction)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        if (
            reaction.message_id == reaction.channel_id
            and reaction.emoji.name == self.emote
        ):
            channel = await self.bot.fetch_channel(reaction.channel_id)
            reacted_message: discord.Message = await channel.fetch_message(
                reaction.message_id
            )
            j = await reacted_message.guild.fetch_member(reaction.user_id)
            await j.remove_roles(reacted_message.role_mentions[0])

    # import google sheet

    async def getsheet(self, server_id):
        

        creds = None
        # The file google_auth_tokens.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("google_auth_tokens.json"):
            creds = Credentials.from_authorized_user_file(
                "google_auth_tokens.json", SCOPES
            )
            print(creds.valid, creds.expiry)
        # If there are no (valid) credentials available, let the user log in.
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("refreshed token")
                except Exception:
                    print("Refresh Request failed")
                    print(repr(Exception))
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "google_client_secret.json", SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
                # creds = flow.run_local_server(port=4041)

                # Tell the user to go to the authorization URL.
                auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')

                print('Generating new token, please go to this URL: {}'.format(auth_url))

                # The user will get an authorization code. This code is used to get the
                # access token.
                code = input('Enter the authorization code: ')
                flow.fetch_token(code=code)

                # You can use flow.credentials, or you can just get a requests session
                # using flow.authorized_session.
                creds = flow.credentials

            # Save the credentials for the next run
        with open("google_auth_tokens.json", "w") as token:
            token.write(creds.to_json())
        try:
            service = build("sheets", "v4", credentials=creds)
        
            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.get(
                spreadsheetId=sdict[str(server_id)]["sheet"],
                includeGridData=True,
                ranges=[sheet_range],
            ).execute()
            print("creds valid")
            return sheet, result
        except HttpError as err:
            raise (err)

    # warning: lowercase format is a function
    async def updatesheet(self, server_id, sheet, updates, Format):
        body = {"valueInputOption": Format, "data": updates}
        result = (
            sheet.values()
            .batchUpdate(spreadsheetId=sdict[str(server_id)]["sheet"], body=body)
            .execute()
        )
        print(f'{(result.get("totalUpdatedCells"))} cells updated.')
        return result

    # update the shows

    async def update(self, show, server_id, server, sheet, updates, count, msg):
        
        # if there is a start time convert it to a unix time, otherwise assume the start time is 20:00 (8pm)
        try:
            start = datetime.strptime(show["time"], "%-I:%m %p")
        except:
            start = timedelta(hours=20)

        # set the countdown to be the first day listed plus the start time
        countdown = show["datetimes"][0] + start

        # update role name
        role_name = f'{show["city"]} | {show["date"]}'
        await server.get_role(show["role"]).edit(name=role_name)

        # set the title
        if "sold" in show["status"].lower():
            status = "[SOLD OUT] |"
        elif "cancel" in show["status"].lower():
            status = "[CANCELED] |"
        else:
            status = ""
        title = f'{status} {show["date"]} | {show["city"]} | {show["country"]} | {show["venue"]}'
        if len(title) > 95:
            title = title[0:95] + "[…]"

        # update the body
        body = f"Countdown: <t:{round(countdown.timestamp())}:R>\n"
        if show["support"]:
            body += f'Support: {show["support"]}\n'
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
        body += f"react with {self.emote} to add or remove the <@&{show['role']}> role (can only be pinged in this thread by using `/pingthread`)"

        # creates/edits thread and message
        if show["thread"] == None:
            if not "past" in show["status"].lower():
                thread = await server.get_channel(
                    sdict[str(server_id)]["forum"]
                ).create_thread(name=title, content=body)
                show["thread"] = thread.thread.jump_url

        else:
            await server.get_channel_or_thread(show["thread"]).edit(name=title)
            try:
                await server.get_channel_or_thread(show["thread"]).get_partial_message(
                    show["thread"]
                ).edit(content=body)
            except:
                print(f"couldn't edit body of {show['thread']}")
                thr = server.get_channel_or_thread(show["thread"])
                await thr.send(
                    f"{thr.owner.mention}, if possible please set the starting message to ```\n{body}```"
                )
        # add role and thread id to sheet, delete row id
        # https://developers.google.com/sheets/api/guides/values#write_multiple_ranges
        if not "past" in show["status"].lower():
            try:
                int(show["thread"])
            except:
                cell = sheet_name + "L" + str(show["row"])

                updates.append(
                    {
                        "range": cell,
                        "values": [
                            [
                                f'=HYPERLINK("{show["thread"]}",IMAGE("https://i.postimg.cc/J4GqBT05/discord-long-2.png"))'
                            ]
                        ],
                    }
                )
                show["thread"] = show["thread"].split("/")[-1]

        print(datetime.now(), role_name)
        if count != 0 and count % 10 == 0:
            print("updating and sleeping")

            await self.updatesheet(server_id, sheet, updates, "USER_ENTERED")
            updates = []
            c2 = 1
            while c2 < 11:
                print(c2)
                c2 += 1
                await asyncio.sleep(1)
        count += 1

        return (updates, count)

    # the main function to sync the threads
    async def sheets_sync(self, server_id, msg=None):
        server = discord.Client.get_guild(self.bot, server_id)
        print(server)
        sheet, result = await self.getsheet(server_id)

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
        updates = []
        raw_updates = []

        # function to remove whitespace
        def clean(input):
            return " ".join(input.split())

        def setrow(v, column, content):
            if column < len(v):
                if content == "userEnteredValue":
                    return int(v[column][content]["numberValue"])

                elif content in v[column]:
                    return clean(v[column][content])
            else:
                return None

        # the starting row
        row_num = 3

        for row in rows:
            show = {}
            v = row["values"]

            show["row"] = row_num
            row_num += 1
            show["type"] = setrow(v, 0, "formattedValue")
            show["date"] = setrow(v, 1, "formattedValue")
            show["venue"] = setrow(v, 2, "formattedValue")
            show["city"] = setrow(v, 3, "formattedValue")
            show["country"] = setrow(v, 4, "formattedValue")
            testin = setrow(v, 4, "formattedValue")
            # support
            if "formattedValue" in v[5]:
                if "note" in v[5]:
                    if clean(v[5]["formattedValue"]) == (
                        "Check lineup in attached note"
                    ):
                        show["support"] = clean(v[5]["note"])
                    else:
                        show["support"] = (
                            f'{clean(v[5]["formattedValue"])} \n-# ({clean(v[5]["note"])})'
                        )
                else:
                    show["support"] = clean(v[5]["formattedValue"])
            else:
                show["support"] = ""

            show["version"] = setrow(v, 6, "formattedValue")
            show["status"] = setrow(v, 7, "formattedValue")
            show["age"] = setrow(v, 8, "formattedValue")
            show["time"] = setrow(v, 9, "formattedValue")
            show["tickets"] = setrow(v, 10, "hyperlink")
            try:
                if setrow(v, 11, "hyperlink") != None:
                        show["thread"] = int(setrow(v, 11, "hyperlink").split("/")[-1])
                else:
                    show["thread"] = None
            except:
                show["thread"] = None
            show["notes"] = setrow(v, 12, "formattedValue")
            show["role"] = (
                int(setrow(v, 13, "formattedValue"))
                if setrow(v, 13, "formattedValue") != None
                else None
            )

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
                t = datetime.strptime(j, "%B %d, %Y")
                dt = t.replace(tzinfo=ZoneInfo(tz))
                dates_datetimes.insert(i, dt)

            # if date is more than 2 weeks old delete role and lock thread
            if dates_datetimes[-1] < datetime.now(ZoneInfo("UTC")) - timedelta(weeks=2):
                # delete role and lock thread
                try:
                    await server.get_role(show["role"]).delete()
                except:
                    pass
                try:
                    await server.get_channel_or_thread(show["thread"]).edit(locked=True)
                except:
                    pass
                # change upcoming to past
                show["status"] = show["status"].replace("UPCOMING", "PAST")
                cell = sheet_name + "H" + str(show["row"])
                updates.append({"range": cell, "values": [[str(show["status"])]]})
            # if more than 3 weeks old stop getting shows

            # if this bot hasnt been run in a while shows longer than 3 weeks may not be locked/deleted
            if dates_datetimes[-1] < datetime.now(ZoneInfo("UTC")) - timedelta(weeks=3):
                print(
                    "breaking",
                    show["city"],
                    datetime.now(ZoneInfo("UTC")) - timedelta(weeks=3),
                )
                break

            show["datetimes"] = dates_datetimes

            # creates role
            if not show["role"]:
                role_name = f"{show['city']} | {show['date']}"
                role = await server.create_role(name=role_name, mentionable=False)
                show["role"] = role.id
                cell = sheet_name + "N" + str(show["row"])
                updates.append({"range": cell, "values": [[str(show["role"])]]})
            # the role id is also the key
            shows[show["role"]] = show
            print(show["row"] - 2, show["date"], show["role"])
        if msg:
            await msg.edit("finished importing sheet")

        # after creating all the roles, add them to the sheet
        await self.updatesheet(server_id, sheet, updates, "RAW")
        updates = []

        # compare current sheet to previous update if it exists
        if not os.path.exists(f"{server_id}.pickle"):
            old = {}
            print("pickle does not exist")
        else:
            with open(f"{server_id}.pickle", "rb") as handle:
                old = pickle.load(handle)
        changedict = {}
        count = 0
        diff = list(dictdiffer.diff(old, shows))

        print(diff)
        for i in diff:
            # the added shows
            if i[0] == "add":
                for l in i[2]:
                    updates, count = await self.update(
                        shows[l[0]], server_id, server, sheet, updates, count, msg
                    )
                print("finished with added shows")
            # the changed shows
            if i[0] == "change":
                print(i)
                id, key = i[1][0], i[1][1]
                print(id, key)
                if key != "datetimes" and key != "thread" and key != "row":
                    if i[2][0] == None:
                        change = f"{key}: {i[2][1]} added\n"
                    elif i[2][1] == None:
                        change = f"{key}: {i[2][1]} removed\n"
                    else:
                        change = f"{key}: {i[2][0]} changed to {i[2][1]}\n"
                    # add changes to the channel
                    if id in changedict:
                        changedict[id] += change
                    else:
                        changedict[id] = change
                    print("finished with changed shows")
        for key, change in changedict.items():
            updates, count = await self.update(
                shows[key], server_id, server, sheet, updates, count, msg
            )
            try:
                await server.get_channel_or_thread(shows[key]["thread"]).send(
                    content=f"<@&{key}> {change}"
                )
            except:
                print(f"couldn't notify {shows[key]['date']}")
        if len(updates) > 0:
            await self.updatesheet(server_id, sheet, updates, "USER_ENTERED")
        # save the new db
        with open(f"{server_id}.pickle", "wb") as handle:
            pickle.dump(shows, handle, protocol=pickle.HIGHEST_PROTOCOL)

    @app_commands.command(name="ping_thread")
    @app_commands.checks.cooldown(
        1, 120
    )  # command can only be used once per 2 min per user
    async def pingthread(self, interaction: discord.Interaction, message: str):
        try:
            thread = await interaction.channel.fetch_message(
                interaction.channel_id
            )  # .role_mentions[0]
            threadrole = thread.role_mentions[0]
            if threadrole in interaction.user.roles:
                await interaction.response.send_message(
                    content=f"{threadrole.mention}\n{interaction.user.mention} says: \n>>> {message}"
                )
            else:
                await interaction.response.send_message(
                    content=f"You do not have <@{threadrole.mention}>", ephemeral=True
                )

        except:
            await interaction.response.send_message(
                content="no role found, make sure you are in a thread and the first message mentions a role",
                ephemeral=True,
            )

    @pingthread.error
    async def on_pingthread_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)

    @app_commands.command(name="sync_thread")
    async def threadsync(self, interaction: discord.Interaction):
        msg = await interaction.response.send_message(
            content=f"attempting to sync", ephemeral=True
        )
        await self.sheets_sync(interaction.guild.id, msg=msg)
        await interaction.followup.send(content="ended sync", ephemeral=True)
    


    @app_commands.command(name="toggle_auto_sync")
    async def togglethreadsync(self, interaction: discord.Interaction, toggle: bool):
        self.autosync = toggle
        msg = await interaction.response.send_message(
        content=f"autosync is now {self.autosync}\nsyncs at <t:{round(looptime.timestamp())}:t>", ephemeral=True
    )
    @app_commands.command(name="auto_sync_status")
    async def threadsync(self, interaction: discord.Interaction):
        msg = await interaction.response.send_message(
            content=f"autosync is {self.autosync}\nsyncs at <t:{round(looptime.timestamp())}:t>", ephemeral=True
        )


    @tasks.loop(time=looptime)
    async def refresh_task(self):
        if self.autosync == True:
            for key in sdict.keys():
                await self.sheets_sync(key)
        else:
            print("auto sync is off")


async def setup(bot: commands.Bot):
    """initializes the Thread cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(ThreadsCog(bot))
