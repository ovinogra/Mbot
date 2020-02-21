# bot.py
import os
import discord
import asyncio
import random
import numpy
from dotenv import load_dotenv
from discord.ext import commands



load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')



bot = commands.Bot(command_prefix='!',case_insensitive=True)
bot.remove_command('help')
MoonID = '<@416656299661459458>'

initial_extensions = ['cogs.practice',
                      'cogs.toolbox',
                      'cogs.noncommand',
                      'cogs.hunt',
                      'cogs.debris']

#initial_extensions = ['cogs.debris']


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    for extension in initial_extensions:
        bot.load_extension(extension)


# General #################################################################

@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title='Commands',
        colour=discord.Colour.blurple()
    )
    embed.add_field(name='Tools',value='**!nut** *query N*: Call nutrimatic *query* for *N* answers (n, nutr, nutrimatic)\n'\
        '**!sub** *query*: Call substitution cryptogram *query* (s, substitution)\n'\
        '**!cc** *query key*: Call caesar cipher *query* key optional (caesar)',inline=False)
    embed.add_field(name='Other',value='**!info**: Current hunt login and links (hunt, huntinfo)\n'\
        '**!sz**: Szeth emote (szeth)\n'\
        '**!flip**: Toss a coin to your Witcher!\n'\
        '**!dice** *N S*: Roll *N* dice each of *S* sides (roll)\n'\
        'Other trigger words, good luck finding them...',inline=False)
    embed.set_footer(text='Crreated by @Moonrise')
    await ctx.send(embed=embed)

@bot.command(name='sz')
async def szeth(ctx):
    await ctx.send('<:szeth:667773296896507919>')


# Development Commands #######################################################

@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.lower() =='pping':
        await message.channel.send('Pong!')

@bot.command(name='load')
@commands.is_owner()
async def load(ctx, cogname):
    bot.load_extension('cogs.'+cogname)
    await ctx.send('Cog {} is loaded!'.format(cogname))

@bot.command(name='reload')
@commands.is_owner()
async def reload(ctx, cogname):
    bot.reload_extension('cogs.'+cogname)
    await ctx.send('Cog {} is reloaded!'.format(cogname))

@bot.command(name='unload')
@commands.is_owner()
async def unload(ctx, cogname):
    bot.unload_extension('cogs.'+cogname)
    await ctx.send('Cog {} is unloaded!'.format(cogname))
    
@bot.listen()
async def on_command_error(ctx, error):
    await ctx.send(error)

bot.run(TOKEN)

