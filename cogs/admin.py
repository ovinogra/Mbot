# admin.py
from tabnanny import check
import discord
from discord.ext import commands
from utils.db2 import DBase


# A cog with some db owner commands, mostly for testing

class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=['ins'])
    @commands.is_owner()
    @commands.has_role('organiser')
    async def login_insert(self, ctx, *, query=None):
        ''' adds a row the hunt db table to initiate puzzle manager commands '''

        if not query:
            await ctx.send('To use: `!ins <guildName> <guildID>')
            return

        guildname,guildID = query.split(' ')
        db = DBase(ctx)
        await db.hunt_insert_row(guildname, int(guildID), ctx.message.channel.category.id)


    @commands.command(aliases=['del'])
    @commands.is_owner()
    @commands.has_role('organiser')
    async def login_delete(self, ctx, *, guildID=None):

        if not guildID:
            await ctx.send('To use: `!del <guildID>')
            return

        db = DBase(ctx)
        await db.hunt_delete_row(int(guildID), ctx.message.channel.category.id)


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

        channels = ctx.message.channel.category.channels
        if action == 'check':
            namesall = ['Channels to be deleted:']
            for channel in channels:
                namesall.append(channel.mention)
            await ctx.send('\n'.join(namesall))
        elif action == 'doit':
            for channel in channels:
                await channel.delete()            
        


async def setup(bot):
    await bot.add_cog(AdminCog(bot))


