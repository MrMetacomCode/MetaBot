import os
import random
from discord.ext import commands

TOKEN = os.getenv('METABOT_DISCORD_TOKEN')

bot = commands.Bot(command_prefix='$')


@bot.command(name='random', help='Returns a random, interesting fact.')
async def randomfact(ctx):
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
                       "The smell of freshly cut grass is actually the scent that plants release when in distress."
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
                       "during World War II and the Holocaust.")
    random_messages = random.choice(random_messages)
    await ctx.send(random_messages)


print("Server running.")
bot.run(TOKEN)
