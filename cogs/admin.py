# admin.py
from tabnanny import check
import discord
from discord.ext import commands
from utils.db2 import DBase


# A cog with some db owner commands, mostly for testing

class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['stat'])
    async def server_status(self, ctx):
        final = []
        final.append('Number of Text Channels: '+str(len(ctx.message.guild.text_channels)))
        final.append('Number of Channels Against Limit: '+str(len(ctx.message.guild.channels)))
        final.append('Number of Members: '+str(len(ctx.message.guild.members)))
        final = '\n'.join(final)
        await ctx.send(final)


    @commands.command(aliases=['data'])
    async def show_message_data(self, ctx, msgid=None):

        channels = ctx.guild.text_channels 
        msg = False
        for channel in channels:
            try:
                msg = await channel.fetch_message(msgid)
            except:
                continue

        if msg:
            final = []
            final.append('Category: '+str(msg.channel.category))
            final.append('Channel: '+str(msg.channel.mention))
            final.append('Author: '+str(msg.author))
            final.append('Created At (UTC): '+str(msg.created_at))
            final.append('>>> '+str(msg.content))
            final = '\n'.join(final)
            await ctx.send(final)
            await ctx.send('All metadata:\n'+str(msg))
        else:
            await ctx.send('Message not found. ')


    @commands.command(aliases=['rmc'])
    @commands.has_role('organiser')
    @commands.guild_only()
    async def delete_category(self, ctx, *, action=None):

        if action is None:
            await ctx.send('`!rmc check` will print the channels to be deleted\n`!rmc doit` will delete said channels')
            return 

        category = ctx.message.channel.category
        channels = category.channels
        if action == 'check':
            namesall = ['Channels to be deleted:']
            for channel in channels:
                namesall.append(channel.mention)
            await ctx.send('\n'.join(namesall))
        elif action == 'doit':
            for channel in channels:
                await channel.delete()
            await category.delete()
        

async def setup(bot):
    await bot.add_cog(AdminCog(bot))


