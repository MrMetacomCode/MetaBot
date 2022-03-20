import os
import os.path
import json
import emoji
import pickle
import random
import sqlite3
import aiohttp
import discord
import requests
import randfacts
from io import BytesIO
from discord import Intents
from discord import Streaming
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from discord.ext.commands import has_permissions, MissingPermissions
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands, tasks
from discord.utils import get

# TESTINGMF_DISCORD_TOKEN
TOKEN = os.getenv('TESTINGMF_DISCORD_TOKEN')
SPREADSHEET_ID = '1S-AIIx2EQrLX8RHJr_AVIGPsQjehEdfUmbwKyinOs_I'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

intents = Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)
bot.scheduler = AsyncIOScheduler()

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


def get_all_guild_ids():
    with conn:
        c.execute(f"SELECT GuildID FROM Guilds")
        return c.fetchall()


def get_table_column_names(table_name):
    table_column_names = []
    with conn:
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()

    if columns is not None:
        for column in columns:
            table_column_names.append(column[1])

    return table_column_names


def get_guild_settings(guild_id, *settings):
    column_names = get_table_column_names("Guilds")
    if set(settings).issubset(set(column_names)):
        selected_columns = ", ".join(settings)
        with conn:
            c.execute(f"SELECT {selected_columns} FROM Guilds WHERE GuildID = ?", (guild_id,))
            return c.fetchone()


def get_fact_send_time(guild_id):
    with conn:
        c.execute(f"""SELECT JobID, Hour, Minute FROM RandomFactSendTime WHERE GuildID={guild_id}""")
        return c.fetchone()


def get_saved_reaction_roles(guild_id):
    with conn:
        c.execute(f"SELECT RoleID, RoleName, RoleEmoji FROM GuildRoles WHERE GuildID={guild_id}")
        return c.fetchall()


def get_reaction_role_by_role_id(guild_id, role_id):
    with conn:
        c.execute(f"SELECT RoleID, RoleName, RoleEmoji FROM GuildRoles WHERE GuildID={guild_id} AND RoleID={role_id}")
        return c.fetchone()


def get_reaction_role_by_emoji(guild_id, emoji):
    with conn:
        c.execute(
            f"SELECT RoleID, RoleName, RoleEmoji FROM GuildRoles WHERE GuildID={int(guild_id)} AND RoleEmoji='{emoji}'")
        return c.fetchone()


def update_fact_send_time(guild_id, job_id, hour, minute):
    with conn:
        c.execute("""UPDATE RandomFactSendTime SET JobID = :job_id, Hour = :hour, Minute = :minute WHERE GuildID = :guild_id""",
                  {"job_id": job_id, "hour": hour, "minute": minute, "guild_id": guild_id})


def update_guild_role_reaction_settings(guild_id, role_reaction_channel_id, role_reaction_message_id):
    with conn:
        c.execute(
            f"""UPDATE Guilds SET RoleReactionChannelID = {role_reaction_channel_id}, ReactMessageID = {role_reaction_message_id}
                      WHERE GuildID = {guild_id}""")


def update_role_reaction(guild_id, role_id, role_name, role_emoji):
    with conn:
        c.execute(
            f"""UPDATE GuildRoles SET RoleID = {role_id}, RoleName = '{role_name}', RoleEmoji = '{role_emoji}'
                      WHERE GuildID = {guild_id} AND RoleName = '{role_name}'""")


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
        c.execute(f"""UPDATE Guilds SET LeaveMessage = '{leave_message}' WHERE GuildID = {guild_id}""")


def update_guild_random_facts_channel(guild_id, random_facts_channel_id):
    with conn:
        c.execute(f"""UPDATE Guilds SET RandomFactsChannelID = {random_facts_channel_id} WHERE GuildID = {guild_id}""")


def insert_guild(guild_id, role_reaction_channel_id, react_message_id, member_count_channel_id, member_count_message_id,
                 leave_message_channel_id, leave_message, random_facts_channel_id):
    with conn:
        c.execute(f"INSERT INTO Guilds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (int(guild_id), None, role_reaction_channel_id, react_message_id, member_count_channel_id,
                   member_count_message_id, leave_message_channel_id, leave_message, random_facts_channel_id))


def insert_rand_fact_send_time(guild_id, hour, minute, job_id=None):
    with conn:
        c.execute(f"INSERT INTO RandomFactSendTime VALUES (?, ?, ?, ?)",
                  (int(guild_id), job_id, hour, minute))


def insert_guild_role(guild_id, role_id, role_name, role_emoji):
    with conn:
        c.execute("INSERT INTO GuildRoles VALUES (?, ?, ?, ?)", (guild_id, role_id, role_name, role_emoji))


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
        role_name = role[1]
        role_emoji = role[2]
        guild = bot.get_guild(guild_id)
        if role_id is None:
            role = get(guild.roles, name=role_name)
        else:
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
        hour = int(hour)
        minute = int(minute)
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
        return f"{hour}:{minute}"


def closure(guild_id):
    async def func():
        random_facts_channel_id = get_guild_settings(int(guild_id), "RandomFactsChannelID")
        if random_facts_channel_id is not None:
            random_facts_channel = bot.get_channel(random_facts_channel_id[0])
            if random_facts_channel is not None:
                await random_facts_channel.send(embed=string_to_embed(f"{randfacts.get_fact()}."))
    return func


async def schedule_random_facts():
    if os.path.isfile('GuildSettings.db'):
        for guild in bot.guilds:
            send_time = get_fact_send_time(guild.id)
            if send_time is None or len(send_time) == 0:
                hour = 12
                minute = 0
            else:
                job_id = send_time[0]
                hour = send_time[1]
                minute = send_time[2]

            func = closure(guild.id)
            new_job = bot.scheduler.add_job(func, CronTrigger(hour=hour, minute=minute, second=0))
            update_fact_send_time(guild.id, new_job.id, hour, minute)
    else:
        print("Database file does not exist.")
        return


@bot.command(name='add-twitch', help='Adds your Twitch to the live notifications.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(
                 options=[
                     discord.ApplicationCommandOption(
                         required=True,
                         name='twitch_name',
                         type=discord.ApplicationCommandOptionType.string,
                         description='What is the username of the Twitch user you would like to add?'
                     )
                 ]
             ))
async def add_twitch(ctx, twitch_name):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        if ctx.guild.id == 762921541204705321:
            await ctx.interaction.followup.send(embed=string_to_embed(
                "If you're here to just plug your Twitch and leave, sincerely fuck off. Otherwise, "
                "feel free to stick around or ask for help :P."))
            return
        with open('streamers.json', 'r') as file:
            streamers = json.loads(file.read())

        user_id = ctx.author.id
        streamers[user_id] = twitch_name

        with open('streamers.json', 'w') as file:
            file.write(json.dumps(streamers))
        await ctx.interaction.followup.send(
            embed=string_to_embed(f"Added {twitch_name} for {ctx.author} to the Twitch notifications list."))
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@bot.command(name='change-fact-send-time', help='Change the time a random fact is sent. Hours is in 24 hour format.',
             pass_context=True, application_command_meta=commands.ApplicationCommandMeta(
                 options=[
                     discord.ApplicationCommandOption(
                         required=True,
                         name='send_hour',
                         type=discord.ApplicationCommandOptionType.integer,
                         description='What is the hour you would like the fact to send at?'
                     ),
                     discord.ApplicationCommandOption(
                         required=True,
                         name='send_minute',
                         type=discord.ApplicationCommandOptionType.integer,
                         description='What is the minute you would like the fact to send at?'
                     ),
                 ]
             ))
@has_permissions(kick_members=True)
async def fact_send_time(ctx, send_hour, send_minute):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id

        random_facts_channel_id = get_guild_settings(guild_id, "RandomFactsChannelID")
        if random_facts_channel_id is not None and len(random_facts_channel_id) > 0:
            random_facts_channel = bot.get_channel(random_facts_channel_id[0])
            if random_facts_channel is None:
                await ctx.interaction.followup.send(embed=string_to_embed(f"The channel random facts are sent in needs "
                                                                          f"to be set before you can change the time they "
                                                                          f"are sent at. Use `/set-random-facts-channel`"))
                return

        send_time = get_fact_send_time(guild_id)
        if send_time is not None and len(send_time) > 0:
            db_job_id = send_time[0]
            db_hour = send_time[1]
            db_minute = send_time[2]
            change_send_time_confirmation_components = discord.ui.MessageComponents(
                discord.ui.ActionRow(
                    (yes_button := discord.ui.Button(label="Yes")),
                    (no_button := discord.ui.Button(label="No")),
                ),
            )
            await ctx.interaction.followup.send(embed=string_to_embed(
                f"The time {convert_normal_time(db_hour, db_minute)} is currently set. Are you sure you want to change this?"),
                components=change_send_time_confirmation_components)

            def check(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    return False
                if interaction.custom_id not in [yes_button.custom_id, no_button.custom_id]:
                    return False
                return True

            change_send_time_confirmation_message_interaction = await bot.wait_for("component_interaction",
                                                                                   check=check)

            change_send_time_confirmation_components.disable_components()
            await change_send_time_confirmation_message_interaction.response.edit_message(
                components=change_send_time_confirmation_components)

            if change_send_time_confirmation_message_interaction.custom_id == no_button.custom_id:
                await ctx.interaction.followup.send(
                    embed=string_to_embed(f"No problem. Come back if you want to change it."))
                return
            else:
                if db_job_id is not None:
                    current_job = bot.scheduler.get_job(db_job_id)
                    if current_job is not None:
                        new_job = current_job.reschedule(CronTrigger(hour=send_hour, minute=send_minute, second=0))
                        update_fact_send_time(guild_id, new_job.id, send_hour, send_minute)
                        await ctx.interaction.followup.send(
                            embed=string_to_embed(
                                f"Changed fact send time to {convert_normal_time(send_hour, send_minute)}."))
                else:
                    func = closure(guild_id)
                    new_job = bot.scheduler.add_job(func, CronTrigger(hour=send_hour, minute=send_minute, second=0))
                    update_fact_send_time(guild_id, new_job.id, send_hour, send_minute)
                    await ctx.interaction.followup.send(
                        embed=string_to_embed(
                            f"Changed fact send time to {convert_normal_time(send_hour, send_minute)}."))
        else:
            await ctx.interaction.followup.send(embed=string_to_embed(
                f"This server is not in our database. Please kick and re-invite MetaBot."))
            return
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@fact_send_time.error
async def add_role_error(error, ctx):
    if isinstance(error, MissingPermissions):
        await ctx.interaction.response.send_message(
            embed=string_to_embed(f"You don't have the permissions to change the fact send time."))


@bot.event
async def on_member_update(before, after):
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
async def live_notifs_loop():
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


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("slash commands!"))

    await schedule_random_facts()
    bot.scheduler.start()

    live_notifs_loop.start()

    print("Bot is ready.")
    print(f"Total servers: {len(bot.guilds)}")


@bot.event
async def on_message(message):
    if "happy birthday" in message.content:
        await message.channel.send("Happy birthday!! :cake: :birthday: :tada:")


@bot.event
async def on_guild_join(guild):
    guild_settings = get_guild_settings(guild.id, "GuildName", "RoleReactionChannelID", "ReactMessageID",
                                        "MemberCountChannelID", "MemberCountMessageID", "LeaveMessageChannelID",
                                        "LeaveMessage", "RandomFactsChannelID")
    if guild_settings is None:
        insert_guild(guild.id, None, None, None, None, None, "quit on the 1 yard line (left the server)", None)
        insert_rand_fact_send_time(guild.id, 12, 0)


# Assign the role when the role is added as a reaction to the message.
@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)
    guild_id = str(payload.guild_id)
    member = get(guild.members, id=payload.user_id)

    role_reaction_channel_id = get_guild_settings(guild_id, "RoleReactionChannelID")[0]
    role_reaction_message_id = get_guild_settings(guild_id, "ReactMessageID")[0]

    saved_roles = get_saved_reaction_roles(guild_id)
    saved_emojis = []
    for role in saved_roles:
        saved_emojis.append(role[2])

    if payload.channel_id == role_reaction_channel_id and payload.message_id == role_reaction_message_id and member.bot is False:
        if str(payload.emoji) in saved_emojis:
            role_info = get_reaction_role_by_emoji(guild_id, str(payload.emoji))
            role_id = role_info[0]
            role_name = role_info[1]
            if role_id is None:
                role = get(guild.roles, name=role_name)
            else:
                role = get(guild.roles, id=role_id)

            if role is not None:
                update_role_reaction(guild_id, role.id, role_name, role_info[2])
                await payload.member.add_roles(role)
                print(f"Assigned {member} to {role}.")


@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    guild_id = str(payload.guild_id)
    member = get(guild.members, id=payload.user_id)

    role_reaction_channel_id = get_guild_settings(guild_id, "RoleReactionChannelID")[0]
    role_reaction_message_id = get_guild_settings(guild_id, "ReactMessageID")[0]

    saved_roles = get_saved_reaction_roles(guild_id)
    saved_emojis = []
    for role in saved_roles:
        saved_emojis.append(role[2])

    if payload.channel_id == role_reaction_channel_id and payload.message_id == role_reaction_message_id:
        if str(payload.emoji) in saved_emojis:
            role_info = get_reaction_role_by_emoji(guild_id, str(payload.emoji))
            role_id = role_info[0]
            role_name = role_info[1]
            if role_id is None:
                role = get(guild.roles, name=role_name)
            else:
                role = get(guild.roles, id=role_id)

            if role is not None:
                update_role_reaction(guild_id, role.id, role_name, role_info[2])
                await member.remove_roles(role)
                print(f"Removed {role} from {member}.")


@bot.event
async def on_member_join(member):
    now = datetime.now()
    guild_id = str(member.guild.id)
    guild = bot.get_guild(member.guild.id)
    member_count = guild.member_count

    updated_member_count = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
    member_count_channel_id = get_guild_settings(guild_id, "MemberCountChannelID")[0]
    channel = bot.get_channel(member_count_channel_id)
    member_count_message_id = get_guild_settings(guild_id, "MemberCountMessageID")[0]
    if member_count_message_id is not None:
        msg = await channel.fetch_message(member_count_message_id)
        await msg.edit(embed=updated_member_count)
    else:
        print("Member count message ID is invalid.")

    print(f"{member.guild} member count has been updated (+1) on {now}.\n Total Member Count: {member_count}")
    await member.create_dm()
    await member.dm_channel.send(f"Welcome to {member.guild}! Be sure to read the rules and have fun here!")


@bot.event
async def on_member_remove(member):
    if not member.bot:
        now = datetime.now()
        guild_id = str(member.guild.id)
        guild = bot.get_guild(member.guild.id)
        member_count = guild.member_count

        updated_member_count = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
        member_count_channel_id = get_guild_settings(guild_id, "MemberCountChannelID")[0]
        member_count_channel = bot.get_channel(member_count_channel_id)
        member_count_message_id = get_guild_settings(guild_id, "MemberCountMessageID")[0]
        if member_count_channel_id is not None:
            msg = await member_count_channel.fetch_message(member_count_message_id)
            await msg.edit(embed=updated_member_count)

        print(f"{member.guild} member count has been updated (-1) on {now}.\n Total Member Count: {member_count}")
        leave_message_channel_id = get_guild_settings(guild_id, "LeaveMessageChannelID")[0]
        if leave_message_channel_id is not None:
            leave_message_channel = bot.get_channel(leave_message_channel_id)
            leave_message = get_guild_settings(guild_id, "LeaveMessage")[0]
            await leave_message_channel.send(f"{member.mention} {leave_message}")


@bot.command(name='insert-role-reaction-message', help='Sends role reaction message.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(options=[]))
@has_permissions(administrator=True)
async def insert_rr_message(ctx):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id
        message_channel_id = ctx.channel.id

        saved_roles = get_saved_reaction_roles(guild_id)

        updated_reaction_message = update_react_message(guild_id, saved_roles)
        react_message = await ctx.channel.send(embed=updated_reaction_message)
        for role in saved_roles:
            await react_message.add_reaction(role[1])

        update_guild_role_reaction_settings(guild_id, message_channel_id, react_message.id)
        msg = await ctx.interaction.followup.send(
            embed=string_to_embed(f"Interaction message has been sent. This message will delete."), ephemeral=True)
        await msg.delete(delay=5)
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@insert_rr_message.error
async def insert_rr_message_error(error, ctx):
    if isinstance(error, MissingPermissions):
        await ctx.interaction.response.send_message(
            embed=string_to_embed("You need to be an administrator to insert a role reaction message."))


@bot.command(name='insert-member-count', help='Sends a dynamic message to show the total member count for the server.',
             pass_context=True, application_command_meta=commands.ApplicationCommandMeta(options=[]))
@has_permissions(administrator=True)
async def insert_member_count(ctx):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id
        guild = bot.get_guild(guild_id)

        member_count = guild.member_count
        embedvar = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
        member_message = await ctx.channel.send(embed=embedvar)

        update_guild_member_count_settings(guild_id, ctx.channel.id, member_message.id)
        msg = await ctx.interaction.followup.send(
            embed=string_to_embed(f"Member count message has been sent. This message will delete."), ephemeral=True)
        await msg.delete(delay=5)
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@insert_member_count.error
async def insert_member_count_error(error, ctx):
    if isinstance(error, MissingPermissions):
        await ctx.interaction.response.send_message(
            embed=string_to_embed("You need to be an administrator to insert a server total member count message."))


@bot.command(name='set-leave-messages-channel', help='Sets the channel where leave messages will be sent.',
             pass_context=True, application_command_meta=commands.ApplicationCommandMeta(
        options=[
            discord.ApplicationCommandOption(
                required=True,
                name='channel',
                type=discord.ApplicationCommandOptionType.channel,
                description='What channel would you like leave messages to be sent in?'
            )
        ]
    ))
@has_permissions(administrator=True)
async def set_leave_messages_channel(ctx, channel: discord.TextChannel):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        update_guild_leave_message_channel(ctx.guild.id, channel.id)
        await ctx.interaction.followup.send(embed=string_to_embed(f"Leave messages will be sent in {channel.mention}"))
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@set_leave_messages_channel.error
async def set_leave_messages_channel_error(error, ctx):
    if isinstance(error, MissingPermissions):
        await ctx.interaction.response.send_message(
            embed=string_to_embed("You need to be an administrator to set where the leave messages send."))


@bot.command(name='change-leave-message', help='Changes the suffix of what is said after a member leaves.',
             pass_context=True, application_command_meta=commands.ApplicationCommandMeta(
        options=[
            discord.ApplicationCommandOption(
                required=True,
                name='leave_message',
                type=discord.ApplicationCommandOptionType.string,
                description='What is the suffix you would like after a user leaves?'
            )
        ]
    ))
@has_permissions(administrator=True)
async def change_leave_message(ctx, leave_message):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        update_guild_leave_message(ctx.guild.id, leave_message)
        await ctx.interaction.followup.send(
            embed=string_to_embed(
                f"Changed server leave message to: `{leave_message}`\n__Example__\nInstead of: Bobby#1234 left the server.\nIt is now: Bobby#1234 {leave_message}"))
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@change_leave_message.error
async def change_leave_message_error(error, ctx):
    if isinstance(error, MissingPermissions):
        await ctx.interaction.response.send_message(
            embed=string_to_embed("You need to be an administrator to change the leave messages."))


@bot.command(name='set-random-facts-channel', help='Sets the channel where random facts will be sent.',
             pass_context=True, application_command_meta=commands.ApplicationCommandMeta(
                 options=[
                     discord.ApplicationCommandOption(
                         required=True,
                         name='channel',
                         type=discord.ApplicationCommandOptionType.channel,
                         description='What is the channel you would like random facts to be sent in?'
                     )
                 ]
             ))
@has_permissions(administrator=True)
async def set_random_facts_channel(ctx, channel: discord.TextChannel):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        update_guild_random_facts_channel(ctx.guild.id, channel.id)
        await ctx.interaction.followup.send(embed=string_to_embed(f"Random facts will be sent in {channel.mention}"))
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@set_random_facts_channel.error
async def set_random_facts_channel_error(error, ctx):
    if isinstance(error, MissingPermissions):
        await ctx.interaction.response.send_message(
            embed=string_to_embed("You need to be an administrator to set where the random facts send."))


@bot.command(name='add-reaction-role', help='Adds role to role reaction message.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(
                 options=[
                     discord.ApplicationCommandOption(
                         required=True,
                         name='role',
                         type=discord.ApplicationCommandOptionType.role,
                         description='What is the role you would like to add to the reaction message?'
                     ),
                     discord.ApplicationCommandOption(
                         required=True,
                         name='role_emoji',
                         type=discord.ApplicationCommandOptionType.string,
                         description="What is the emoji you would like to assign to the role you're adding?"
                     )
                 ]
             ))
@has_permissions(administrator=True)
async def add_role(ctx, role: discord.Role, role_emoji: str):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id
        guild = bot.get_guild(guild_id)

        used_emojis = []
        saved_roles = get_saved_reaction_roles(guild_id)
        for saved_role in saved_roles:
            used_emojis.append(saved_role[2])

        guild_emoji_strings = []
        for guild_emoji in guild.emojis:
            guild_emoji_strings.append(str(guild_emoji))

        if role_emoji in used_emojis:
            msg = await ctx.interaction.followup.send(
                embed=string_to_embed(f"This emoji is already assigned to another role. Please use a different one."))
            await msg.delete(delay=5)
            return
        elif role_emoji not in guild_emoji_strings and role_emoji not in emoji.EMOJI_DATA:
            msg = await ctx.interaction.followup.send(
                embed=string_to_embed(f"The emoji you gave does not exist or is not in this server. This message will delete."))
            await msg.delete(delay=5)
            return
        else:
            guild_reaction_roles = get_saved_reaction_roles(guild_id)
            reaction_role_ids = []
            if guild_reaction_roles is not None:
                for saved_role in guild_reaction_roles:
                    reaction_role_ids.append(saved_role[0])

            if role.id in reaction_role_ids:
                update_role_reaction(guild_id, role.id, role.name, role_emoji)
                await ctx.interaction.followup.send(
                    embed=string_to_embed(f"{role.mention} is already in the list of reaction roles."))
                return
            else:
                insert_guild_role(guild_id, role.id, role.name, role_emoji)

        guild_settings = get_guild_settings(guild_id, "RoleReactionChannelID", "ReactMessageID")
        if guild_settings is not None:
            channel_id = guild_settings[0]
            if channel_id is not None:
                channel = bot.get_channel(channel_id)
                if channel is not None:
                    msg = await channel.fetch_message(guild_settings[1])
                    if msg is not None:
                        new_role_info = (role.id, role.name, role_emoji)
                        saved_roles.append(new_role_info)
                        updated_reaction_embed = update_react_message(guild_id, saved_roles)
                        await msg.edit(embed=updated_reaction_embed)
                        await msg.add_reaction(role_emoji)
                        msg = await ctx.interaction.followup.send(
                            embed=string_to_embed(
                                f"{role.mention} has been added to the role reaction message. This message will delete."))
                        await msg.delete(delay=5)
            else:
                await ctx.interaction.followup.send(
                    embed=string_to_embed(f"The role reaction message has not been created yet. To do this, run "
                                          f"`/insert-role-reaction-message` in the channel you would like it to show up in."))
                return
        else:
            await ctx.interaction.followup.send(
                embed=string_to_embed(f"This server isn't in our database. Try kicking and adding me again."))
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@add_role.error
async def add_role_error(error, ctx):
    if isinstance(error, MissingPermissions):
        await ctx.interaction.response.send_message(
            embed=string_to_embed("You don't have the permissions to change the roles."))


@bot.command(name='remove-reaction-role', help='Removes role from the role reaction message.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(
                 options=[
                     discord.ApplicationCommandOption(
                         required=True,
                         name='role',
                         type=discord.ApplicationCommandOptionType.role,
                         description='What is the role you would like to remove from the reaction message?'
                     )
                 ]
             ))
@has_permissions(administrator=True)
async def remove_role(ctx, role: discord.Role):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()

        guild_id = ctx.guild.id
        guild = bot.get_guild(guild_id)
        metabot = get(guild.members, id=753479351139303484)

        if role is not None:
            role_being_removed_info = get_reaction_role_by_role_id(guild_id, role.id)
            remove_guild_reaction_role(guild_id, role)

            saved_roles = get_saved_reaction_roles(guild_id)
            updated_reaction_message = update_react_message(guild_id, saved_roles)

            guild_settings = get_guild_settings(guild_id, "RoleReactionChannelID", "ReactMessageID")
            if guild_settings is not None:
                channel_id = guild_settings[0]
                if channel_id is not None:
                    channel = bot.get_channel(channel_id)
                    if channel is not None:
                        msg = await channel.fetch_message(guild_settings[1])
                        if msg is not None:
                            await msg.edit(embed=updated_reaction_message)
                            for member in guild.members:
                                try:
                                    await msg.remove_reaction(role_being_removed_info[2], member)
                                except Exception:
                                    continue
                            msg = await ctx.interaction.followup.send(
                                embed=string_to_embed(
                                    f"{role.mention} has been removed from the role reaction message. This message will delete."))
                            await msg.delete(delay=5)
                else:
                    await ctx.interaction.followup.send(
                        embed=string_to_embed(f"The role reaction message has not been created yet. To do this, run "
                                              f"`/insert-role-reaction-message` in the channel you would like it to show up in."))
                    return
            else:
                await ctx.interaction.followup.send(
                    embed=string_to_embed(f"This server isn't in our database. Try kicking and adding me again."))
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@remove_role.error
async def remove_role_error(error, ctx):
    if isinstance(error, MissingPermissions):
        await ctx.interaction.response.send_message(
            embed=string_to_embed("You don't have the permissions to change the roles."))


@bot.command(name='update-role-reaction-message', help='Updates the role reaction message.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(options=[]))
@has_permissions(administrator=True)
async def update_message(ctx):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()
        guild_id = ctx.guild.id

        saved_roles = get_saved_reaction_roles(guild_id)
        updated_reaction_message = update_react_message(guild_id, saved_roles)

        guild_settings = get_guild_settings(guild_id, "RoleReactionChannelID", "ReactMessageID")
        if guild_settings is not None:
            channel_id = guild_settings[0]
            if channel_id is not None:
                channel = bot.get_channel(channel_id)
                if channel is not None:
                    msg = await channel.fetch_message(guild_settings[1])
                    if msg is not None:
                        await msg.edit(embed=updated_reaction_message)
                        msg = await ctx.interaction.followup.send(embed=string_to_embed(f"Role reaction message has been updated. This message will delete."))
                        await msg.delete(delay=5)
                        return
                    else:
                        await ctx.interaction.followup.send(
                            embed=string_to_embed(f"Role reaction message could not be found. Please insert a new one using `/insert-role-reaction-message`."))
                        return
            else:
                await ctx.interaction.followup.send(
                    embed=string_to_embed(f"The role reaction message has not been created yet. To do this, run "
                                          f"`/insert-role-reaction-message` in the channel you would like it to show up in."))
                return
        else:
            await ctx.interaction.followup.send(
                embed=string_to_embed(f"This server isn't in our database. Try kicking and adding me again."))
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


@bot.command(name='happy-birthday', help='Tags a member with a happy birthday message.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(
                 options=[
                     discord.ApplicationCommandOption(
                         required=True,
                         name='member',
                         type=discord.ApplicationCommandOptionType.user,
                         description='What is the user you would like to congratulate?'
                     )
                 ]
             ))
async def happy_birthday(ctx, member: discord.Member):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()
        member = str(member)
        member_name_end = member.find("#")
        member_name = member[:member_name_end]
        member_id = member[member_name_end + 1:]
        user_id = get(bot.get_all_members(), name=member_name, discriminator=member_id).id
        await ctx.interaction.followup.send(
            embed=string_to_embed(f"Happy birthday <@{user_id}>!! :cake: :birthday: :tada:"))
    else:
        await ctx.send(string_to_embed(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484"))


@bot.command(name='roll-dice', help='Simulates rolling dice.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(
                 options=[
                     discord.ApplicationCommandOption(
                         required=True,
                         name='number_of_dice',
                         type=discord.ApplicationCommandOptionType.integer,
                         description='What is the number of dice you are simulating rolling?'
                     ),
                     discord.ApplicationCommandOption(
                         required=True,
                         name='number_of_sides',
                         type=discord.ApplicationCommandOptionType.integer,
                         description='What is the number of sides on each die you are simulating rolling?'
                     )
                 ]
             ))
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.interaction.followup.send(embed=string_to_embed(', '.join(dice)))
    else:
        await ctx.send(string_to_embed(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484"))


@bot.command(name='guess', help='Guess a random number in 10 tries.', pass_context=True,
             application_command_meta=commands.ApplicationCommandMeta(options=[]))
async def guess_number(ctx):
    if hasattr(ctx, "interaction"):
        await ctx.interaction.response.defer()
        await ctx.interaction.followup.send(embed=string_to_embed(
            f"Hello {ctx.author.name}! I'm thinking of a number between 1 and 1000. You are given 10 tries to "
            f"find the number. Good luck!"))
        number = random.randint(1, 1000)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()

        for guessesTaken in range(10):

            guess = int((await bot.wait_for('message', check=check)).content)

            if guess < number:
                await ctx.interaction.followup.send(embed=string_to_embed("Your guess is too low."))
            elif guess > number:
                await ctx.interaction.followup.send(embed=string_to_embed("Your guess is too high."))
            else:
                await ctx.interaction.followup.send(
                    embed=string_to_embed(f"GG! You correctly guessed the number in {guessesTaken + 1} guesses!"))
                return
        else:
            await ctx.interaction.followup.send(embed=string_to_embed(
                f"Sorry, you took too many guesses. The number I was thinking of was {number}"))
    else:
        await ctx.send(
            "MetaBot is now using slash commands! Simply type / and it will bring up the list of commands to use. "
            "If the commands don't show up, make sure MetaBot has the permission 'Use Application Commands'. If that doesn't "
            "work, just kick and re-invite the bot. Top.gg bot page (includes invite link): "
            "https://top.gg/bot/753479351139303484")


bot.remove_command("help")


async def main():
    await bot.login(TOKEN)
    await bot.register_application_commands(bot.commands)
    await bot.connect()


print("Bot started...")
loop = bot.loop
loop.run_until_complete(main())
