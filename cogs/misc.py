# practice.py
import discord
from discord.ext import commands
import random
import os


# A cog with some simple practice commands

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
        await ctx.send('<:szeth:667773296896507919>')


    @commands.command()
    @commands.is_owner()
    async def emote(self,ctx,query):

        await ctx.message.delete()

        if query == 'list':
            all_emotes = os.listdir('./misc/emotes/')
            final = ''
            for item in all_emotes:
                final = final + item + '\n'
            await ctx.send(final)
            return

        
        filepath = './misc/emotes/'+query+'.png'
        await ctx.send(file=discord.File(filepath))




def setup(bot):
    bot.add_cog(MiscCog(bot))
