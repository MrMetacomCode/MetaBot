import os
import discord
from discord.utils import get
from discord import Intents

intents = Intents.all()
client = discord.Client(intents=intents)

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')


# This sends or updates an embed message with a description of the roles.
@client.event
async def on_message(message):
    if message.channel.id == 700895165665247325:
        if message.content.startswith('roles'):
            embedvar = discord.Embed(title="React to this message to get your roles!",
                                     description="Click the corresponding emoji to receive your role.\n<:WarThunder:"
                                                 "745425772944162907> - War Thunder\n<:Apex:745425965764575312> - "
                                                 "Apex\n<:ModernWarfare:757104623738814554> - "
                                                 "Modern Warfare\n<:Minecraft:757029546632413346> - "
                                                 "Minecraft\n<:R6Siege:757030019909550122> - R6 Siege", color=0x00ff00)
            await message.channel.send(embed=embedvar)
            print("Changed message embed color.")
        elif message.content.startswith('update'):
            embedvar2 = discord.Embed(title="React to this message to get your roles!",
                                      description="Click the corresponding emoji to receive your role.\n<:WarThunder:"
                                                  "745425772944162907> - War Thunder\n<:Apex:745425965764575312> - "
                                                  "Apex\n<:ModernWarfare:757104623738814554> - "
                                                  "Modern Warfare\n<:Minecraft:757029546632413346> - "
                                                  "Minecraft\n<:R6Siege:757030019909550122> - R6 Siege\n"
                                                  "<:AmongUs:760192601625591859> - Among Us", color=0x00ff00)
            channel = client.get_channel(700895165665247325)
            msg = await channel.fetch_message(757114312413151272)
            await msg.edit(embed=embedvar2)
            print("Updated role reaction message.")
    else:
        return


# Assign the role when the role is added as a reaction to the message.
@client.event
async def on_raw_reaction_add(payload):
    guild = client.get_guild(payload.guild_id)
    member = get(guild.members, id=payload.user_id)
    # channel and message IDs should be integer:
    if payload.channel_id == 700895165665247325 and payload.message_id == 757114312413151272:
        if str(payload.emoji) == "<:Apex:745425965764575312>":
            role = get(payload.member.guild.roles, name='Apex')
        elif str(payload.emoji) == "<:WarThunder:745425772944162907>":
            role = get(payload.member.guild.roles, name='War Thunder')
        elif str(payload.emoji) == "<:ModernWarfare:757104623738814554>":
            role = get(payload.member.guild.roles, name='Modern Warfare')
        elif str(payload.emoji) == "<:R6Siege:757030019909550122>":
            role = get(payload.member.guild.roles, name='R6 Siege')
        elif str(payload.emoji) == "<:Minecraft:757029546632413346>":
            role = get(payload.member.guild.roles, name='Minecraft')
        elif str(payload.emoji) == "<:AmongUs:760192601625591859>":
            role = get(payload.member.guild.roles, name='Among Us')
        else:
            role = get(guild.roles, name=payload.emoji)

        if role is not None:
            await payload.member.add_roles(role)
            print(f"Assigned {member} to {role}.")


# Assign the role when the role is added as a reaction to the message.
@client.event
async def on_raw_reaction_remove(payload):
    guild = client.get_guild(payload.guild_id)
    member = get(guild.members, id=payload.user_id)
    if payload.channel_id == 700895165665247325 and payload.message_id == 757114312413151272:
        if str(payload.emoji) == "<:Apex:745425965764575312>":
            role = get(guild.roles, name='Apex')
        elif str(payload.emoji) == "<:WarThunder:745425772944162907>":
            role = get(guild.roles, name='War Thunder')
        elif str(payload.emoji) == "<:ModernWarfare:757104623738814554>":
            role = get(guild.roles, name='Modern Warfare')
        elif str(payload.emoji) == "<:R6Siege:757030019909550122>":
            role = get(guild.roles, name='R6 Siege')
        elif str(payload.emoji) == "<:Minecraft:757029546632413346>":
            role = get(guild.roles, name='Minecraft')
        elif str(payload.emoji) == "<:AmongUs:760192601625591859>":
            role = get(guild.roles, name='Among Us')
        else:
            role = discord.utils.get(guild.roles, name=payload.emoji)

        if role is not None:
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")


print("Server Running.")

client.run(TOKEN)
