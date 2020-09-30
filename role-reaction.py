import os
import discord
from discord.utils import get

client = discord.Client()

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')


# This sends an embed message with a description of the roles.
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


# This is to add and remove the role Apex when the reaction is removed or added to the welcome message.
@client.event
async def on_raw_reaction_add(payload):
    # channel and message IDs should be integer:
    if payload.channel_id == 700895165665247325 and payload.message_id == 757114312413151272:
        if str(payload.emoji) == "<:Apex:745425965764575312>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(payload.member.guild.roles, name='Apex')
            await payload.member.add_roles(role)
            print(f"Assigned {member} {role}.")

        if str(payload.emoji) == "<:WarThunder:745425772944162907>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(payload.member.guild.roles, name='War Thunder')
            await payload.member.add_roles(role)
            print(f"Assigned {member} {role}.")

        if str(payload.emoji) == "<:ModernWarfare:757104623738814554>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(payload.member.guild.roles, name='Modern Warfare')
            await payload.member.add_roles(role)
            print(f"Assigned {member} {role}.")

        if str(payload.emoji) == "<:R6Siege:757030019909550122>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(payload.member.guild.roles, name='R6 Siege')
            await payload.member.add_roles(role)
            print(f"Assigned {member} {role}.")

        if str(payload.emoji) == "<:Minecraft:757029546632413346>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(payload.member.guild.roles, name='Minecraft')
            await payload.member.add_roles(role)
            print(f"Assigned {member} {role}.")

        if str(payload.emoji) == "<:AmongUs:760192601625591859>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(payload.member.guild.roles, name='Among Us')
            await payload.member.add_roles(role)
            print(f"Assigned {member} {role}.")


@client.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id == 700895165665247325 and payload.message_id == 757114312413151272:
        if str(payload.emoji) == "<:Apex:745425965764575312>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(guild.roles, name='Apex')
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")

        if str(payload.emoji) == "<:WarThunder:745425772944162907>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(guild.roles, name='War Thunder')
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")

        if str(payload.emoji) == "<:ModernWarfare:757104623738814554>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(guild.roles, name='Modern Warfare')
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")

        if str(payload.emoji) == "<:R6Siege:757030019909550122>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(guild.roles, name='R6 Siege')
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")

        if str(payload.emoji) == "<:Minecraft:757029546632413346>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(guild.roles, name='Minecraft')
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")

        if str(payload.emoji) == "<:AmongUs:760192601625591859>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = get(guild.roles, name='Among Us')
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")


print("Server Running")

client.run(TOKEN)
