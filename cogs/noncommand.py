# noncommand.py
import discord
from discord.ext import commands
import random


# A cog with some simple non command responses

class NoncommandCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        

        if message.content.lower() =='ping':
            await message.channel.send('Pong!')


        if message.content.lower().startswith('hello mbot') or message.content.lower().startswith('hi mbot'):
            await message.channel.send('Welcome again {}!'.format(message.author.mention))


        if message.content.lower().startswith('bye mbot') or message.content.lower().startswith('goodbye mbot'):
            await message.channel.send('Good night {}'.format(message.author.mention))


        if message.content.lower().startswith('thanks mbot') or message.content.lower().startswith('thank you mbot'):
            url = 'https://i.imgur.com/XZsOmxg.png?2'
            embed=discord.Embed()
            embed.set_image(url=url)
            await message.channel.send(content='Aww... \nHere\'s a mushroom for you too <3',embed=embed)


        if 'space' in message.content.lower():
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
            response = random.choice(space_quotes)
            await message.channel.send(response)


        if message.content.lower().startswith('other trigger words'):
            url = 'https://i.imgur.com/XZsOmxg.png?2'
            embed=discord.Embed()
            embed.set_image(url=url)
            await message.channel.send('Did you really just try that? <:szeth:667773296896507919> No. Not what I meant. '\
            'But Mbot is still impressed you found this. Here\'s a mushroom for your efforts.',embed=embed)




def setup(bot):
    bot.add_cog(NoncommandCog(bot))


