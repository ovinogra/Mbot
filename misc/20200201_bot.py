# bot.py
import os
import discord
import asyncio
import random
import urllib.request
import re
import numpy
from dotenv import load_dotenv
from discord.ext import commands



load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')



bot = commands.Bot(command_prefix='!')
bot.remove_command('help')


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


# General #################################################################

@bot.command(name='help')
async def help(ctx):
    response = \
    '```md\n'\
    '< Mbot Commands v0.1 > \n'\
    '* !nexus         -> /* PLAYER ROLE * Link to current nexus sheet\n'\
    '* !folder        -> /* PLAYER ROLE * Link to current hunt drive folder\n'\
    '* !login         -> /* PLAYER ROLE * Current hunt login info\n'\
    '* !nut query #   -> Call nutrimatic query for 15 (default) or # (optional) answers\n'\
    '* !flip          -> Toss a coin! (To your Witcher) Heads or tails?\n'\
    '* !dice N S      -> Roll N dice each of S sides\n'\
    '* !sz            -> Szeth...\n'\
    '* Other trigger words -> Only a few so far, but I\'m not telling you what they are\n'\
    '\n'\
    '/* PLAYER ROLE *  : Available only to the role of the current hunt\n'\
    'Should NOT be invoked in general channels\n'\
    '\n'\
    '< Coming eventually >\n'\
    '* !nuthelp       -> Nutrimatic query syntax cheat sheet\n'\
    '* !qq query N    -> Call quipqiup query for N answers\n'\
    '\n'\
    '> Created and hosted by @Moonrise\n'\
    '```'
    
    await ctx.send(response)


@bot.command(name='sz')
async def szeth(ctx):
    await ctx.send('<:szeth:667773296896507919>')





# Hunt Specific Commands #################################################################
huntrole = 'pam player'





@bot.command(name='folder')
@commands.has_role(huntrole)
async def folder(ctx):
    link = 'removed'
    embed = discord.Embed(
        title='Link to the current Google drive folder',
        url=link,
        colour=discord.Colour.magenta()
    )
    await ctx.send(embed=embed)


@bot.command(name='nexus')
@commands.has_role(huntrole)
async def nexus(ctx):
    link = 'removed'
    embed = discord.Embed(
        title='Link to the current Nexus sheet',
        url=link,
        colour=discord.Colour.magenta()
    )
    await ctx.send(embed=embed)


@bot.command(name='login')
@commands.has_role(huntrole)
async def login(ctx):
    await ctx.send(
        'Website:  https://www.puzzlesaremagic.com/\n'\
        'Username: 17thshardteam\n'\
        'Password: ryshadium'
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send('You do not have the role for the current puzzlehunt')


# The Useful Commands/Tools #################################################################

@bot.command()
async def nut(ctx, *, query):
    number = 15
    query = query[:]
    if query[-1].isdigit() == True and query[-2].isspace() == True:
        number = int(query[-1:])
        query = query[0:-2]
    elif query[-2:].isdigit() == True and query[-3].isspace() == True:
        number = int(query[-2:])
        query = query[0:-3]
    elif query[-3:].isdigit() == True and query[-4].isspace() == True:
        number = int(query[-3:])
        query = query[0:-4]
    if number > 40:
        await ctx.send('That is too many solutions for my mushroom powered processing. Choose something smaller.')
    else: 
        query_initial = query[:]
        query = query.replace('&','%26')
        query = query.replace('+','%2B')
        query = query.replace('#','%23')
        query = query.replace(' ','+')
        url = 'https://nutrimatic.org/?q='+query+'&go=Go'
        text = urllib.request.urlopen(url).read()
        text1 = text.decode()
        if text1.find('No results found, sorry') != -1:
            final = 'Error: No results found at all :('
        elif text1.find('error: can\'t parse') != -1:
            final = 'Error: I cannot parse that :('
        else:
            posA = [m.start() for m in re.finditer('<span',text1)]
            posB = [m.start() for m in re.finditer('</span',text1)]
            final1 = []
            if len(posA) < number:
                number = len(posA)
                if text1.find('Computation') != -1:
                    final1 = 'Error: Computation limit reached'
                if text1.find('No more results found') != -1:
                    final1 = 'Error: No more results found here'
            listnew = []
            sizenew = []
            final = []
            for n in range(0,number):
                word = text1[posA[n]+36:posB[n]]
                size = text1[posA[n]+23:posA[n]+32]
                listnew.append(word)
                sizenew.append(size)
            sizenew = [round(float(sizenew[n]),3) for n in range(0,len(sizenew))]
            sizenew = [round(float(sizenew[n]),3) for n in range(0,len(sizenew))]
            for n in range(0,number):
                final.append(listnew[n]+"...................."+str(sizenew[n]))
            final = '\n'.join(final)
            if len(final1) != 0:
                final = final+'\n'+final1
        embed = discord.Embed(
            title='Your nutrimatic link',
            url=url,
            description=final,
            author=query,
            colour=discord.Colour.magenta()
        )
        embed.set_footer(text='Query: '+query_initial)
        await ctx.send(embed=embed)


# Practice commands #################################################################

@bot.command(name='flip')
async def flip(ctx):
    flip = random.choice(['heads', 'tails'])
    await ctx.send(flip)

# The practice command that blew up into instanity
@bot.command(name='dice')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    if number_of_dice > 10:
        await ctx.send('Why do you need so many dice rolls...')
    elif number_of_dice == 0:
        await ctx.send('This is how I know you do not need me. Doomslug was ever the better companion.')
    elif number_of_dice < 0 and number_of_dice >= -20000:
        await ctx.send('*Mbot gives an exasperated sigh*')
    elif number_of_dice <-20000:
        await ctx.send('Do you think I was Made in Abyss? You do know that those who go there, rarely come back...')
    if number_of_sides > 20:
        await ctx.send('What kind of dice do you have??? My friend, those are called marbles. Did you lose them?')
    elif number_of_sides < 4 and number_of_sides > 0:
        await ctx.send('Do you live in Flatland?')
    elif number_of_sides == 2:
        await ctx.send('You could just flip a coin.')
    elif number_of_sides == 0:
        await ctx.send('I am not sure you actually need my help. Maybe I can fly you to the nearest therapist...')
    elif number_of_sides < 0 and number_of_sides >= -9:
        await ctx.send('What are we in, inverse space? I wonder, would that be the place with all the watching eyes...')
    elif number_of_sides < -10 and number_of_sides >= -25:
        await ctx.send('Heh, going deeper I see.')
    elif number_of_sides < -25 and number_of_sides >= -33:
        await ctx.send('I recommend stopping that now.')
    elif number_of_sides < -33 and number_of_sides >= -55:
        await ctx.send('<:szeth:667773296896507919>')
    elif number_of_sides < -55 and number_of_sides >= -74:
        await ctx.send('Why are you even testing this? Are you a quality analyst? (Please don\'t be too harsh on my code when you (maybe eventually) see it: https://xkcd.com/1513/ )')
    elif number_of_sides < -74 and number_of_sides >= -103:
        await ctx.send('You broke me. Happy now?')
    elif number_of_sides < -103:
        await ctx.send('Okay, I refuse to go farther... The eyes are watching.')
    if number_of_dice <= 10 and number_of_dice > 0 and number_of_sides <= 20 and number_of_sides >= 4:
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.send(', '.join(dice))


# No command responses #################################################################

@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower() =='ping':
        await message.channel.send('Pong!')

# added lower bit
@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower().startswith('hello mbot'):
        await message.channel.send('Welcome again {}!'.format(message.author.mention))


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower().startswith('bye mbot'):
        await message.channel.send('Good night {}'.format(message.author.mention))


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower().startswith('thanks mbot'):
        url = 'https://i.imgur.com/XZsOmxg.png?2'
        embed=discord.Embed()
        embed.set_image(url=url)
        await message.channel.send(content='Aww... \nHere\'s a mushroom for you too <3',embed=embed)


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    space_quotes = [
        "Space going to space can't wait.",
        'Did someone say space? Are we going to space?',
        'SPAAACCCCCE!',
        "Ohmygodohmygodohmygod! I'm in space!",
        "Gotta go to space. Yeah. Gotta go to space.",
        "Space. Space. Space. Space. Comets. Stars. Galaxies. Orion.",
        "Space space space. Going. Going there. Okay. I love you, space.",
        "Orbit. Space orbit. In my spacesuit.",
        "Space going to space can't wait.",
        "What's your favorite thing about space? Mine is space.",
        "*Spaaaaace...*",
        "Space. Space. Gonna go to space.",
        "That\'s it. I'm going to space.",
        "Hey lady. Lady. I'm the best. I'm the best at space.",
        "Are we in space yet? What's the hold-up? Gotta go to space. Gotta go to SPACE."
    ]
    if 'space' in message.content.lower():
        response = random.choice(space_quotes)
        await message.channel.send(response)



@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower().startswith('other trigger words'):
        url = 'https://i.imgur.com/XZsOmxg.png?2'
        embed=discord.Embed()
        embed.set_image(url=url)
        await message.channel.send('Did you really just try that? <:szeth:667773296896507919> No. Not what I meant. '\
        'But Mbot is still impressed you found this. Here\'s a mushroom for your efforts.',embed=embed)






bot.run(TOKEN)

