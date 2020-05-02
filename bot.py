# bot.py
import os
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands



load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')



bot = commands.Bot(command_prefix='!',case_insensitive=True)
MoonID = '<@416656299661459458>'

initial_extensions = ['misc',
                      'toolbox',
                      'noncommand',
                      'hunt',
                      'debris']

#initial_extensions = ['debris']


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    for extension in initial_extensions:
        bot.load_extension('cogs.'+extension)
    pfp = open('./misc/mush0_color.png', 'rb').read()
    await bot.user.edit(avatar=pfp)


# General #################################################################

bot.remove_command('help')

@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title='Commands',
        colour=discord.Colour.dark_grey()
    )
    embed.add_field(name='Tools',value='**!nut** *query*: Nutrimatic\n'\
        '**!qq** *query key*: Quipqiup (opt. key(s))\n'\
        '**!cc** *query key*: Caesar cipher (opt. key)\n'\
        '**!let** *query*: Convert letters <-> numbers',inline=False)
    embed.add_field(name='Other',value='**!info**: Current hunt login and links\n'\
        '**!sz**: Szeth\n'\
        '**!flip**: Toss a coin to your Witcher!\n'\
        '**!dice** *N S*: Roll *N* dice of *S* sides\n'\
        'What does Mbot need to engage to fly?\n',inline=False)
    embed.set_footer(text='Created/hosted by @Moonrise')
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

@bot.command(name='restart')
@commands.is_owner()
async def restart(ctx,initial=initial_extensions):
    for cogname in initial:
        try:
            bot.reload_extension('cogs.'+cogname)
            await ctx.send('Cog {} is reloaded!'.format(cogname))
        except:
            try: 
                bot.load_extension('cogs.'+cogname)
                await ctx.send('Cog {} is loaded!'.format(cogname))
            except:
                await ctx.send('Cog {} not loaded :('.format(cogname))

    

@bot.listen()
async def on_command_error(ctx, error):
    await ctx.send(error)

bot.run(TOKEN)

