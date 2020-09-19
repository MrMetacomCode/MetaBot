import os
import discord
from discord.utils import get
from discord.ext.commands import bot

client = discord.Client()

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')


@client.event
async def on_message(message):
    if message.content.startswith('React to this message to get your roles! [TEST]'):
        embedvar = discord.Embed(title="Title", description="Desc", color=0x00ff00)
        embedvar.add_field(name="Field1", value="hi", inline=False)
        embedvar.add_field(name="Field2", value="hi2", inline=False)
        await message.channel.send(embed=embedvar)
        print("Changed message embed color.")


@client.event
async def on_raw_reaction_add(payload):
    # channel and message IDs should be integer:
    if payload.channel_id == 700895165665247325 and payload.message_id == 756577133165543555:
        if str(payload.emoji) == "<:WarThunder:745425772944162907>":
            role = get(payload.member.guild.roles, name='War Thunder')
            await payload.member.add_roles(role)
            print("Assigned user role.")


@client.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id == 700895165665247325 and payload.message_id == 756577133165543555:
        if str(payload.emoji) == "<:WarThunder:745425772944162907>":
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, name='War Thunder')
            await member.remove_roles(role)
            print(f"Removed {role} from {member}.")

print("Server Running")

client.run(TOKEN)
