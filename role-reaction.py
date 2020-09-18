import discord

@bot.event
async def on_ready():
    channel = bot.get_channel('487165969903517696')
    role = discord.utils.get(user.server.roles, name="CSGO_P")
    message = await bot.send_message(channel, "React to me!")
    while True:
        reaction = await bot.wait_for_reaction(emoji="🏃", message=message)
        await bot.add_roles(reaction.message.author, role)
       
bot.run
