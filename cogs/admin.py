# admin.py
import discord
from discord.ext import commands
from utils.db import DBase


# A cog with some db owner commands, mostly for testing

class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=['ins'])
    @commands.is_owner()
    async def logininsert(self, ctx, *, query=None):
        helpstate = 'To use: `!logininsert <guildName> <guildID>'

        if not query:
            await ctx.send(helpstate)
            return

        guildname,guildID = query.split(' ')
        db = DBase(ctx)
        await db.hunt_insert_row(guildname,guildID)


    @commands.command(aliases=['del'])
    @commands.is_owner()
    async def logindelete(self, ctx, *, guildID=None):
        helpstate = 'To use: `!logindelete <guildID>'

        if not guildID:
            await ctx.send(helpstate)
            return

        db = DBase(ctx)
        await db.hunt_delete_row(guildID)


    @commands.command(aliases=['stat'])
    async def serverstatus(self, ctx):
        final = []
        final.append('Number of Text Channels: '+str(len(ctx.message.guild.text_channels)))
        final.append('Number of Channels Against Limit: '+str(len(ctx.message.guild.channels)))
        final.append('Number of Members: '+str(len(ctx.message.guild.members)))
        final = '\n'.join(final)
        await ctx.send(final)






def setup(bot):
    bot.add_cog(AdminCog(bot))


