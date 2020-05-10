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
    async def insertlogin(self, ctx, *, query=None):
        helpstate = 'To use: `!insertlogin <guildName> <guildID>'

        if not query:
            await ctx.send(helpstate)
            return

        guildname,guildID = query.split(' ')
        db = DBase(ctx)
        await db.inserthuntdata(guildname,guildID)


    @commands.command(aliases=['del'])
    @commands.is_owner()
    async def deletelogin(self, ctx, *, guildID=None):
        helpstate = 'To use: `!deletelogin <guildID>'

        if not guildID:
            await ctx.send(helpstate)
            return

        db = DBase(ctx)
        await db.deletehuntdata(guildID)





def setup(bot):
    bot.add_cog(AdminCog(bot))


