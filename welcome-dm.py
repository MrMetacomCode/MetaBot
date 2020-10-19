import os
import discord

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')

client = discord.Client()


# This sends a welcome DM when a new member joins the server
@client.event
async def on_member_join(member):
    guild1 = client.get_guild(762921541204705321)
    guild2 = client.get_guild(593941391110045697)
    if guild1.id == 762921541204705321:
        await member.create_dm()
        await member.dm_channel.send("Welcome to MetaBot! If you need help, simply message #help and tag the admin "
                                     "role for assistance with the code.")
    elif guild2.id == 593941391110045697:
        await member.create_dm()
        await member.dm_channel.send(f"Hi {member}, welcome to Metacomet! Be sure to select your role in #welcome-and-"
                                     f"roles. Have fun here!")


print("Welcome-DM is Running.")

client.run(TOKEN)
