import os
import os.path
import json
import pickle
import random
import sqlite3

import aiohttp
import discord
import asyncio
import requests
import randfacts
from io import BytesIO
from discord import Intents
from discord import Streaming
from twitchAPI.twitch import Twitch
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from discord.ext.commands import has_permissions, MissingPermissions
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands, tasks
from discord.utils import get

# TESTINGBOT_DISCORD_TOKEN
TOKEN = os.getenv('METABOT_DISCORD_TOKEN')
SPREADSHEET_ID = '1S-AIIx2EQrLX8RHJr_AVIGPsQjehEdfUmbwKyinOs_I'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

intents = Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

# Authentication with Twitch API.
client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
body = {
    'client_id': client_id,
    'client_secret': client_secret,
    "grant_type": 'client_credentials'
}
r = requests.post('https://id.twitch.tv/oauth2/token', body)
keys = r.json()
headers = {
    'Client-ID': client_id,
    'Authorization': 'Bearer ' + keys['access_token']
}

conn = sqlite3.connect('GuildSettings.db')
c = conn.cursor()


def get_all_guild_settings(guild_id):
    with conn:
        c.execute(f"SELECT * FROM Guilds WHERE GuildID={guild_id}")
        return c.fetchone()


def get_fact_send_time(guild_id):
    with conn:
        c.execute(f"SELECT Hour, Minute FROM RandomFactSendTime WHERE GuildID={guild_id}")
        return c.fetchone()


def get_saved_reaction_roles(guild_id):
    with conn:
        c.execute(f"SELECT RoleID, RoleEmoji FROM GuildRoles WHERE GuildID={guild_id}")
        return c.fetchall()


def get_reaction_role_by_role_id(guild_id, role_id):
    with conn:
        c.execute(f"SELECT RoleID, RoleEmoji FROM GuildRoles WHERE GuildID={guild_id} AND RoleID={role_id}")
        return c.fetchone()


def get_reaction_role_by_emoji(guild_id, emoji):
    with conn:
        c.execute(f"SELECT RoleID, RoleEmoji FROM GuildRoles WHERE GuildID={guild_id} AND RoleEmoji={emoji}")
        return c.fetchone()


def update_fact_send_time(guild_id, hour, minute):
    with conn:
        c.execute(f"""UPDATE RandomFactSendTime SET Hour = {hour}, Minute = {minute} WHERE GuildID = {guild_id}""")


def update_guild_role_reaction_settings(guild_id, role_reaction_channel_id, role_reaction_message_id):
    with conn:
        c.execute(
            f"""UPDATE Guilds SET RoleReactionChannelID = {role_reaction_channel_id}, ReactMessageID = {role_reaction_message_id}
                      WHERE GuildID = {guild_id}""")


def update_guild_member_count_settings(guild_id, member_count_channel_id, member_count_message_id):
    with conn:
        c.execute(
            f"""UPDATE Guilds SET MemberCountChannelID = {member_count_channel_id}, MemberCountMessageID = {member_count_message_id}
                      WHERE GuildID = {guild_id}""")


def update_guild_leave_message_channel(guild_id, leave_message_channel_id):
    with conn:
        c.execute(
            f"""UPDATE Guilds SET LeaveMessageChannelID = {leave_message_channel_id} WHERE GuildID = {guild_id}""")


def update_guild_leave_message(guild_id, leave_message):
    with conn:
        c.execute(f"""UPDATE Guilds SET LeaveMessage = {leave_message} WHERE GuildID = {guild_id}""")


def update_guild_random_facts_channel(guild_id, random_facts_channel_id):
    with conn:
        c.execute(f"""UPDATE Guilds SET RandomFactsChannelID = {random_facts_channel_id} WHERE GuildID = {guild_id}""")


def insert_guild(guild_id, role_reaction_channel_id, react_message_id, member_count_channel_id, member_count_message_id,
                 leave_message_channel_id, leave_message, random_facts_channel_id):
    with conn:
        c.execute(f"INSERT INTO Guilds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (int(guild_id), None, role_reaction_channel_id, react_message_id, member_count_channel_id,
                   member_count_message_id, leave_message_channel_id, leave_message, random_facts_channel_id))


def insert_rand_fact_send_time(guild_id, hour, minute):
    with conn:
        c.execute(f"INSERT INTO RandomFactSendTime VALUES (?, ?, ?)",
                  (int(guild_id), hour, minute))


def insert_guild_role(guild_id, role_id, role_emoji):
    with conn:
        c.execute("INSERT INTO GuildRoles VALUES (?, ?, ?)", (guild_id, role_id, role_emoji))


def remove_guild_reaction_role(guild_id, role: discord.Role):
    with conn:
        c.execute("DELETE from GuildRoles WHERE GuildID = :guild_id AND RoleID = :role_id",
                  {'guild_id': guild_id, 'role_id': role.id})


# Authentication with the Google Sheets API.
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


def log_and_print_exception(e):
    logging_file = open("log.txt", "a")
    logging_file.write(f"{datetime.now()}\n{str(e)}\n\n")
    logging_file.close()
    print(f"Exception logged. Error:\n{e}")


# Returns true if online, false if not.
def check_user(streamer_name):
    try:
        if streamer_name is not None:
            stream = requests.get('https://api.twitch.tv/helix/streams?user_login=' + streamer_name,
                                  headers=headers)
            if str(stream) == '<Response [200]>':
                stream_data = stream.json()

                if len(stream_data['data']) == 1:
                    return True, stream_data
                else:
                    return False, stream_data
        else:
            stream_data = None
            return False, stream_data
    except Exception as e:
        log_and_print_exception(e)
        stream_data = None
        return False, stream_data


async def has_notif_already_sent(channel, user):
    async for message in channel.history(limit=200):
        if user is not None:
            if f"{user.mention} is now playing" in message.content:
                return message
            else:
                return False
        else:
            return False


def update_react_message(guild_id, roles_info):
    role_display = ""
    for role in roles_info:
        role_id = role[0]
        role_emoji = role[1]
        guild = bot.get_guild(guild_id)
        role = get(guild.roles, id=role_id)
        if role is not None:
            role_display += f"{role_emoji} - {role.name}\n"
    if not role_display:
        role_display = "No Roles Have Been Added Yet"

    role_reaction_message = discord.Embed(title="React to this message to get your roles!",
                                          description="Click the corresponding emoji to receive your "
                                                      "role.\n" + role_display,
                                          color=0x00ff00)
    return role_reaction_message


def embed_maker(thing_list):
    list_number = 1
    embed = ""
    for thing in thing_list:
        item = f"{list_number} = {thing}\n"
        embed += item
        list_number += 1
    return embed


def string_to_embed(description, title=discord.Embed.Empty, color=0x00ff00):
    return discord.Embed(title=title, description=description, color=color)


def convert_normal_time(hour, minute):
    # Converting 24h time to normal time.
    try:
        if minute < 10:
            minute = f"0{minute}"
        if hour < 12:
            morning_or_night = "am"
        elif hour >= 12:
            morning_or_night = "pm"
        if hour > 12:
            hour = hour - 12
        if hour == 0:
            hour = 12
        normal_time = f"{hour}:{minute}{morning_or_night}"
        return normal_time
    except:
        return datetime.now()


async def schedule_random_facts():
    # Initializing scheduler
    scheduler = AsyncIOScheduler()
    if os.path.isfile('GuildSettings.db'):
        for guild in bot.guilds:
            send_time = get_fact_send_time(guild.id)
            if send_time is not None and len(send_time) > 0:
                hour = send_time[0]
                minute = send_time[1]

                async def func():
                    random_facts_channel = get_all_guild_settings(guild.id)[8]
                    await random_facts_channel.send(string_to_embed(f"{randfacts.get_fact()}."))

                scheduler.add_job(func, CronTrigger(hour=hour, minute=minute, second=0))
    else:
        print("Database file does not exist.")
        exit()

    scheduler.start()


class MetaBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @bot.command(name='addtwitch', help='Adds your Twitch to the live notifs.', pass_context=True)
    async def add_twitch(self, ctx, twitch_name):
        if ctx.guild.id == 762921541204705321:
            await ctx.send("If you're here to just plug your Twitch and leave, sincerely fuck off. Otherwise, "
                           "feel free to stick around or ask for help :P.")
            return
        with open('streamers.json', 'r') as file:
            streamers = json.loads(file.read())

        user_id = ctx.author.id
        streamers[user_id] = twitch_name

        with open('streamers.json', 'w') as file:
            file.write(json.dumps(streamers))
        await ctx.send(f"Added {twitch_name} for {ctx.author} to the Twitch notifications list.")

    @bot.command(name='fact send time', help='Set a time for a random fact to send. Hours is in 24 hour format.',
                 pass_context=True)
    @has_permissions(kick_members=True)
    async def fact_send_time(self, ctx, new_hour, new_minute):
        await ctx.interaction.response.defer()

        if isinstance(new_hour, int) is False or isinstance(new_minute, int) is False:
            await ctx.interaction.followup.send(
                embed=string_to_embed(f"Please use integers for both the hour and minute."))
            return

        guild_id = str(ctx.guild.id)
        send_time = get_fact_send_time(int(guild_id))
        if len(send_time) > 0:
            db_hour = send_time[0]
            db_minute = send_time[1]
            change_send_time_confirmation_components = discord.ui.MessageComponents(
                discord.ui.ActionRow(
                    discord.ui.Button(label="Yes", custom_id="YES"),
                    discord.ui.Button(label="No", custom_id="NO"),
                ),
            )
            await ctx.interaction.followup.send(embed=string_to_embed(
                f"The time {convert_normal_time(db_hour, db_minute)} is currently set. Would you like to change this?"),
                components=change_send_time_confirmation_components)

            def check(interaction_: discord.Interaction):
                if interaction_.user != ctx.author:
                    return False
                if interaction_.message.id != change_send_time_confirmation_components.id:
                    return False
                return True

            change_send_time_confirmation_message_interaction = await bot.wait_for("component_interaction", check=check)

            change_send_time_confirmation_components.disable_components()
            await change_send_time_confirmation_message_interaction.response.edit_message(
                components=change_send_time_confirmation_components)

            if change_send_time_confirmation_message_interaction.component.custom_id == "NO":
                return
            else:
                update_fact_send_time(guild_id, new_hour, new_minute)
                await ctx.interaction.followup.send(
                    embed=string_to_embed(f"Changed fact send time to {convert_normal_time(new_hour, new_minute)}."))

    @fact_send_time.error
    async def add_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.interaction.followup.send(
                embed=string_to_embed(f"You don't have the permissions to change the fact send time."))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.guild.id == 593941391110045697 or after.guild.id == 762921541204705321:
            with open('streamers.json', 'r') as file:
                streamers = json.loads(file.read())
            if before.activity == after.activity:
                return

            if isinstance(after.activity, Streaming) is False:
                return
            if isinstance(after.activity, Streaming):
                twitch_name = after.activity.twitch_name
                user_id = after.id
                does_twitch_name_exist = False
                for user_id_, twitch_name_ in streamers.items():
                    if twitch_name == twitch_name_:
                        does_twitch_name_exist = True
                if user_id not in streamers and does_twitch_name_exist is False:
                    streamers[user_id] = twitch_name
                    print(f"Added streamer {twitch_name} to streamers.json")

            with open('streamers.json', 'w') as file:
                file.write(json.dumps(streamers))

    # Defines a loop that will run every 10 seconds (checks for live users every 10 seconds).
    @tasks.loop(seconds=10)
    async def live_notifs_loop(self):
        with open('streamers.json', 'r') as file:
            streamers = json.loads(file.read())
        try:
            if streamers is not None:
                guild = bot.get_guild(593941391110045697)
                channel = bot.get_channel(740369106880036965)
                role = get(guild.roles, id=800971369441394698)
                for user_id, twitch_name in streamers.items():
                    selected_member = ""
                    async for member in guild.fetch_members(limit=None):
                        if member.id == int(user_id):
                            selected_member = member
                    status, stream_data = check_user(twitch_name)
                    user = bot.get_user(int(user_id))
                    if status is True:
                        thumbnail_url_first_part = stream_data['data'][0]['thumbnail_url'].split('{')
                        full_thumbnail_url = f"{thumbnail_url_first_part[0]}1920x1080.jpg"
                        message = await has_notif_already_sent(channel, user)
                        if message is not False:
                            continue
                        if selected_member != "":
                            await selected_member.add_roles(role)
                        async with aiohttp.ClientSession() as session:
                            async with session.get(full_thumbnail_url) as resp:
                                buffer = BytesIO(await resp.read())
                        await channel.send(
                            f":red_circle: **LIVE**"
                            f"\n{user.mention} is now playing {stream_data['data'][0]['game_name']} on Twitch!"
                            f"\n{stream_data['data'][0]['title']}"
                            f"\n<https://www.twitch.tv/{twitch_name}>",
                            file=discord.File(fp=buffer, filename="thumbnail.jpg"))
                        print(f"{user} started streaming. Sending a notification.")
                        continue
                    elif stream_data is not None:
                        if selected_member != "":
                            await selected_member.remove_roles(role)
                        message = await has_notif_already_sent(channel, user)
                        if message is not False:
                            print(f"{user} stopped streaming. Removing the notification.")
                            await message.delete()
        except TypeError as e:
            log_and_print_exception(e)

    @commands.Cog.listener()
    async def on_ready(self):
        await bot.change_presence(activity=discord.Game("$help WALL-E"))
        await schedule_random_facts()
        self.live_notifs_loop.start()

        print("Bot is ready.")
        print(f"Total servers: {len(bot.guilds)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if "happy birthday" in message.content:
            await message.channel.send("Happy birthday!! :cake: :birthday: :tada:")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        guild_settings = get_all_guild_settings(guild.id)
        if len(guild_settings) == 0:
            insert_guild(guild.id, None, None, None, None, None, "quit on the 1 yard line (left the server)", None)
            insert_rand_fact_send_time(guild.id, 12, 0)

    # Assign the role when the role is added as a reaction to the message.
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = bot.get_guild(payload.guild_id)
        guild_id = str(payload.guild_id)
        member = get(guild.members, id=payload.user_id)

        role_reaction_channel_id = get_all_guild_settings(guild_id)[2]
        role_reaction_message_id = get_all_guild_settings(guild_id)[3]

        saved_roles = get_saved_reaction_roles(guild_id)
        saved_emojis = []
        for role in saved_roles:
            saved_emojis.append(role[1])

        if payload.channel_id == role_reaction_channel_id and payload.message_id == role_reaction_message_id and member.bot is False:
            if str(payload.emoji) in saved_emojis:
                role_id = get_reaction_role_by_emoji(guild_id, str(payload.emoji))
                role = get(payload.member.guild.roles, id=role_id)
                if role is not None:
                    await payload.member.add_roles(role)
                    print(f"Assigned {member} to {role}.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = bot.get_guild(payload.guild_id)
        guild_id = str(payload.guild_id)
        member = get(guild.members, id=payload.user_id)

        role_reaction_channel_id = get_all_guild_settings(guild_id)[2]
        role_reaction_message_id = get_all_guild_settings(guild_id)[3]

        saved_roles = get_saved_reaction_roles(guild_id)
        saved_emojis = []
        for role in saved_roles:
            saved_emojis.append(role[1])

        if payload.channel_id == role_reaction_channel_id and payload.message_id == role_reaction_message_id:
            if str(payload.emoji) in saved_emojis:
                role_id = get_reaction_role_by_emoji(guild_id, str(payload.emoji))
                role = get(guild.roles, id=role_id)
                if role is not None:
                    await member.remove_roles(role)
                    print(f"Removed {role} from {member}.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        now = datetime.now()
        guild_id = str(member.guild.id)
        guild = bot.get_guild(member.guild.id)
        member_count = guild.member_count

        updated_member_count = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
        member_count_channel_id = get_all_guild_settings(guild_id)[4]
        channel = bot.get_channel(member_count_channel_id)
        member_count_message_id = get_all_guild_settings(guild_id)[5]
        if member_count_message_id is not None:
            msg = await channel.fetch_message(member_count_message_id)
            await msg.edit(embed=updated_member_count)
        else:
            print("Member count message ID is invalid.")

        print(f"{member.guild} member count has been updated (+1) on {now}.\n Total Member Count: {member_count}")
        await member.create_dm()
        await member.dm_channel.send(f"Welcome to {member.guild}! Be sure to read the rules and have fun here!")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        now = datetime.now()
        guild_id = str(member.guild.id)
        guild = bot.get_guild(member.guild.id)
        member_count = guild.member_count

        updated_member_count = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
        member_count_channel_id = get_all_guild_settings(guild_id)[4]
        member_count_channel = bot.get_channel(member_count_channel_id)
        member_count_message_id = get_all_guild_settings(guild_id)[5]
        if member_count_channel_id is not None:
            msg = await member_count_channel.fetch_message(member_count_message_id)
            await msg.edit(embed=updated_member_count)

        print(f"{member.guild} member count has been updated (-1) on {now}.\n Total Member Count: {member_count}")
        leave_message_channel_id = get_all_guild_settings(guild_id)[6]
        if leave_message_channel_id is not None:
            leave_message_channel = bot.get_channel(leave_message_channel_id)
            leave_message = get_all_guild_settings(guild_id)[7]
            await leave_message_channel.send(f"{member.mention} {leave_message}")

    @bot.command(name='insert role reaction message', help='Sends role reaction message.', pass_context=True)
    @has_permissions(administrator=True)
    async def insert_rr_message(self, ctx):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id
        message_channel_id = ctx.channel.id

        saved_roles = get_saved_reaction_roles(guild_id)

        updated_reaction_message = update_react_message(guild_id, saved_roles)
        react_message = await ctx.channel.send(embed=updated_reaction_message)
        for role in saved_roles:
            await react_message.add_reaction(role[1])

        update_guild_role_reaction_settings(guild_id, message_channel_id, react_message.id)

    @insert_rr_message.error
    async def insert_rr_message_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You need to be an administrator to insert a role reaction message.")

    @bot.command(name='insert member count',
                 help='Sends a dynamic message to show the total member count for the server.', pass_context=True)
    @has_permissions(administrator=True)
    async def insert_member_count(self, ctx):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id
        guild = bot.get_guild(guild_id)

        member_count = guild.member_count
        embedvar = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
        member_message = await ctx.channel.send(embed=embedvar)

        update_guild_member_count_settings(guild_id, ctx.channel.id, member_message.id)

    @insert_member_count.error
    async def insert_member_count_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You need to be an administrator to insert a server total member count message.")

    @bot.command(name='set leave messages channel', help='Sets the channel where leave messages will be sent.',
                 pass_context=True)
    @has_permissions(administrator=True)
    async def set_leave_messages_channel(self, ctx):
        await ctx.interaction.response.defer()

        update_guild_leave_message_channel(ctx.guild.id, ctx.channel.id)

    @set_leave_messages_channel.error
    async def set_leave_messages_channel_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You need to be an administrator to set where the leave messages send.")

    @bot.command(name='change leave message', help='Changes the suffix of what is said after a member leaves.',
                 pass_context=True)
    @has_permissions(administrator=True)
    async def change_leave_message(self, ctx, leave_message):
        await ctx.interaction.response.defer()

        update_guild_leave_message(ctx.guild.id, leave_message)

    @change_leave_message.error
    async def change_leave_message_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You need to be an administrator to change the leave messages.")

    @bot.command(name='set random facts channel', help='Sets the channel where random facts will be sent.',
                 pass_context=True)
    @has_permissions(administrator=True)
    async def set_random_facts_channel(self, ctx):
        await ctx.interaction.response.defer()

        update_guild_random_facts_channel(ctx.guild.id, ctx.channel.id)

    @set_random_facts_channel.error
    async def set_random_facts_channel_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You need to be an administrator to set where the random facts send.")

    @bot.command(name='add reaction role', help='Adds role to role reaction message.', pass_context=True)
    @has_permissions(administrator=True)
    async def add_role(self, ctx, role: discord.Role, emoji: discord.Emoji):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id

        used_emojis = []
        saved_roles = get_saved_reaction_roles(guild_id)
        for saved_role in saved_roles:
            used_emojis.append(saved_role[1])

        if emoji in used_emojis:
            msg = await ctx.interaction.followup.send(
                embed=string_to_embed(f"This emoji is already assign to another role. Please use a different one."))
            await msg.delete(delay=10)
            return
        else:
            insert_guild_role(guild_id, role.id, emoji)

        updated_reaction_message = update_react_message(guild_id, saved_roles)

        guild_settings = get_all_guild_settings(guild_id)
        channel = guild_settings[2]
        msg = await channel.fetch_message(guild_settings[3])
        await msg.edit(embed=updated_reaction_message)
        await msg.add_reaction(emoji)

    @add_role.error
    async def add_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the permissions to change the roles.")

    @bot.command(name='remove reaction role', help='Removes role from the role reaction message.', pass_context=True)
    @has_permissions(administrator=True)
    async def remove_role(self, ctx, role: discord.Role):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id
        guild = bot.get_guild(guild_id)

        if role is not None:
            remove_guild_reaction_role(guild_id, role)

            saved_roles = get_saved_reaction_roles(guild_id)
            updated_reaction_message = update_react_message(guild_id, saved_roles)

            guild_settings = get_all_guild_settings(guild_id)
            channel = guild_settings[2]
            msg = await channel.fetch_message(guild_settings[3])
            await msg.edit(embed=updated_reaction_message)

            role_info = get_reaction_role_by_role_id(guild_id, role.id)
            for member in guild.members:
                try:
                    await msg.remove_reaction(role_info[1], member)
                except:
                    pass

    @remove_role.error
    async def remove_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the permissions to change the roles.")

    @bot.command(name='happybirthday', help='Tags a member with a bday message.')
    async def bday(self, ctx, member: discord.Member):
        await ctx.message.delete()
        member = str(member)
        member_name_end = member.find("#")
        member_name = member[:member_name_end]
        member_id = member[member_name_end + 1:]
        user_id = get(bot.get_all_members(), name=member_name, discriminator=member_id).id
        await ctx.send(f"Happy birthday <@{user_id}>!! :cake: :birthday: :tada:")

    @bot.command(name='rolldice', help='Simulates rolling dice.')
    async def roll(self, ctx, number_of_dice: int, number_of_sides: int):
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.send(', '.join(dice))

    @bot.command(name='guess', help='Guess a random number in 10 tries.')
    async def guessnumber(self, ctx):
        await ctx.send(
            f"Hello {ctx.author.name}! I'm thinking of a number between 1 and 1000. You are given 10 tries to "
            f"find the number. Good luck!")
        number = random.randint(1, 1000)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()

        for guessesTaken in range(10):

            guess = int((await bot.wait_for('message', check=check)).content)

            if guess < number:
                await ctx.send("Your guess is too low.")
            elif guess > number:
                await ctx.send("Your guess is too high.")
            else:
                await ctx.send(f"GG! You correctly guessed the number in {guessesTaken + 1} guesses!")
                return
        else:
            await ctx.send(f"Sorry, you took too many guesses. The number I was thinking of was {number}")


bot.remove_command("rolldice")
bot.remove_command("guess")
bot.remove_command("happybirthday")
bot.remove_command("add reaction role")
bot.remove_command("remove reaction role")
bot.remove_command("insert role reaction message")
bot.remove_command("insert member count")
bot.remove_command("set leave messages channel")
bot.remove_command("change leave message")
bot.remove_command("set random facts channel")
bot.remove_command("fact send time")
bot.remove_command("leave message")
bot.remove_command("addtwitch")
bot.add_cog(MetaBot(bot))


async def main():
    await bot.login(TOKEN)
    # await bot.register_application_commands()
    await bot.connect()


print("Bot started...")
loop = bot.loop
loop.run_until_complete(main())
