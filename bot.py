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
intents.message_content = True

bot = commands.Bot(command_prefix='!',case_insensitive=True,intents=intents)

initial_extensions = ['misc',
                       'toolbox',
                       'login',
                       'debris',
                       'admin',
                       'tags',
                       'hunt',
                       'archive']

# initial_extensions = ['login','hunt']

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    for extension in initial_extensions:
        await bot.load_extension('cogs.' + extension)


# General #################################################################

# help moved to hunt cog
bot.remove_command('help')

# Development Commands #######################################################

# @bot.listen()
# async def on_message(message):
#     if message.author == bot.user:
#         return
#     if message.content.lower() =='pping':
#         await message.channel.send('Pong!')

@bot.command(name='load')
@commands.is_owner()
@commands.has_role('organiser')
async def load_cog(ctx, cogname):
    await bot.load_extension('cogs.'+cogname)
    await ctx.send('Cog {} is loaded!'.format(cogname))

@bot.command(name='reload')
@commands.has_role('organiser')
@commands.is_owner()
async def reload_cog(ctx, cogname):
    await bot.reload_extension('cogs.'+cogname)
    await ctx.send('Cog {} is reloaded!'.format(cogname))

@bot.command(name='unload')
@commands.has_role('organiser')
@commands.is_owner()
async def unload_cog(ctx, cogname):
    await bot.unload_extension('cogs.'+cogname)
    await ctx.send('Cog {} is unloaded!'.format(cogname))

@bot.command(name='restart')
@commands.has_role('organiser')
@commands.is_owner()
async def restart_cog(ctx,initial_extensions=initial_extensions):
    for extension in initial_extensions:
        try:
            await bot.reload_extension('cogs.'+extension)
            await ctx.send('Cog {} is reloaded!'.format(extension))
        except:
            try: 
                await bot.load_extension('cogs.'+extension)
                await ctx.send('Cog {} is loaded!'.format(extension))
            except:
                await ctx.send('Cog {} not loaded :('.format(extension))

    

@bot.listen()
async def on_command_error(ctx, error):
    await ctx.send(error)

bot.run(TOKEN)

