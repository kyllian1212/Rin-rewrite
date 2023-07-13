import zoneinfo
from datetime import datetime
import typing
import discord
from discord import app_commands
from discord.ext import commands

#gets timezones from device (might not work on windows, see docs) https://docs.python.org/3/library/zoneinfo.html#zoneinfo.available_timezones 
timezoneslist = list(zoneinfo.available_timezones())
#print("timezones:", timezoneslist)
#print(type(timezoneslist))
#print(type([]))
now = datetime.now()

    
    

#TZ needs to be type "choise" not sure how to do that 

class timeCog(commands.Cog):
    global timezoneslist
    def __init__(self, bot):
        self.bot = bot
        #self.timezoneslist = timezoneslist
    async def daycheck(day, len):
        if day > len:
            return day - len , True
        else:
            return day, False
        
    async def timefunc(self, timezone: str, year: typing.Optional[int], month: typing.Optional[int], day: typing.Optional[int], hour: typing.Optional[int], minute: typing.Optional[int], second: typing.Optional[int], ampm: typing.Optional[str]):
        if year:
            if not month:
                print("year requires month")
        if month:
            if not day:
                print ("month requires day")
        addmonth = False
        addyear = False
        if ampm == "pm":
            hour = hour + 12

        if not second:
            second = 0
        if not minute: 
            minute=0
        if not hour:
            hour = 0
        
        if not day:
            if hour < now.hour:
                day = now.day + 1
            else:
                day = now.day
            
            if day > 28:
                # if the month has 31 days
                if now.month in [1,3,5,7,8,10,12]:
                    #check if day is greater than 31
                    day, addmonth = self.daycheck(day, 31)
                # if month has 30 days
                elif now.month in [4,6,9,11]:
                    # check if day is greater than 30
                    day, addmonth = self.daycheck(day, 30)
                # if feb
                elif now.month == 2:
                    #check if leap year
                    if now.year % 4 == 0:
                        # check if day is greater than 29
                        day, addmonth = self.daycheck(day, 29)
                
                    else:
                        day, addmonth = self.daycheck(day, 28)
                    
            
        if not month:
            
            if addmonth:
                vmonth = now.month + 1
            else:
                vmonth = now.month
            
            if day < now.day:
                vmonth += 1
            else: 
                month = vmonth
                
            if month > 12:
                month -= 12
                addyear = True
        
        if not year:
            
            if month < now.month:
            
                year = now.year + 1
            else:
                year = now.year
            
            if addyear:
                year += 1    
            



        
              
            
        isotime = datetime(year=year, month=month, day=day, hour=hour, minute=minute,second=second, tzinfo=zoneinfo.ZoneInfo(timezone))
        holdtime = isotime.timestamp()
        timestamp = round(holdtime)
        return timestamp
        
        
    
    @app_commands.command(name="time",description="converts timezone to timestamp")
    async def time(self, interaction: discord.Interaction, timezone: str, year: typing.Optional[int], month: typing.Optional[int], day: typing.Optional[int], hour: typing.Optional[int], minute: typing.Optional[int], second: typing.Optional[int], ampm: typing.Optional[str]):
        await interaction.response.defer()
        timestamp = self.timefunc(timezone, year, month, day, hour, minute, second, ampm)
        await interaction.followup.send(embed=discord.Embed(description=f"<t:{timestamp}:d> `<t:{timestamp}:d>` \n<t:{timestamp}:D> `<t:{timestamp}:D>` \n<t:{timestamp}:t> `<t:{timestamp}:t>` \n<t:{timestamp}:T> `<t:{timestamp}:T>` \n<t:{timestamp}:f> `<t:{timestamp}:f>` \n<t:{timestamp}:F> `<t:{timestamp}:F>` \n<t:{timestamp}:R> `<t:{timestamp}:R>`"))
        
   #timezone autocomplete 
    @time.autocomplete('timezone')
    async def time_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        print("hi", interaction, current)
        return [
            app_commands.Choice(name=timezone, value=timezone)
            for timezone in timezoneslist if current.lower() in timezone.lower()
        ]
    
    
    #event command, not in use bc users cant put newlines in slash commands
    
    # @app_commands.command(name="event")    
    # async def event(self, name: str, image: typing.Optional[discord.Attachment], interaction: discord.Interaction, timezone: str, year: typing.Optional[int], month: typing.Optional[int], day: typing.Optional[int], hour: typing.Optional[int], minute: typing.Optional[int], second: typing.Optional[int], ampm: typing.Optional[str], durration: int, desc: typing.Optional[str]):
    #     timestamp = self.timefunc(timezone, year, month, day, hour, minute, second, ampm)
    #     end = (durration * 60) + timestamp
        
    #     discord.Guild.create_scheduled_event(name=name, image=image, start_time=timestamp, end_time=end, description= desc)









async def setup(bot: commands.Bot):
    """initializes the voice channel cog

    Args:
        bot (commands.Bot): the discord bot
    """
    await bot.add_cog(timeCog(bot))