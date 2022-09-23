# previous versions
the changelog for previous versions of the bot is available here: https://github.com/kyllian1212/Rin/blob/master/changelog.md

------------------------------------------------------------------------
# v1.0.0 - 26/09/2022

## **huge bot changes**
* the entire bot has been rewritten from the ground up! with discord.py being updated to 2.0.0, it means the bot finally supports slash commands and other cool new things.
* the bot now has a sqlite database, which should help a lot in writing new features and having more flexibility/readability in the code. it will also allow the bot to finally support multiple servers instead of just the porter robinson discord
* the bot has been split into multiple files for easier code readability.

## **slash commands!!**
* the following commands are now slash commands:
  * !!info > /info
  * !!fiftyfifty > /fiftyfifty
  * !!roll > /roll
  * !!october_18 > /october_18
* !!say and !!saytts are still normal commands however and wont be slash commands

## **new features**
* **adding songs to presence queue for Rin to listen**: 
  * you can now add songs to the "presence queue" via the command **/add_song_to_presence_queue**! its the song that will be displayed as Rin's presence (Listening to `song`). she will have a default list of songs from now on that she'll go through randomly, and whenever someone adds songs to the queue she'll switch to those after the previous one is finished until there are no more songs in the queue. 
  * this is currently only possible with spotify links but i'll look into having other streaming platforms be supported. 
  * you can only put a maximum of 3 songs in the queue at once.
  * admins can check the presence queue with **/check_presence_queue** and if anyone put any rule-breaking songs, they can delete them with **/delete_song_from_presence_queue** (this means do not add songs with offensive words in the title/artist name because we'll know and we'll know who added them). they can also interrupt the current song playing with **/interrupt_current_song**
* **/set_archive_channel, /archive and /unarchive**: allows the bot to archive channels automatically! including moving it to the category of your choice and setting the appropriate role permissions.
* **/rin_timeout, /rin_kick and /rin_ban**: allows the bot to timeout, kick, ban someone and dm them (or not) the reason. 
* **/rebuild_database**: this one is less important but if there's any issue with the bot's database or an update, this will destroy the entire database and rebuild it from scratch (which means all data in the database will be erased)

## **some cool changes**
* **/roll**: you are now able to roll any number and any dice you want instead of just a 1d6 dice (min 1d1, max 100d100)
* **!!say and !!saytts**: both are now dependant on having the "Administrator" permission instead of depending on a specific role
* deleted **!!changelog** because tbh this was a kinda useless commands
* added a temporary countdown for second sky 2022 (this is specifically for PRD)

## **reporting messages**
* **/set_log_channel**: will set which channel the reported messages will go to in the server you're in.
* the report function deleting messages will now depend on if you have the "Administrator" or "Manage Messages" permissions instead of depending on a specific role.
* changed the reaction listener from `on_reaction_add` to `on_raw_reaction_add`, which means every message, no matter when it has been sent, is now able to be reported.
* displayed user roles in a reported message are now mentions (which means it should adapt in the report if a role that person has is renamed or color changed in the future)
* added message creation date/time to the report (its unix timestamped so it should display correctly depending on which timezone you're in)
* the reported date/time cannot be timestamped so i added the timezone in

## **default song library**
* added 4 songs in the default song library:
  * The Prince by Madeon
  * Love You Back by Madeon
  * Gonna Be Good by Madeon (length not exact because it's not out yet)
  * Everything Goes On by Porter Robinson

## **features planned for future versions (v1.1.0 etc.)**
those are features that were low in priority to get them out this month, or that i wasn't able to figure out how to do yet:
* support for more music platforms (apple music, soundcloud...) for **/add_song_to_presence_queue**, and members being able to delete songs they added in the queue (eg. if they added some by accident)
* song progress indicated in rin's presence
* more songs in the default song library if any super cool porter & madeon songs release by then
* **/get_pronouns_role**: allows members to set their own pronouns, creating a new role if it hasn't been added to anyone before (was planned for this version but still need to think on how to make it work in multiple servers)
* streaming music in voice chat
* word blacklisting (reporting automatically a message if it contains a blacklisted word)
* maybe some fun games stuff if i can figure it out!
* a web dashboard would be cool af too but i need to figure it out and that would probably be a v2.0.0 kinda thing so itll be in a long time
* i probably can't have the bot open for every server because of the presence stuff but i'll figure something out eventually!
* optimizing/refactoring the code even more because i've done all this in a kinda rush LMAO