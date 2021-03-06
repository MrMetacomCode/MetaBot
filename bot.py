import os
import os.path
import json
import pickle
import random
import discord
import datetime
import asyncio
import requests
from discord import Intents
from discord import Streaming
from twitchAPI.twitch import Twitch
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from discord.ext.commands import has_permissions, MissingPermissions
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands, tasks
from discord.utils import get
# import logging

# logging.basicConfig(level=logging.DEBUG, filename='logs.txt')
# logger = logging.getLogger(__name__)
# logger.debug('test')

# TESTINGBOT_DISCORD_TOKEN
TOKEN = os.getenv('METABOT_DISCORD_TOKEN')
SPREADSHEET_ID = '1S-AIIx2EQrLX8RHJr_AVIGPsQjehEdfUmbwKyinOs_I'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

intents = Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
twitch = Twitch(client_id, client_secret)
twitch.authenticate_app([])
TWITCH_STREAM_API_ENDPOINT_V5 = "https://api.twitch.tv/kraken/streams/{}"
API_HEADERS = {
    'Client-ID': client_id,
    'Accept': 'application/vnd.twitchtv.v5+json',
}

creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Beginning of economy system.
class Metacash(commands.Cog):
    """Economy bot commands."""
    main_shop = [{"name": "Watch", "price": 100, "description": "Time"},
                 {"name": "Laptop", "price": 1000, "description": "Work"},
                 {"name": "PC", "price": 10000, "description": "Gaming"}]

    async def get_bank_data(self):
        with open("mainbank.json", "r") as bank:
            users = json.load(bank)
        return users

    async def open_account(self, user):
        users = await self.get_bank_data()

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["wallet"] = 0
            users[str(user.id)]["bank"] = 0

        with open("mainbank.json", "w") as bank:
            json.dump(users, bank)
        return True

    async def update_bank(self, user, change=0, mode="wallet"):
        users = await self.get_bank_data()
        users[str(user.id)][mode] += change

        with open("mainbank.json", "w") as bank:
            json.dump(users, bank)

        bal = [users[str(user.id)]["wallet"], users[str(user.id)]["bank"]]
        return bal

    async def buy_this(self, user, item_name, amount):
        item_name = item_name.lower()
        name_ = None
        for item in self.main_shop:
            name = item["name"].lower()
            if name == item_name:
                name_ = name
                price = item["price"]
                break

        if name_ is None:
            return [False, 1]
        amount = int(amount)
        cost = price * amount

        users = await self.get_bank_data()

        bal = await self.update_bank(user)

        if bal[0] < cost:
            return [False, 2]

        try:
            index = 0
            t = None
            for thing in users[str(user.id)]["bag"]:
                n = thing["item"]
                if n == item_name:
                    old_amt = thing["amount"]
                    new_amt = old_amt + amount
                    users[str(user.id)]["bag"][index]["amount"] = new_amt
                    t = 1
                    break
                index += 1
            if t is None:
                obj = {"item": item_name, "amount": amount}
                users[str(user.id)]["bag"].append(obj)
        except:
            obj = {"item": item_name, "amount": amount}
            users[str(user.id)]["bag"] = [obj]

        with open("mainbank.json", "w") as f:
            json.dump(users, f)

        await self.update_bank(user, cost * -1, "wallet")

        return [True, "Worked"]

    async def sell_this(self, user, item_name, amount, price=None):
        item_name = item_name.lower()
        name_ = None
        for item in self.main_shop:
            name = item["name"].lower()
            if name == item_name:
                name_ = name
                if price == None:
                    price = 0.9 * item["price"]
                break

        if name_ == None:
            return [False, 1]

        cost = price * amount

        users = await self.get_bank_data()

        bal = await self.update_bank(user)

        try:
            index = 0
            t = None
            for thing in users[str(user.id)]["bag"]:
                n = thing["item"]
                if n == item_name:
                    old_amt = thing["amount"]
                    new_amt = old_amt - amount
                    if new_amt < 0:
                        return [False, 2]
                    users[str(user.id)]["bag"][index]["amount"] = new_amt
                    t = 1
                    break
                index += 1
            if t is None:
                return [False, 3]
        except:
            return [False, 3]

        with open("mainbank.json", "w") as f:
            json.dump(users, f)

        await self.update_bank(user, cost, "wallet")

        return [True, "Worked"]

    @bot.command()
    async def leaderboard(self, ctx, x=3):
        users = await self.get_bank_data()
        leader_board = {}
        total = []
        for user in users:
            name = int(user)
            total_amount = users[user]["wallet"] + users[user]["bank"]
            leader_board[total_amount] = name
            total.append(total_amount)

        total = sorted(total, reverse=True)

        embedvar = discord.Embed(title=f"Top {x} Richest People", description="This is a total of bank and wallet "
                                                                              "money.", color=3394611)
        index = 1
        for amt in total:
            id_ = leader_board[amt]
            member = bot.get_user(id_)
            name = member.name
            embedvar.add_field(name=f"{index}. {name}", value=f"{amt}", inline=False)
            if index == x:
                break
            else:
                index += 1

        await ctx.send(embed=embedvar)

    @bot.command()
    async def shop(self, ctx):
        embedvar = discord.Embed(title="Shop")

        for item in self.main_shop:
            name = item["name"]
            price = item["price"]
            desc = item["description"]
            embedvar.add_field(name=name, value=f"${price} | {desc}")

        await ctx.send(embed=embedvar)

    @bot.command()
    async def buy(self, ctx, item, amount):

        res = await self.buy_this(ctx.author, item, amount)

        if not res[0]:
            if res[1] == 1:
                await ctx.send("This item doesn't exist.")
                return
            elif res[1] == 2:
                await ctx.send(f"You don't have the sufficient funds in your wallet to buy {item}.")
                return

        await ctx.send(f"You just bought {amount} of {item}.")

    @bot.command()
    async def sell(self, ctx, item, amount=1):
        await self.open_account(ctx.author)

        res = await self.sell_this(ctx.author, item, amount)

        if not res[0]:
            if res[1] == 1:
                await ctx.send("That item doesn't exist.")
                return
            elif res[1] == 2:
                await ctx.send(f"You don't have {amount} of {item} in your inventory.")
                return
            elif res[1] == 3:
                await ctx.send(f"You don't have {item} in your inventory.")
                return

        await ctx.send(f"You sold {amount} of {item}.")

    @bot.command()
    async def inventory(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author
        users = await self.get_bank_data()

        try:
            bag = users[str(user.id)]["bag"]
        except:
            bag = []

        embedvar = discord.Embed(title="Bag")
        for item in bag:
            name = item["item"]
            amount = item["amount"]

            embedvar.add_field(name=name, value=amount)

        await ctx.send(embed=embedvar)

    @bot.command(help="Withdraw money from your bank to your wallet.")
    async def withdraw(self, ctx, amount=None):
        await self.open_account(ctx.author)
        if amount is None:
            await ctx.send("Please enter the amount.")
            return

        bal = await self.update_bank(ctx.author)
        amount = int(amount)
        if amount > bal[1]:
            await ctx.send("You don't have the sufficient funds.")
            return
        elif amount < 0:
            await ctx.send("Amount must be positive.")
            return

        await self.update_bank(ctx.author, amount)
        await self.update_bank(ctx.author, -1 * amount, "bank")
        await ctx.send(f"You withdrew {amount} coins.")

    @bot.command(help="Deposit money from your wallet to your bank.")
    async def deposit(self, ctx, amount=None):
        await self.open_account(ctx.author)
        if amount is None:
            await ctx.send("Please enter the amount.")
            return

        bal = await self.update_bank(ctx.author)

        amount = int(amount)
        if amount > bal[0]:
            await ctx.send("You don't have the sufficient funds.")
            return
        elif amount < 0:
            await ctx.send("Amount must be positive.")
            return

        await self.update_bank(ctx.author, -1 * amount)
        await self.update_bank(ctx.author, amount, "bank")
        await ctx.send(f"You deposited {amount} coins.")

    @bot.command(help="Send money to someone.")
    async def send(self, ctx, member: discord.Member, amount=None):
        await self.open_account(ctx.author)
        await self.open_account(member)
        if amount is None:
            await ctx.send("Please enter the amount.")
            return

        bal = await self.update_bank(ctx.author)
        if amount == "all":
            amount = bal[0]

        amount = int(amount)
        if amount > bal[1]:
            await ctx.send("You don't have the sufficient funds.")
            return
        elif amount < 0:
            await ctx.send("Amount must be positive.")
            return

        await self.update_bank(ctx.author, -1 * amount)
        await self.update_bank(member, amount, "bank")
        await ctx.send(f"You gave {member} {amount} coins.")

    @bot.command(help="Steal a random amount of MetaCash from someone.")
    async def rob(self, ctx, member: discord.Member):
        await self.open_account(ctx.author)
        await self.open_account(member)

        bal = await self.update_bank(member)

        if bal[0] < 200:
            await ctx.send("User doesn't have enough money to rob.")
            return

        earnings = random.randrange(0, bal[0])

        await self.update_bank(ctx.author, earnings)
        await self.update_bank(member, -1 * earnings)
        await ctx.send(f"You robbed {member} of {earnings} MetaCash.")

    @bot.command(help="Slots gambling game.")
    async def slots(self, ctx, amount=None):
        await self.open_account(ctx.author)
        if amount is None:
            await ctx.send("Please enter the amount.")
            return

        bal = await self.update_bank(ctx.author)

        amount = int(amount)
        if amount > bal[0]:
            await ctx.send("You don't have the sufficient funds.")
            return
        elif amount < 0:
            await ctx.send("Amount must be positive.")
            return

        final = []
        for i in range(3):
            a = random.choice(["X", "O", "Q", "A", "I", "Z", "O", "W", "U", "C"])

            final.append(a)

        await ctx.send(str(final))
        if final[0] == final[1] or final[0] == final[2] or final[2] == final[1]:
            await ctx.send(f"You won! {2 * amount} has been added to your account.")
            await self.update_bank(ctx.author, 2 * amount)
        else:
            await ctx.send(f"You lost :(. {-1 * amount} has been removed from your account.")
            await self.update_bank(ctx.author, -1 * amount)

    @bot.command(help="Displays current wallet and bank balance.")
    async def balance(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author
        users = await self.get_bank_data()

        wallet_amt = users[str(user.id)]["wallet"]
        bank_amt = users[str(user.id)]["bank"]

        embedvar = discord.Embed(title=f"{ctx.author.name}'s balance", color=3394611)
        embedvar.add_field(name="Wallet", value=wallet_amt)
        embedvar.add_field(name="Bank Balance", value=bank_amt)
        await ctx.send(embed=embedvar)

    @bot.command(help="Gives you MetaCash.")
    async def beg(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author
        users = await self.get_bank_data()
        earnings = random.randrange(50)
        await ctx.send(f"Someone gave you {earnings} coins!")

        users[str(user.id)]["wallet"] += earnings

        with open("mainbank.json", "w") as bank:
            json.dump(users, bank)


bot.remove_command("withdraw")
bot.remove_command("deposit")
bot.remove_command("send")
bot.remove_command("rob")
bot.remove_command("slots")
bot.remove_command("balance")
bot.remove_command("beg")
bot.remove_command("shop")
bot.remove_command("buy")
bot.remove_command("inventory")
bot.remove_command("leaderboard")
bot.remove_command("sell")
bot.add_cog(Metacash(bot))


# End of economy system.

class MetaBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def embed_maker(self, thing_list):
        list_number = 1
        embed = ""
        for thing in thing_list:
            item = f"{list_number} = {thing}\n"
            embed += item
            list_number += 1
        return embed

    @bot.command(name='jail', help='Jails tagged user for specified amount of time.', pass_context=True)
    @has_permissions(kick_members=True)
    async def jail_member(self, ctx, member: discord.Member):
        if ctx.guild.id == 593941391110045697:
            for role in member.roles:
                if str(role) == "JAIL":
                    await ctx.send("This member is already in jail.")
                    return
            jail_times = ["24 Hours", "1 Week", "1 Month"]
            jail_times_embed = self.embed_maker(jail_times)
            embedvar = discord.Embed(title=f"Select a time to jail {member} for:",
                                     description=jail_times_embed,
                                     color=0x00ff00)
            await ctx.send(embed=embedvar)

            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel

            for x in range(5):
                jail_time_number = (await bot.wait_for('message', check=check)).content
                try:
                    jail_time_number = int(jail_time_number)
                except ValueError:
                    await ctx.send("Please use a number.")
                    continue
                break
            else:
                await ctx.send("You didn't use a number. Goodbye.")
                return

            jail_time = 24
            jail_time_type = "Hours"
            if jail_time_number == 1:
                jail_time = 24
                jail_time_type = "Hours"
            elif jail_time_number == 2:
                jail_time = 168
                jail_time_type = "Days"
            elif jail_time_number == 3:
                jail_time = 672
                jail_time_type = "Month"

            await ctx.send(f"Enter a reason for jailing {member}:")
            reason = str((await bot.wait_for('message', check=check)).content)

            general_channel = bot.get_channel(593941391110045699)
            await general_channel.send(f"{member} has been jailed for {jail_time} {jail_time_type.lower()}.")

            # If the user is in a voice chat, disconnect them.
            if member.voice is None:
                pass
            else:
                await member.move_to(None)

            now = datetime.datetime.now()
            guild = ctx.guild
            jail_channel = bot.get_channel(773397004868649010)
            roles = []
            for role in member.roles:
                role = str(role)
                roles.append(role)
            roles = roles[1:]
            roles_display = ""
            if len(roles) >= 3:
                for role in roles[:-1]:
                    roles_display += f"{role}, "
                roles_display += f"and {roles[-1]}."
            elif len(roles) == 2:
                roles_display += f"{roles[0]} and {roles[1]}."
            else:
                roles_display += f"{roles[0]}."
            # Converting 24h time to normal time.
            try:
                now2 = str(now).split(" ")
                date = now2[0]
                date_items = date.split("-")
                year = date_items[0]
                month = date_items[1]
                day = date_items[2]
                time = now2[1]
                time_items = time.split(":")
                hour = int(time_items[0])
                minute = int(time_items[1])
                if hour < 12:
                    morning_or_night = "am"
                elif hour >= 12:
                    morning_or_night = "pm"
                if hour > 12:
                    hour = hour - 12
                if hour == 0:
                    hour = 12
                new_date = f"{month}/{day}/{year}"
                new_time = f"{hour}:{minute}{morning_or_night}"
                now = f"{new_date} at {new_time}"
            except:
                now = datetime.datetime.now()

            jail_ticket_embed = discord.Embed(title=f"{member} has been jailed on {now}",
                                              description=f"Reason: {reason}\nYou will be released in: {jail_time} {jail_time_type}",
                                              color=0x00ff00)
            jail_ticket_message = await jail_channel.send(embed=jail_ticket_embed)
            for role in roles:
                role = get(guild.roles, name=role)
                await member.remove_roles(role)
            jail_role = get(guild.roles, name="JAIL")
            await member.add_roles(jail_role)
            await ctx.send(f"{member} has been jailed.")

            await asyncio.sleep(delay=jail_time * 3600)
            for role in roles:
                role = get(guild.roles, name=role)
                await member.add_roles(role)
            await member.remove_roles(jail_role)
            await general_channel.send(f"{member} has been released from jail.")
            jail_ticket_title = jail_ticket_embed.title
            jail_ticket_description = jail_ticket_embed.description
            released_jail_ticket = discord.Embed(title=f"🔓STATUS: RELEASED\n{jail_ticket_title}",
                                                 description=f"{jail_ticket_description}",
                                                 color=0x00ff00)
            await jail_ticket_message.edit(embed=released_jail_ticket)
        else:
            await ctx.send("This command is reserved and hasn't been rolled out for use with all servers.")

    @bot.command(name='addfact', aliases=['addfacts'], help='Adds fact to random facts list.', pass_context=True)
    @has_permissions(kick_members=True)
    async def add_fact(self, ctx, fact_name=None, fact=None):
        fact_name = fact_name.upper()
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        guild_id = str(ctx.guild.id)
        if fact_name is None:
            await ctx.send("Please include a fact name.")
            return
        elif fact is None:
            await ctx.send("Please include fact. Make sure **'fact name' 'fact'** is the format you are using.")
            return

        if fact_name in guild_settings[guild_id]["random_facts"]:
            await ctx.send(f"{fact_name} is already in the random facts list.")
            return
        else:
            guild_settings[guild_id]["random_facts"][fact] = fact_name
            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))
            await ctx.send(f"Added {fact_name} to the random facts list.")

    @add_fact.error
    async def add_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the permissions to change the random facts.")

    @bot.command(name='removefact', aliases=['removefacts'], help='Adds fact to random facts list.', pass_context=True)
    @has_permissions(kick_members=True)
    async def remove_fact(self, ctx, fact_name):
        fact_name = fact_name.upper()
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        guild_id = str(ctx.guild.id)
        fact = None
        for key, value in guild_settings[guild_id]["random_facts"].items():
            if value == fact_name:
                fact = key

        if fact not in guild_settings[guild_id]["random_facts"]:
            await ctx.send(f"{fact_name} isn't in the random facts list.")
            return
        else:
            guild_settings[guild_id]["random_facts"].pop(fact)
            await ctx.send(f"{fact_name} has been removed from the random facts list.")
            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

    @remove_fact.error
    async def add_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the permissions to change the random facts.")

    @bot.command(name='listfacts', aliases=['listfact', 'listrandomfact', 'listrandomfacts'], help='Lists all facts '
                                                                                                   'in random facts '
                                                                                                   'list.')
    async def list_facts(self, ctx):
        # This is the first part of listfacts. The rest is in on_reaction_add below this command.
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        guild_id = str(ctx.guild.id)

        facts_display = ""
        facts = []
        for fact_name, fact in guild_settings[guild_id]["random_facts"].items():
            item = f"{fact_name} - {fact}"
            facts.append(item)

        for fact in facts[:8]:
            facts_display += f"{fact}\n\n"

        embedvar = discord.Embed(title=f"Here are the random facts that will send at your given time "
                                       f"periods:",
                                 description="Page 1\n" + facts_display,
                                 color=0x00ff00)
        msg = await ctx.send(embed=embedvar)

        for emoji in ('⬅️', '➡️'):
            await msg.add_reaction(emoji)

    @bot.command(name='addtwitch', help='Adds your Twitch to the live notifs.', pass_context=True)
    async def add_twitch(self, ctx, twitch_name):
        with open('streamers.json', 'r') as file:
            streamers = json.loads(file.read())

        user_id = ctx.author.id
        streamers[user_id] = twitch_name

        with open('streamers.json', 'w') as file:
            file.write(json.dumps(streamers))
        await ctx.send(f"Added {twitch_name} for {ctx.author} to the Twitch notifications list.")

    # Old way of sending Twitch notifs using on_member_update **UNRELIABLE**
    # @commands.Cog.listener()
    # async def on_member_update(self, before, after):
    #     if after.guild.id == 593941391110045697:
    #         if before.activity == after.activity:
    #             return
    #
    #         role = get(after.guild.roles, id=800971369441394698)
    #         channel = get(after.guild.channels, id=740369106880036965)
    #
    #         async for message in channel.history(limit=200):
    #             if before.mention in message.content and "is now streaming" in message.content:
    #                 if isinstance(after.activity, Streaming):
    #                     return
    #
    #         if isinstance(after.activity, Streaming):
    #             await after.add_roles(role)
    #             stream_url = after.activity.url
    #             stream_url_split = stream_url.split(".")
    #             streaming_service = stream_url_split[1]
    #             streaming_service = streaming_service.capitalize()
    #             await channel.send(
    #                 f":red_circle: **LIVE**\n{before.mention} is now streaming on {streaming_service}!\n{stream_url}")
    #         elif isinstance(before.activity, Streaming):
    #             await after.remove_roles(role)
    #             async for message in channel.history(limit=200):
    #                 if before.mention in message.content and "is now streaming" in message.content:
    #                     await message.delete()
    #         else:
    #             return

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        ### Second part of list facts ###
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        guild_id = str(reaction.message.guild.id)
        facts_display = ""
        facts = []
        for fact_name, fact in guild_settings[guild_id]["random_facts"].items():
            item = f"{fact_name} - {fact}"
            facts.append(item)
        msg = reaction.message
        embed_title = msg.embeds[0].title
        embed_description = msg.embeds[0].description
        try:
            facts_page = embed_description[5]
            facts_page = int(facts_page)
        except ValueError:
            facts_page = 1
        if embed_title == "Here are the random facts that will send at your given time periods:" and user.id != 753479351139303484:
            await msg.remove_reaction(reaction, user)
            if str(reaction) == "⬅️" and facts_page >= 2:
                facts_page -= 1
            if str(reaction) == "➡️" and facts_page <= len(facts[::8]) - 1:
                facts_page += 1

        max_iteration = 8 * facts_page
        min_iteration = 8 * (facts_page - 1)
        fact_list = facts[min_iteration:max_iteration]
        for fact in fact_list:
            facts_display += f"{fact}\n\n"
        embedvar = discord.Embed(title=f"Here are the random facts that will send at your given time "
                                       f"periods:",
                                 description=f"Page {facts_page}\n" + facts_display,
                                 color=0x00ff00)
        await msg.edit(embed=embedvar)
        ### End of second part of list facts ###

    @bot.command(name='factsendtime', aliases=['factssendtime', 'facttime', 'factstime'], help='Set a time for a '
                                                                                               'random fact to send. '
                                                                                               'Hours is in 24h '
                                                                                               'cycles.',
                 pass_context=True)
    @has_permissions(kick_members=True)
    async def fact_send_time(self, ctx, hour=None, minute=None):
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        guild_id = str(ctx.guild.id)
        current_hour = guild_settings[guild_id]["random_facts_send_time"]["hour"]
        current_minute = guild_settings[guild_id]["random_facts_send_time"]["minute"]
        if hour is None:
            await ctx.send("Please include an hour.")
            return
        elif minute is None:
            await ctx.send("Please include a minute.")
            return
        elif hour == current_hour and minute == current_minute:
            await ctx.send(f"This time is currently set. Please enter a different hour or minute.")
            return
        else:
            guild_settings[guild_id]["random_facts_send_time"]["hour"] = hour
            guild_settings[guild_id]["random_facts_send_time"]["minute"] = minute
            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))
            await ctx.send(f"Changed fact send time to {hour}:{minute}.")

    @fact_send_time.error
    async def add_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the permissions to change the fact send time.")

    @bot.command(name='test')
    async def testing(self, ctx):
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        for guild_id in guild_settings:
            print(guild_id)

    async def func(self):
        await bot.wait_until_ready()
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        for guild_id in guild_settings:
            channel = bot.get_channel(guild_settings[guild_id]["random_facts_channel_id"])
            if guild_settings[guild_id]["random_facts"] is not None:
                random_facts = []
                for values in guild_settings[guild_id]["random_facts"].values():
                    random_fact = values.split("\n")
                    random_facts += random_fact
                try:
                    random_choice = random.choice(random_facts)
                except IndexError:
                    continue
                await channel.send(random_choice)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is ready.")
        print(f"Total servers: {len(bot.guilds)}")
        # print("Server names:")
        # for guild in bot.guilds:
        #    print(guild.name)

        await bot.change_presence(activity=discord.Game("$help WALL-E"))

        # Initializing scheduler
        scheduler = AsyncIOScheduler()
        if not os.path.isfile('guild_settings.json'):
            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps({}))

        if not os.path.isfile('mainbank.json'):
            with open('mainbank.json', 'w') as file:
                file.write(json.dumps({}))

        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())

        hour = 12
        minute = 0
        for guild in bot.guilds:
            guild_id = str(guild.id)
            try:
                hour = guild_settings[str(guild_id)]["random_facts_send_time"]["hour"]
                minute = guild_settings[str(guild_id)]["random_facts_send_time"]["minute"]
            except KeyError:
                hour = 12
                minute = 0
                continue

        # Sends "Your Message" at 12PM and 18PM (Local Time)
        scheduler.add_job(self.func, CronTrigger(hour=hour, minute=minute, second=0))

        # Starting the scheduler
        scheduler.start()

        # Returns true if Twitch user is live, else returns false
        def checkuser(user):
            try:
                userid = twitch.get_users(logins=[user])['data'][0]['id']
                url = TWITCH_STREAM_API_ENDPOINT_V5.format(userid)
                try:
                    req = requests.Session().get(url, headers=API_HEADERS)
                    jsondata = req.json()
                    if 'stream' in jsondata:
                        if jsondata['stream'] is not None:
                            return True
                        else:
                            return False
                except Exception as e:
                    print("Error checking user: ", e)
                    return False
            except IndexError:
                return False

        # Checks if Twitch users are live and sends a message if they are.
        @tasks.loop(seconds=10)
        async def live_notifs_loop():
            with open('streamers.json', 'r') as file:
                streamers = json.loads(file.read())
            if streamers is not None:
                guild1 = bot.get_guild(593941391110045697)
                channel = bot.get_channel(740369106880036965)
                role = get(guild1.roles, id=800971369441394698)
                for user_id, twitchname in streamers.items():
                    status = checkuser(twitchname)
                    user = bot.get_user(int(user_id))
                    if status is True:
                        async for message in channel.history(limit=200):
                            if str(user.mention) in message.content and "is now streaming" in message.content:
                                break
                            else:
                                async for member in guild1.fetch_members(limit=None):
                                    if member.id == int(user_id):
                                        await member.add_roles(role)
                                await channel.send(
                                    f":red_circle: **LIVE**\n{user.mention} is now streaming on Twitch!"
                                    f"\nhttps://www.twitch.tv/{twitchname}")
                                print(f"{user} started streaming. Sending a notification.")
                                break
                    else:
                        async for member in guild1.fetch_members(limit=None):
                            if member.id == int(user_id):
                                await member.remove_roles(role)
                        async for message in channel.history(limit=200):
                            if str(user.mention) in message.content and "is now streaming" in message.content:
                                await message.delete()

        live_notifs_loop.start()

    def update_react_message(self, guild_settings, guild_id):
        role_display = ""
        for emoji, role_name in guild_settings[guild_id]["roles"].items():
            role_display += f"{emoji} - {role_name}\n"
        if not role_display:
            role_display = "(No Roles Exist)"

        embedvar = discord.Embed(title="React to this message to get your roles!",
                                 description="Click the corresponding emoji to receive your "
                                             "role.\n" + role_display,
                                 color=0x00ff00)
        return embedvar

    @commands.Cog.listener()
    async def on_message(self, message):
        if "happy birthday" in message.content:
            await message.channel.send("Happy birthday!! :cake: :birthday: :tada:")

        if message.content.startswith('$jail'):
            await message.delete()

        # This sends or updates an embed message with a description of the roles.
        if message.content.startswith('insert role reaction message'):
            await message.delete()
            guild_id = str(message.guild.id)
            message_channel_id = message.channel.id
            with open('guild_settings.json', 'r') as file:
                guild_settings = json.loads(file.read())

            embedvar = self.update_react_message(guild_settings, guild_id)
            react_message = await message.channel.send(embed=embedvar)
            for emoji in guild_settings[guild_id]["roles"]:
                await react_message.add_reaction(emoji)

            guild_settings[guild_id]["react_message_id"] = react_message.id
            guild_settings[guild_id]["role_reaction_channel_id"] = message_channel_id

            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

        if message.content.startswith('insert member count'):
            await message.delete()
            guild_id = str(message.guild.id)
            with open('guild_settings.json', 'r') as file:
                guild_settings = json.loads(file.read())
            guild = bot.get_guild(message.guild.id)
            member_count = guild.member_count
            embedvar = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
            member_message = await message.channel.send(embed=embedvar)

            guild_settings[guild_id]["member_count_message_id"] = member_message.id
            guild_settings[guild_id]["member_count_channel_id"] = message.channel.id

            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

        if message.content.startswith('insert leave messages'):
            await message.delete()
            with open('guild_settings.json', 'r') as file:
                guild_settings = json.loads(file.read())

            guild_settings[str(message.guild.id)]["leave_message_channel_id"] = message.channel.id

            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

        if message.content.startswith('insert random facts'):
            await message.delete()
            with open('guild_settings.json', 'r') as file:
                guild_settings = json.loads(file.read())

            guild_settings[str(message.guild.id)]["random_facts_channel_id"] = message.channel.id

            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        if guild.id not in guild_settings:
            guild_settings[guild.id] = {"roles": {}, "random_facts": {}, "role_reaction_channel_id": None,
                                        "react_message_id": None, "member_count_channel_id": None,
                                        "member_count_message_id": None,
                                        "leave_message_channel_id": None, "leave_message":
                                            "quit on the 1 yard line (left the server).",
                                        "random_facts_channel_id": None,
                                        "random_facts_send_time": {"hour": 12, "minute": 0}}
            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

    # Assign the role when the role is added as a reaction to the message.
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())

        guild = bot.get_guild(payload.guild_id)
        guild_id = str(payload.guild_id)
        member = get(guild.members, id=payload.user_id)

        if payload.channel_id == guild_settings[guild_id]["role_reaction_channel_id"] and payload.message_id == \
                guild_settings[guild_id]["react_message_id"]:
            if str(payload.emoji) in guild_settings[guild_id]["roles"]:
                role = get(payload.member.guild.roles, name=guild_settings[guild_id]["roles"][str(payload.emoji)])
                if role is not None:
                    await payload.member.add_roles(role)
                    print(f"Assigned {member} to {role}.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())

        guild = bot.get_guild(payload.guild_id)
        guild_id = str(payload.guild_id)
        member = get(guild.members, id=payload.user_id)

        if payload.channel_id == guild_settings[guild_id]["role_reaction_channel_id"] and payload.message_id == \
                guild_settings[guild_id]["react_message_id"]:
            if str(payload.emoji) in guild_settings[guild_id]["roles"]:
                role = get(guild.roles, name=guild_settings[guild_id]["roles"][str(payload.emoji)])
                if role is not None:
                    await member.remove_roles(role)
                    print(f"Removed {role} from {member}.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        now = datetime.datetime.now()
        guild_id = str(member.guild.id)
        guild = bot.get_guild(member.guild.id)
        member_count = guild.member_count

        embedvar = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
        channel = bot.get_channel(guild_settings[guild_id]["member_count_channel_id"])
        if guild_settings[guild_id]["member_count_message_id"] is not None:
            msg = await channel.fetch_message(guild_settings[guild_id]["member_count_message_id"])
            await msg.edit(embed=embedvar)
        else:
            print("Member count message ID is invalid.")

        print(f"{member.guild} member count has been updated (+1) on {now}.\n Total Member Count: {member_count}")
        await member.create_dm()
        await member.dm_channel.send(f"Welcome to {member.guild}! Be sure to read the rules and have fun here!")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        now = datetime.datetime.now()
        guild_id = str(member.guild.id)
        guild = bot.get_guild(member.guild.id)
        member_count = guild.member_count

        embedvar = discord.Embed(title=f"Total member count: {member_count}", color=0x00ff00)
        member_count_channel = bot.get_channel(guild_settings[guild_id]["member_count_channel_id"])
        if guild_settings[guild_id]["member_count_message_id"] is not None:
            msg = await member_count_channel.fetch_message(guild_settings[guild_id]["member_count_message_id"])
            await msg.edit(embed=embedvar)

        print(f"{member.guild} member count has been updated (-1) on {now}.\n Total Member Count: {member_count}")
        if guild_settings[guild_id]["leave_message_channel_id"] is not None:
            leave_message_channel = bot.get_channel(guild_settings[guild_id]["leave_message_channel_id"])
            leave_message = guild_settings[guild_id]["leave_message"]
            await leave_message_channel.send(f"{member.mention} {leave_message}")

        with open('guild_settings.json', 'w') as file:
            file.write(json.dumps(guild_settings))

    @bot.command(name='leavemessage', aliases=['changeleavemessage'], help='Changes the message that comes after the '
                                                                           'member name that left the server.',
                 pass_context=True)
    @has_permissions(kick_members=True)
    async def change_leave_message(self, ctx, new_leave_message):
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        guild_id = str(ctx.guild.id)
        if guild_settings[guild_id]["leave_message"] == new_leave_message:
            await ctx.send("Please provide a different leave message.")
        else:
            guild_settings[guild_id]["leave_message"] = str(new_leave_message)
            await ctx.send(f"Leave message changed to: '{new_leave_message}'")
            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

    @change_leave_message.error
    async def add_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the permissions to change the leave message.")

    @bot.command(name='addrole', aliases=['addroles'], help='Adds role to role reaction message.', pass_context=True)
    @has_permissions(administrator=True)
    async def add_role(self, ctx, role_name, emoji):
        await ctx.message.delete()
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        guild_id = str(ctx.guild.id)
        if emoji in guild_settings[guild_id]["roles"]:
            msg = await ctx.send(f"This emoji is already assign to another role. Please use a different one.")
            await msg.delete(delay=10)
            return
        else:
            guild_settings[guild_id]["roles"][emoji] = role_name
            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

        embedvar = self.update_react_message(guild_settings, guild_id)
        channel = bot.get_channel(guild_settings[guild_id]["role_reaction_channel_id"])
        msg = await channel.fetch_message(guild_settings[guild_id]["react_message_id"])
        await msg.edit(embed=embedvar)
        await msg.add_reaction(emoji)

    @add_role.error
    async def add_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the permissions to change the roles.")

    @bot.command(name='removerole', help='Adds role to role reaction message.', pass_context=True)
    @has_permissions(administrator=True)
    async def remove_role(self, ctx, role_name):
        await ctx.message.delete()
        with open('guild_settings.json', 'r') as file:
            guild_settings = json.loads(file.read())
        guild_id = str(ctx.guild.id)
        guild = bot.get_guild(ctx.guild.id)

        emoji = None
        for key, value in guild_settings[guild_id]["roles"].items():
            if value == role_name:
                emoji = key

        if emoji not in guild_settings[guild_id]["roles"]:
            # await ctx.send(f"{emoji} is already in the role reaction message.")
            return
        else:
            guild_settings[guild_id]["roles"].pop(emoji)
            with open('guild_settings.json', 'w') as file:
                file.write(json.dumps(guild_settings))

        embedvar = self.update_react_message(guild_settings, guild_id)
        channel = bot.get_channel(guild_settings[guild_id]["role_reaction_channel_id"])
        msg = await channel.fetch_message(guild_settings[guild_id]["react_message_id"])
        await msg.edit(embed=embedvar)
        for member in guild.members:
            try:
                await msg.remove_reaction(emoji, member)
            except:
                pass

    @remove_role.error
    async def remove_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the permissions to change the roles.")

    @bot.command(name='happybirthday', help='Tags a member with a bday message.')
    async def bday(self, ctx, member: discord.Member):
        await ctx.message.delete()
        member = str(member)
        member_name_end = member.find("#")
        member_name = member[:member_name_end]
        member_id = member[member_name_end + 1:]
        user_id = get(bot.get_all_members(), name=member_name, discriminator=member_id).id
        await ctx.send(f"Happy birthday <@{user_id}>!! :cake: :birthday: :tada:")

    @bot.command(name='rolldice', help='Simulates rolling dice.')
    async def roll(self, ctx, number_of_dice: int, number_of_sides: int):
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.send(', '.join(dice))

    @bot.command(name='guess', help='Guess a random number in 10 tries.')
    async def guessnumber(self, ctx):
        await ctx.send(
            f"Hello {ctx.author.name}! I'm thinking of a number between 1 and 1000. You are given 10 tries to "
            f"find the number. Good luck!")
        number = random.randint(1, 1000)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()

        for guessesTaken in range(10):

            guess = int((await bot.wait_for('message', check=check)).content)

            if guess < number:
                await ctx.send("Your guess is too low.")
            elif guess > number:
                await ctx.send("Your guess is too high.")
            else:
                await ctx.send(f"GG! You correctly guessed the number in {guessesTaken + 1} guesses!")
                return
        else:
            await ctx.send(f"Sorry, you took too many guesses. The number I was thinking of was {number}")

    # @bot.command(name='bombs', aliases=['bomb'], help='For War Thunder game. Finds bombs from spreadsheet and returns '
    #                                                   'bombs required to destroy a base and bombs required to destroy '
    #                                                   'an airfield.')
    # async def bomb(self, ctx):
    #     american_bombs = 'Bomb Table!B19:Q29'
    #     german_bombs = 'Bomb Table!B33:Q39'
    #     russian_bombs = 'Bomb Table!B43:Q54'
    #     british_bombs = 'Bomb Table!B58:Q64'
    #     japanese_bombs = 'Bomb Table!B68:Q81'
    #     italian_bombs = 'Bomb Table!B85:Q91'
    #     chinese_bombs = 'Bomb Table!B95:Q115'
    #     french_bombs = 'Bomb Table!B119:Q125'
    #     swedish_bombs = 'Bomb Table!B128:Q138'
    #
    #     bomb_data = {"US": {}, "GERMAN": {}, "RUSSIA": {}, "BRITAIN": {}, "JAPAN": {}, "ITALY": {}, "CHINA": {},
    #                  "FRANCE": {}, "SWEDEN": {}}
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=american_bombs).execute()
    #     american_list = result.get('values', [])
    #     for items in american_list:
    #         bomb_data["US"][items[0]] = items[1:]
    #
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=german_bombs).execute()
    #     german_list = result.get('values', [])
    #     for items in german_list:
    #         bomb_data["GERMAN"][items[0]] = items[1:]
    #
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=russian_bombs).execute()
    #     russian_list = result.get('values', [])
    #     for items in russian_list:
    #         bomb_data["RUSSIA"][items[0]] = items[1:]
    #
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=british_bombs).execute()
    #     british_list = result.get('values', [])
    #     for items in british_list:
    #         bomb_data["BRITAIN"][items[0]] = items[1:]
    #
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=japanese_bombs).execute()
    #     japanese_list = result.get('values', [])
    #     for items in japanese_list:
    #         bomb_data["JAPAN"][items[0]] = items[1:]
    #
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=italian_bombs).execute()
    #     italian_list = result.get('values', [])
    #     for items in italian_list:
    #         bomb_data["ITALY"][items[0]] = items[1:]
    #
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=chinese_bombs).execute()
    #     chinese_list = result.get('values', [])
    #     for items in chinese_list:
    #         bomb_data["CHINA"][items[0]] = items[1:]
    #
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=french_bombs).execute()
    #     french_list = result.get('values', [])
    #     for items in french_list:
    #         bomb_data["FRANCE"][items[0]] = items[1:]
    #
    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=swedish_bombs).execute()
    #     swedish_list = result.get('values', [])
    #     for items in swedish_list:
    #         bomb_data["SWEDEN"][items[0]] = items[1:]
    #
    #     try:
    #         countries = []
    #         for country_number in bomb_data:
    #             countries.append(country_number)
    #
    #         countries_embed = self.embed_maker(countries)
    #
    #         embedvar = discord.Embed(title="Select a country to view bombs from:",
    #                                  description=countries_embed,
    #                                  color=0x00ff00)
    #         await ctx.send(embed=embedvar)
    #
    #         def check(message):
    #             return message.author == ctx.author and message.channel == ctx.channel
    #
    #         for x in range(5):
    #             country_number = (await bot.wait_for('message', check=check)).content
    #             try:
    #                 country_number = int(country_number)
    #             except ValueError:
    #                 await ctx.send("Please use a number.")
    #                 continue
    #             break
    #         else:
    #             await ctx.send("You didn't use a number. Goodbye.")
    #             return
    #
    #         if country_number == 1:
    #             country = countries[0]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[0]]:
    #                 bombs.append(bomb_)
    #
    #             american_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {country}:",
    #                                      description=american_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         elif country_number == 2:
    #             country = countries[1]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[1]]:
    #                 bombs.append(bomb_)
    #
    #             german_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {countries[1]}:",
    #                                      description=german_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         elif country_number == 3:
    #             country = countries[2]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[2]]:
    #                 bombs.append(bomb_)
    #
    #             russian_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {countries[2]}:",
    #                                      description=russian_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         elif country_number == 4:
    #             country = countries[3]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[3]]:
    #                 bombs.append(bomb_)
    #
    #             british_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {countries[3]}:",
    #                                      description=british_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         elif country_number == 5:
    #             country = countries[4]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[4]]:
    #                 bombs.append(bomb_)
    #
    #             japanese_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {countries[4]}:",
    #                                      description=japanese_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         elif country_number == 6:
    #             country = countries[5]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[5]]:
    #                 bombs.append(bomb_)
    #
    #             italian_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {countries[5]}:",
    #                                      description=italian_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         elif country_number == 7:
    #             country = countries[6]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[6]]:
    #                 bombs.append(bomb_)
    #
    #             chinese_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {countries[6]}:",
    #                                      description=chinese_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         elif country_number == 8:
    #             country = countries[7]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[7]]:
    #                 bombs.append(bomb_)
    #
    #             france_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {countries[7]}:",
    #                                      description=france_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         elif country_number == 9:
    #             country = countries[8]
    #             bombs = []
    #             for bomb_ in bomb_data[countries[8]]:
    #                 bombs.append(bomb_)
    #
    #             sweden_bombs_embed = self.embed_maker(bombs)
    #             embedvar = discord.Embed(title=f"Select a bomb from {countries[8]}:",
    #                                      description=sweden_bombs_embed,
    #                                      color=0x00ff00)
    #             await ctx.send(embed=embedvar)
    #         else:
    #             await ctx.send("Couldn't find that country's bombs.")
    #             return
    #
    #         for x in range(5):
    #             bomb_number = (await bot.wait_for('message', check=check)).content
    #             try:
    #                 bomb_number = int(bomb_number)
    #             except ValueError:
    #                 await ctx.send("Please use a number.")
    #                 continue
    #             break
    #         else:
    #             await ctx.send("You didn't use a number. Goodbye.")
    #             return
    #
    #         for x in range(len(bomb_data[country]) + 1):
    #             if bomb_number == x:
    #                 bomb_type = bombs[x - 1]
    #
    #         await ctx.send("Enter battle rating:")
    #         try:
    #             battle_rating = float((await bot.wait_for('message', check=check)).content)
    #         except ValueError:
    #             await ctx.send("Please use a decimal number.")
    #             return
    #
    #         await ctx.send("Is this a four base map? Enter 'YES' or 'NO'")
    #         try:
    #             four_base = str((await bot.wait_for('message', check=check)).content)
    #         except ValueError:
    #             await ctx.send("Please enter 'YES' or 'NO'.")
    #             return
    #
    #         base_bombs_list = bomb_data[country][bomb_type]
    #
    #         try:
    #             four_base = int(four_base)
    #         except ValueError:
    #             four_base = str(four_base)
    #             four_base = four_base.upper()
    #         try:
    #             if 1.0 <= battle_rating <= 2.0:
    #                 if four_base == "YES":
    #                     base_bombs_required = base_bombs_list[2]
    #                     airfield_bombs_required = int(base_bombs_required) * 5
    #                 else:
    #                     base_bombs_required = base_bombs_list[3]
    #                     airfield_bombs_required = int(base_bombs_required) * 5
    #             elif 2.3 <= battle_rating <= 3.3:
    #                 if four_base == "YES":
    #                     base_bombs_required = base_bombs_list[4]
    #                     airfield_bombs_required = int(base_bombs_required) * 6
    #                 else:
    #                     base_bombs_required = base_bombs_list[5]
    #                     airfield_bombs_required = int(base_bombs_required) * 6
    #             elif 3.7 <= battle_rating <= 4.7:
    #                 if four_base == "YES":
    #                     base_bombs_required = base_bombs_list[6]
    #                     airfield_bombs_required = int(base_bombs_required) * 8
    #                 else:
    #                     base_bombs_required = base_bombs_list[7]
    #                     airfield_bombs_required = int(base_bombs_required) * 8
    #             elif 5.0 <= battle_rating:
    #                 if four_base == "YES":
    #                     base_bombs_required = base_bombs_list[8]
    #                     airfield_bombs_required = int(base_bombs_required) * 15
    #                 else:
    #                     base_bombs_required = base_bombs_list[9]
    #                     airfield_bombs_required = int(base_bombs_required) * 15
    #             else:
    #                 await ctx.send("That battle rating doesn't exist.")
    #                 return
    #         except ValueError:
    #             await ctx.send(
    #                 "This bomb data hasn't been added to the spreadsheet yet. If you are requesting a 4 base "
    #                 "map, it may be too soon. Please refer to 3 base map data and multiply it by 2x for each "
    #                 "base to get approximate 4 base data.")
    #             return
    #
    #         await ctx.send(
    #             f"Bombs Required for Bases: {base_bombs_required} \nBombs Required for Airfield: "
    #             f"{airfield_bombs_required}")
    #
    #     except Exception as e:
    #         await ctx.send("User error, try again.")
    #         raise e


bot.remove_command("rolldice")
bot.remove_command("guess")
bot.remove_command("bombs")
bot.remove_command("happybirthday")
bot.remove_command("addrole")
bot.remove_command("removerole")
bot.remove_command("addfact")
bot.remove_command("removefact")
bot.remove_command("listfacts")
bot.remove_command("factsendtime")
bot.remove_command("leavemessage")
bot.remove_command("test")
bot.remove_command("jail")
bot.remove_command("addtwitch")
bot.add_cog(MetaBot(bot))

print("Server Running.")

bot.run(TOKEN)
