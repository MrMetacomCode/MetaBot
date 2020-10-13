import os
import random
# import logging

from discord.ext import commands

# logging.basicConfig(level=logging.DEBUG, filename='logs.txt')
# logger = logging.getLogger(__name__)
# logger.debug('test')


TOKEN = os.getenv('METABOT_DISCORD_TOKEN')

bot = commands.Bot(command_prefix='$')

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
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))


@bot.command(name='bombs', help='Find Bombs from Spreadsheet. If bomb name has spaces just smash it all together!')
async def bomb(ctx, country=None, bomb_type=None, battle_rating=None):

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
        if country not in bomb_data:
            await ctx.send("Country is invalid.")

        bomb_type = bomb_type.upper()
        bomb_type_list = []
        for country_ in bomb_data.values():
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

        base_bombs_list = bomb_data[country.upper()][bomb_type.upper()]

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


print("Server Running")

bot.run(TOKEN)
