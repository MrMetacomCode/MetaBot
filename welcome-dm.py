import os
import discord
import datetime
from discord import Intents

intents = Intents.all()
client = discord.Client(intents=intents)

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')


# This sends a welcome DM when a new member joins the server
@client.event
async def on_member_join(member):
    now = datetime.datetime.now()
    guild_id = member.guild.id
    guild = client.get_guild(guild_id)
    member_count = guild.member_count
    metacomet_welcome_channel = client.get_channel(700895165665247325)
    metabot_welcome_channel = client.get_channel(762921541787975683)
    embedvar = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
    if guild_id == 762921541204705321:
        msg = await metabot_welcome_channel.fetch_message(770505391741337611)
        await msg.edit(embed=embedvar)
        if member_count + 1:
            print(f"MetaBot member count has been updated (+1) on {now}.\n Total Member Count: {member_count}")
        await member.create_dm()
        await member.dm_channel.send("Welcome to MetaBot! If you need help, simply message #help and tag the admin "
                                     "role for assistance with the source code.")
    elif guild_id == 593941391110045697:
        msg = await metacomet_welcome_channel.fetch_message(770472133281316914)
        await msg.edit(embed=embedvar)
        if member_count + 1:
            print(f"Metacomet member count has been updated (+1) on {now}.\n Total Member Count: {member_count}")
        await member.create_dm()
        await member.dm_channel.send(f"Welcome to Metacomet! Be sure to select your role in #welcome-and-"
                                     f"roles. Have fun here!")


@client.event
async def on_member_remove(member):
    now = datetime.datetime.now()
    guild_id = member.guild.id
    guild = client.get_guild(guild_id)
    member_count = guild.member_count
    metacomet_welcome_channel = client.get_channel(700895165665247325)
    metabot_welcome_channel = client.get_channel(762921541787975683)
    embedvar = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
    if guild_id == 593941391110045697:
        msg = await metacomet_welcome_channel.fetch_message(770472133281316914)
        await msg.edit(embed=embedvar)
        if member_count - 1:
            print(f"Metacomet member count has been updated (-1) on {now}.\n Total Member Count: {member_count}")
        channel = client.get_channel(593941391110045699)
        await channel.send(f"{member} quit on the 1 yard line (left the server).")
    elif guild_id == 762921541204705321:
        msg = await metabot_welcome_channel.fetch_message(770505391741337611)
        await msg.edit(embed=embedvar)
        if member_count - 1:
            print(f"MetaBot member count has been updated (-1) on {now}.\n Total Member Count: {member_count}")
        channel = client.get_channel(762921541787975686)
        await channel.send(f"{member} quit on the 1 yard line (left the server).")


print("Welcome-DM is Running.")

client.run(TOKEN)
