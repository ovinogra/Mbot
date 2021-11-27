# bot.py
import os
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='?',case_insensitive=True,intents=intents)

# initial_extensions = ['misc',
#                       'toolbox',
#                       'login',
#                       'debris',
#                       'admin',
#                       'tags',
#                       'hunt',
#                       'bighunt',
#                       'archive']

initial_extensions = ['bighunt']

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    for extension in initial_extensions:
        bot.load_extension('cogs.'+extension)


# General #################################################################

bot.remove_command('help')

@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title='Commands',
        colour=discord.Colour.dark_grey()
    )
    embed.add_field(name='Tools',value=
        '**!nut**: Nutrimatic\n'\
#        '**!qq**: Quipqiup\n'\
        '**!cc**: Caesar cipher\n'\
        '**!vig**: Vigenere cipher\n'\
        '**!alpha**: A1Z26\n'\
        '**!atbash**: atbash cipher\n'\
        '**!atom**: Periodic table\n'\
        '**!tag**: Other resources',inline=True)
    embed.add_field(name='Puzzle Manager',value=
        '**!login** [update]\n'\
        '**!nexus** [-unsolved] [-round=1]\n**!create** Name [-round=1]\n**!solve** ANSWER\n**!note** backsolve\n**!update** [-name=Name]\n**!undosolve**\n'\
        '**!check** (setup only)',inline=True)
    embed.add_field(name='Fun',value='**!sz**, **!flip**, **!dice** *N S*, engage',inline=False)
    embed.set_footer(text='@Moonrise#3554')
    await ctx.send(embed=embed)


# Development Commands #######################################################

# @bot.listen()
# async def on_message(message):
#     if message.author == bot.user:
#         return
#     if message.content.lower() =='pping':
#         await message.channel.send('Pong!')

@bot.command(name='load')
@commands.is_owner()
async def load_cog(ctx, cogname):
    bot.load_extension('cogs.'+cogname)
    await ctx.send('Cog {} is loaded!'.format(cogname))

@bot.command(name='reload')
@commands.is_owner()
async def reload_cog(ctx, cogname):
    bot.reload_extension('cogs.'+cogname)
    await ctx.send('Cog {} is reloaded!'.format(cogname))

@bot.command(name='unload')
@commands.is_owner()
async def unload_cog(ctx, cogname):
    bot.unload_extension('cogs.'+cogname)
    await ctx.send('Cog {} is unloaded!'.format(cogname))

@bot.command(name='restart')
@commands.is_owner()
async def restart_cog(ctx,initial_extensions=initial_extensions):
    for extension in initial_extensions:
        try:
            bot.reload_extension('cogs.'+extension)
            await ctx.send('Cog {} is reloaded!'.format(extension))
        except:
            try: 
                bot.load_extension('cogs.'+extension)
                await ctx.send('Cog {} is loaded!'.format(extension))
            except:
                await ctx.send('Cog {} not loaded :('.format(extension))

    

@bot.listen()
async def on_command_error(ctx, error):
    await ctx.send(error)

bot.run(TOKEN)

