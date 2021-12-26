# practice.py
import re

import discord
from discord.ext import commands
import random
import os
import asyncio


# A cog for nonessential commands and triggers

class MiscCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def flip(self, ctx):
        if random.uniform(0,1) <= 0.2:
            await ctx.send('Coin landed on the edge\n*wait what??*')
        else:
            flip = random.choice(['heads', 'tails'])
            await ctx.send(flip)

    @commands.command(aliases=['dice'])
    async def roll(self, ctx, number_of_dice: int, number_of_sides: int):
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

    @commands.command(aliases=['sz'])
    async def szeth(self,ctx):
        filepath = './misc/emotes/szeth.png'
        await ctx.send(file=discord.File(filepath))
        #await ctx.send('<:szeth:667773296896507919>')


    @commands.command()
    async def emote(self,ctx,query):

        if query == 'list':
            all_emotes = os.listdir('./misc/emotes/')
            final = '`!emote namehere`\n'
            for item in all_emotes:
                final = final + item[:-4] + '\n'
            await ctx.send(final)
            return

        await ctx.message.delete()

        filepath = './misc/emotes/'+query+'.png'
        await ctx.send(file=discord.File(filepath))



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        

        if message.content.lower() =='ping':
            await message.channel.send('Pong!')


        if re.match('(hi|hello),? m-?bot.*', message.content.lower()):
            await message.channel.send('Welcome again {}!'.format(message.author.mention))


        if re.match('(bye|good-?bye),? m-?bot.*', message.content.lower()):
            await message.channel.send('Good night {}'.format(message.author.mention))


        if re.match('(thanks|thank you|thx),? m-?bot.*', message.content.lower()):
            url = 'https://i.imgur.com/XZsOmxg.png?2'
            embed=discord.Embed()
            embed.set_image(url=url)
            await message.channel.send(content='Aww... \nHere\'s a mushroom for you too <3',embed=embed)


        if 'space' in message.content.lower():
            quotes = [
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
            response = random.choice(quotes)
            await message.channel.send(response)


        if 'quote' in message.content.lower():
            quotes = [
                "What's the most important step a man can take? The next one.",
                "What's the most important ~~step~~ drink a man can take? The next one.",
                "What's the most important ~~step~~ puzzle a man can ~~take~~ solve? The next one.",
                "What's the most important puzzle a man can solve? The next one.",
                'There is always another secret.',
                'There is always another puzzle.',
                "Life before Death. Strength before Weakness. Journey before Destination.",
                "Life before Death. Strength before Weakness. Journey before Pancakes.",
                "Elend: I kind of lost track of time.\nBreeze: For two hours?\nElend: There were ~~books~~puzzles involved...",
                "I've always been very confident in my immaturity.",
                "Puzzles are hard. But I'll see what I can do.",
                "Sometimes our conversations remind me of a broken sword. Sharp as hell... but lacking a point.",
                "I try to avoid having thoughts. They lead to other thoughts, and—if you're not careful—those lead to actions. Actions make you tired. I have this on rather good authority from someone who once read it in a book.",
                "Not having ice cream is the culmination of all disasters.",
                "*Am I alive?*",
                "I'm convinced that responsibility is some kind of psychological disease.",
                "Power is an illusion of perception.",
                "I’m so storming pure I practically belch rainbows.",
                "Mocking a woman is like drinking too much wine. It may be fun for a short time, but the hangover is hell.",
                "Inappropriate... like dividing by zero?",
                "Women are fickle, but men are fools.",
                "I am not enthused by my first experiments in self-determination.",
                "Mushroom locating AI. With supplementary espionage additions. At your service."
            ]
            response = random.choice(quotes)
            await message.channel.send(response)


        if message.content.lower().startswith('other trigger words'):
            url = 'https://i.imgur.com/XZsOmxg.png?2'
            embed=discord.Embed()
            embed.set_image(url=url)
            await message.channel.send('Did you really just try that? <:szeth:667773296896507919> No. Not what I meant. '\
            'But Mbot is still impressed you found this. Here\'s a mushroom for your efforts.',embed=embed)





def setup(bot):
    bot.add_cog(MiscCog(bot))
