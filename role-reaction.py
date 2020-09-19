import os
import discord

client = discord.Client()

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')


@client.event
async def on_raw_reaction_add(payload):
    # channel and message IDs should be integer:
    if payload.channel_id == 700895165665247325 and payload.message_id == 756577133165543555:
        if str(payload.emoji) == "<:WarThunder:745425772944162907>":
            role = discord.utils.get(payload.member.guild.roles, name='War Thunder')
            await payload.member.add_roles(role)


async def on_raw_reaction_remove(payload):
    # channel and message IDs should be integer:
    if payload.channel_id == 700895165665247325 and payload.message_id == 756577133165543555:
        if str(payload.emoji) != "<:WarThunder:745425772944162907>":
            role = discord.utils.get(payload.member.guild.roles, name='War Thunder')
            await payload.member.remove_roles(role)

print("Server Running")

client.run(TOKEN)
