import os
import discord

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')

client = discord.Client()


# This sends a welcome DM when a new member joins the server
@client.event
async def on_member_join(member):
    guild_id = member.guild.id
    if guild_id == 762921541204705321:
        await member.create_dm()
        await member.dm_channel.send("Welcome to MetaBot! If you need help, simply message #help and tag the admin "
                                     "role for assistance with the source code.")
    elif guild_id == 593941391110045697:
        await member.create_dm()
        await member.dm_channel.send(f"Welcome to Metacomet! Be sure to select your role in #welcome-and-"
                                     f"roles. Have fun here!")


@client.event
async def on_member_remove(member):
    guild_id = member.guild.id
    if guild_id == 593941391110045697:
        channel = client.get_channel(593941391110045699)
        await channel.send(f"{member} quit on the 1 yard line (left the server).")
    elif guild_id == 762921541204705321:
        channel = client.get_channel(762921541787975686)
        await channel.send(f"{member} quit on the 1 yard line (left the server).")


print("Welcome-DM is Running.")

client.run(TOKEN)
