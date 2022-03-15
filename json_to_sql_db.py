import json
import sqlite3

conn = sqlite3.connect('GuildSettings.db')

c = conn.cursor()

c.execute("""CREATE TABLE Guilds (
            GuildID INT PRIMARY KEY NOT NULL,
            GuildName TEXT,
            RoleReactionChannelID INT,
            ReactMessageID INT,
            MemberCountChannelID INT,
            MemberCountMessageID INT,
            LeaveMessageChannelID INT,
            LeaveMessage TEXT,
            RandomFactsChannelID INT
         )""")

c.execute("""CREATE TABLE GuildRoles (
            GuildID INT,
            RoleID INT,
            RoleName TEXT,
            RoleEmoji TEXT
         )""")

c.execute("""CREATE TABLE RandomFactSendTime (
            GuildID INT PRIMARY KEY NOT NULL,
            Hour INT,
            Minute INT
         )""")


def insert_role(guild_id, role_id, role_name, role_emoji):
    if role_id is not None:
        try:
            role_id = int(role_id)
        except:
            pass
    with conn:
        c.execute(f"INSERT INTO GuildRoles VALUES (?, ?, ?, ?)", (int(guild_id), role_id, str(role_name), str(role_emoji)))


def insert_guild(guild_id, role_reaction_channel_id, react_message_id, member_count_channel_id, member_count_message_id,
                 leave_message_channel_id, leave_message, random_facts_channel_id):
    with conn:
        c.execute(f"INSERT INTO Guilds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (int(guild_id), None, role_reaction_channel_id, react_message_id, member_count_channel_id,
                   member_count_message_id, leave_message_channel_id, leave_message, random_facts_channel_id))


def insert_random_fact_send_time(guild_id, hour, minute):
    with conn:
        c.execute(f"INSERT INTO RandomFactSendTime VALUES (?, ?, ?)", (int(guild_id), int(hour), int(minute)))


with open('guild_settings.json', 'r') as file:
    guild_settings = json.loads(file.read())

for guild_id, values in guild_settings.items():
    if len(values["roles"]) > 0:
        for role_emoji, role_name in values["roles"].items():
            insert_role(guild_id, None, role_name, role_emoji)

    role_reaction_channel_id = values["role_reaction_channel_id"]
    react_message_id = values["react_message_id"]
    member_count_channel_id = values["member_count_channel_id"]
    member_count_message_id = values["member_count_message_id"]
    leave_message_channel_id = values["leave_message_channel_id"]
    leave_message = str(values["leave_message"])
    random_facts_channel_id = values["random_facts_channel_id"]
    insert_guild(guild_id, role_reaction_channel_id, react_message_id, member_count_channel_id, member_count_message_id,
                 leave_message_channel_id, leave_message, random_facts_channel_id)

    send_time_hour = values["random_facts_send_time"]["hour"]
    send_time_minute = values["random_facts_send_time"]["minute"]
    insert_random_fact_send_time(guild_id, send_time_hour, send_time_minute)

conn.commit()
conn.close()
