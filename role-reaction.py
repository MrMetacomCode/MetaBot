import os
import discord

client = discord.Client()

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')


@client.event
async def on_reaction_add(reaction, user):
    role_channel_id = '700895165665247325'
    if reaction.message.channel.id != role_channel_id:
        return
    if str(reaction.emoji) == "<:WarThunder:745425772944162907>":
        await client.add_roles(user, name='War Thunder')


print("Server Running")

client.run(TOKEN)
