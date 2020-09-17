import os

import discord

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')

client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')


@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to Metacomet! Be sure to select your role in #welcome-and-roles.  Have fun here!'
    )

print("Welcome-DM is Running")

client.run(TOKEN)
