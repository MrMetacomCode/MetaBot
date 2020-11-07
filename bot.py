import os
import json
import random
import discord
from discord import Intents
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

# import logging

# logging.basicConfig(level=logging.DEBUG, filename='logs.txt')
# logger = logging.getLogger(__name__)
# logger.debug('test')


TOKEN = os.getenv('METABOT_DISCORD_TOKEN')

intents = Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)


# Beginning of economy system.
class Metacash(commands.Cog):
    """Some stuff."""
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

        with open("mainbank.json", "w") as bank:
            json.dump(users, bank)

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
                                                                              "money.")
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
        earnings = random.randrange(100)
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

    async def func(self):
        await bot.wait_until_ready()
        channel = bot.get_channel(593941391110045699)
        random_messages = ("McDonald’s once made bubblegum-flavored broccoli.",
                           "Some fungi create zombies, then control their minds.",
                           "The first oranges weren’t orange. They were green.",
                           "The Earl of Sandwich, John Montagu, who lived in the 1700s, reportedly invented the sandwich "
                           "so he wouldn’t have to leave his gambling table to eat.",
                           "Canadians say “sorry” so much that a law was passed in 2009 declaring that an apology can’t "
                           "be used as evidence of admission to guilt.",
                           "One habit of intelligent humans is being easily annoyed by people around them, but saying "
                           "nothing in order to avoid a meaningless argument.",
                           "Nintendo trademarked the phrase “It’s on like Donkey Kong” in 2010.",
                           "There were two AI chatbots created by Facebook to talk to each other, but they were shut down "
                           "after they started communicating in a language they made for themselves.",
                           "Daniel Radcliffe was allergic to his Harry Potter glasses.",
                           "Hershey’s Kisses are named that after the kissing sound the deposited chocolate makes as it "
                           "falls from the machine on the conveyor belt.",
                           "The Buddha commonly depicted in statues and pictures is a different person entirely. The real "
                           "Buddha was actually incredibly skinny because of self-deprivation.",
                           "There is a company in Japan that has schools that teach you how to be funny. The first one "
                           "opened in 1982. About 1,000 students take the course each year.",
                           "There are more Lego minifigures than there are people on Earth.",
                           "Elvis was originally blonde. He started coloring his hair black for an edgier look. "
                           "Sometimes, he would touch it up himself using shoe polish.",
                           "The voice actor of SpongeBob and the voice actor of Karen, Plankton’s computer wife, "
                           "have been married since 1995.",
                           "The smell of freshly cut grass is actually the scent that plants release when in distress.",
                           "During pregnancy woman’s brain shrinks and it takes up to six months to regain its original "
                           "size.",
                           "Human saliva contains a painkiller called opiorphin that is six times more powerful than "
                           "morphine.",
                           "Hippopotamus milk is pink.",
                           "On Venus, it snows metal. Two types have been discovered so far: galena and bismuthinite.",
                           "Sound waves can make objects levitate.",
                           "People are more likely to make good decisions when they need to urinate.",
                           "Some snakes survive for two years without a meal.",
                           "A strawberry isn’t an actual berry, but a banana is.",
                           "A jellyfish is approximately 95% water.",
                           "The brain treats rejection like physical pain.",
                           "Cotton candy was invented by a dentist.",
                           "Nazi human experimentation was a series of medical experiments on large numbers of prisoners, "
                           "including children, by Nazi Germany in its concentration camps in the early to mid 1940s, "
                           "during World War II and the Holocaust.",
                           "<@442853051791835147> is mega sus.",
                           "<@668335245610844161> still trying to land?",
                           "<@762120478361518122> still not giving up cyan?",
                           "<@472846171627454464> are you going to stop coding me yet?",
                           "Where is my creator?")
        random_messages = random.choice(random_messages)
        await channel.send(random_messages)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is ready.")

        # Initializing scheduler
        scheduler = AsyncIOScheduler()

        # Sends "Your Message" at 12PM and 18PM (Local Time)
        scheduler.add_job(self.func, CronTrigger(hour="0, 12", minute="0", second="0"))

        # Starting the scheduler
        scheduler.start()

    bomb_data = {'US': {'AN-M30A1': [13, 17, 21, 25],
                        'AN-M57': [6, 8, 10, 12],
                        'LDGPMK.81': [5, 7, 9, 10],
                        'AN-M64A1': [4, 5, 6, 7],
                        'LDGPMK.82': [4, 5, 6, 7],
                        'M117CONE45': [2, 3, 3, 4],
                        'AN-M65A1': [2, 2, 3, 3],
                        'AN-M65A1FINM129': [2, 2, 3, 3],
                        'LDGPMK.83': [1, 2, 2, 3],
                        'AN-M66A2': [1, 1, 1, 2],
                        'LDGPMK.84': [1, 1, 1, 1],
                        },

                 'GERMAN': {'SD10C': [24, 32, 40, 47],
                            'SC50JA': [11, 15, 20, 24],
                            'SC250JA': [3, 5, 6, 7],
                            'SC500K': [2, 2, 3, 3],
                            'SC1000L2': [1, 1, 1, 1],
                            'PC1400X': [1, 2, 2, 3],
                            'SC1800B': [1, 1, 1, 1],
                            },

                 'RUSSIA': {'AO-25-M1': [17, 22, 28, 34],
                            'FAB-50': [13, 17, 21, 25],
                            'FAB-100': [8, 10, 13, 15],
                            'OFAB-100': [9, 11, 17, 22],
                            'FAB-250-M43': [4, 6, 7, 8],
                            'OFAB-250-270': [4, 5, 6, 7],
                            'FAB-500': [2, 3, 3, 3],
                            'FAB-500M54': [2, 3, 3, 4],
                            'FAB-1000': [1, 1, 2, 2],
                            'FAB-1500M46': [1, 1, 1, 1],
                            'FAB-3000M46': [1, 1, 1, 1],
                            'FAB-5000': [1, 1, 1, 1],
                            },

                 'BRITAIN': {'G.P.250LBMK.IV': [10, 13, 16, 20],
                             'G.P.500LBMK.IV': [6, 7, 9, 11],
                             'H.E.M.C.500LBSMK.II': [0, 0, 0, 0],
                             'G.P.1000LBMK.I': [2, 3, 3, 4],
                             'M.C.1000LBMK.I': [2, 2, 2, 3],
                             'H.C.4000LBMK.II': [1, 1, 1, 1],
                             },

                 'JAPAN': {'ARMYTYPE94GPHE50KG': [13, 17, 21, 25],
                           'NAVYTYPE97NO.6GROUNDBOMB': [12, 17, 21, 25],
                           'ARMYTYPE94GPHE100KG': [7, 9, 11, 14],
                           'NAVYTYPE98NO.25': [4, 6, 7, 8],
                           'ARMYTYPE92GPHE250KG': [4, 5, 7, 8],
                           'NAVYTYPENO.25MOD.2': [4, 5, 7, 8],
                           'JM117750LBSBOMB': [2, 3, 3, 4],
                           'NUMBERTYPE250MODEL1GP(SAP)': [6, 7, 9, 11],
                           'NAVYTYPENO.50MOD.2': [2, 3, 4, 4],
                           'ARMYTYPE92GPHE500KG': [2, 3, 3, 4],
                           'NAVYTYPE99NO.80APBOMB': [0, 0, 0, 0],
                           'NAVYTYPENUMBER80MOD.1': [1, 1, 2, 2],
                           },
                 'ITALY': {'GP50VERTICAL': [12, 15, 20, 24],
                           'GP50HORIZONTAL': [10, 14, 17, 20],
                           'SAP100BOMB': [11, 15, 18, 23],
                           'GP100': [6, 8, 10, 12],
                           'GP250': [4, 5, 6, 7],
                           'GP500': [2, 3, 3, 4],
                           'GP800': [1, 2, 2, 2],
                           },
                 'CHINA': {'AN-M30A1': [13, 17, 21, 25],
                           'FAB-50': [13, 17, 21, 25],
                           'SC50JA': [12, 15, 20, 24],
                           'AN-M57': [6, 8, 10, 12],
                           'SAP100': [11, 15, 18, 23],
                           '100KGNO.1': [7, 9, 11, 13],
                           'FAB-100': [8, 10, 15, 20],
                           '200KGNO.1': [4, 5, 7, 8],
                           'FAB-250-M43': [4, 6, 7, 8],
                           'NAVYTYPENO.25MOD.2': [4, 5, 7, 8],
                           'AN-M64A1': [4, 5, 6, 7],
                           'SC250JA': [3, 5, 6, 7],
                           'GP250': [4, 5, 6, 7],
                           'AN-M65A1': [2, 2, 3, 3],
                           'FAB-500': [2, 3, 3, 3],
                           'NAVYTYPENO.50MOD.2': [2, 3, 4, 4],
                           'NAVYTYPENUMBER80MOD.1': [1, 1, 2, 2],
                           'AN-M66A2': [1, 1, 1, 2],
                           'FAB-1000': [1, 1, 2, 2],
                           'FAB-1500M46': [1, 1, 1, 1],
                           'FAB-3000M46': [1, 1, 1, 1],
                           },
                 'FRANCE': {'TYPE61C': [13, 17, 21, 25],
                            'DT-2': [15, 19, 23, 27],
                            '50KGG.A.MMN.50': [10, 14, 18, 23],
                            '100KGNO.1': [7, 9, 11, 13],
                            '200KGNO.1': [4, 5, 7, 8],
                            '500KGNO.2': [2, 2, 2, 3],
                            'SAMP250': [0, 0, 0, 8],
                            },
                 'SWEDEN': {'50KGM/42': [0, 0, 0, 0],
                            '50KGM/37A': [11, 15, 18, 23],
                            '50KGM.47': [0, 0, 0, 0],
                            '50KGMODEL1938': [13, 17, 21, 25],
                            '100KGMODEL1938': [7, 9, 11, 14],
                            '120KGM/61': [10, 13, 16, 20],
                            '120KGM/40': [4, 5, 7, 8],
                            '120KGM/50': [4, 5, 6, 7],
                            '500KGM/41': [3, 4, 5, 6],
                            '500KGM/56': [2, 3, 3, 4],
                            '600KGM/50': [1, 1, 2, 3],
                            }
                 }

    @bot.command(name='rolldice', help='Simulates rolling dice.')
    async def roll(self, ctx, number_of_dice: int, number_of_sides: int):
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.send(', '.join(dice))

    # Random command returns a random fact. @bot.command(name='random', help='Returns a random, interesting fact.')
    # async def randomfact(ctx): random_messages = ("McDonald’s once made bubblegum-flavored broccoli.", "Some fungi
    # create zombies, then control their minds.", "The first oranges weren’t orange. They were green.", "The Earl of
    # Sandwich, John Montagu, who lived in the 1700s, reportedly invented the sandwich " "so he wouldn’t have to
    # leave his gambling table to eat.", "Canadians say “sorry” so much that a law was passed in 2009 declaring that
    # an apology can’t " "be used as evidence of admission to guilt.", "One habit of intelligent humans is being
    # easily annoyed by people around them, but saying " "nothing in order to avoid a meaningless argument.",
    # "Nintendo trademarked the phrase “It’s on like Donkey Kong” in 2010.", "There were two AI chatbots created by
    # Facebook to talk to each other, but they were shut " "down after they started communicating in a language they
    # made for themselves.", "Daniel Radcliffe was allergic to his Harry Potter glasses.", "Hershey’s Kisses are
    # named that after the kissing sound the deposited chocolate makes as it " "falls from the machine on the
    # conveyor belt.", "The Buddha commonly depicted in statues and pictures is a different person entirely. The "
    # "real Buddha was actually incredibly skinny because of self-deprivation.", "There is a company in Japan that
    # has schools that teach you how to be funny. The first one " "opened in 1982. About 1,000 students take the
    # course each year.", "There are more Lego minifigures than there are people on Earth.", "Elvis was originally
    # blonde. He started coloring his hair black for an edgier look. " "Sometimes, he would touch it up himself using
    # shoe polish.", "The voice actor of SpongeBob and the voice actor of Karen, Plankton’s computer wife,
    # " "have been married since 1995.", "The smell of freshly cut grass is actually the scent that plants release
    # when in distress." "During pregnancy woman’s brain shrinks and it takes up to six months to regain its original
    # " "size.", "Human saliva contains a painkiller called opiorphin that is six times more powerful than "
    # "morphine.", "Hippopotamus milk is pink.", "On Venus, it snows metal. Two types have been discovered so far:
    # galena and bismuthinite.", "Sound waves can make objects levitate.", "People are more likely to make good
    # decisions when they need to urinate.", "Some snakes survive for two years without a meal.", "A strawberry isn’t
    # an actual berry, but a banana is.", "A jellyfish is approximately 95% water.", "The brain treats rejection like
    # physical pain.", "Cotton candy was invented by a dentist.", "Nazi human experimentation was a series of medical
    # experiments on large numbers of " "prisoners, including children, by Nazi Germany in its concentration camps in
    # the early to " "mid 1940s, during World War II and the Holocaust.") random_messages = random.choice(
    # random_messages) await ctx.send(random_messages)

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
            await ctx.send(f"Nope, sorry, you took too many guesses. The number I was thinking of was {number}")

    @bot.command(name='bombs', help='Finds bombs for WarThunder to destroy targets. If bomb name has spaces just '
                                    'smash it all together!')
    async def bomb(self, ctx, country=None, bomb_type=None, battle_rating=None):
        try:
            if country is None:
                await ctx.send("Country is missing.")

            if bomb_type is None:
                await ctx.send("Bomb type is missing.")

            if battle_rating is None:
                await ctx.send("Battle rating is missing.")
                return

            country = country.upper()
            if country in ['AMERICA', 'AMERICAN', 'USA', 'United_States_of_America']:
                country = 'US'
            elif country in ['DE', 'GERMANY', 'NAZI', 'FATHERLAND']:
                country = 'GERMAN'
            elif country in ['RUSSIA', 'RUSSIAN', 'SOVIET', 'USSR', 'RU']:
                country = 'RUSSIA'
            elif country in ['BRITISH', 'UK']:
                country = 'BRITAIN'
            elif country in ['JP', 'JAPANESE']:
                country = 'JAPAN'
            elif country in ['ITALIAN', 'IT']:
                country = 'ITALY'
            elif country in ['CHINESE', 'CN']:
                country = 'CHINA'
            elif country in ['FRENCH', 'FR']:
                country = 'FRANCE'
            elif country in ['SWEDISH']:
                country = 'SWEDEN'
            if country not in self.bomb_data:
                await ctx.send("Country is invalid.")

            bomb_type = bomb_type.upper()
            bomb_type_list = []
            for country_ in self.bomb_data.values():
                for bomb_type_ in country_:
                    bomb_type_list.append(bomb_type_)
            if bomb_type not in bomb_type_list:
                await ctx.send("Bomb type is invalid.")
                return

            try:
                battle_rating = float(battle_rating)
            except ValueError:
                await ctx.send("Battle rating is invalid.")
                return

            base_bombs_list = self.bomb_data[country.upper()][bomb_type.upper()]

            if 1.0 <= battle_rating <= 2.0:
                base_bombs_required = base_bombs_list[0]
                airfield_bombs_required = base_bombs_required * 5
            elif 2.3 <= battle_rating <= 3.3:
                base_bombs_required = base_bombs_list[1]
                airfield_bombs_required = base_bombs_required * 6
            elif 3.7 <= battle_rating <= 4.7:
                base_bombs_required = base_bombs_list[2]
                airfield_bombs_required = base_bombs_required * 8
            elif 5.0 <= battle_rating:
                base_bombs_required = base_bombs_list[3]
                airfield_bombs_required = base_bombs_required * 15
            else:
                return

            if base_bombs_required == 0:
                await ctx.send("This bomb data is unavailable.")
            else:
                await ctx.send(
                    f"Bombs Required for Bases: {base_bombs_required} \nBombs Required for Airfield: "
                    f"{airfield_bombs_required}")

        except Exception as e:
            await ctx.send("User error, try again.")
            raise e


bot.remove_command("rolldice")
bot.remove_command("guess")
bot.remove_command("bombs")
bot.add_cog(MetaBot(bot))

print("Server Running.")

bot.run(TOKEN)
