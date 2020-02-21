# hunt.py
import discord
from discord.ext import commands


# A cog with some simple non command responses

huntrole = 'pam player'

class HuntCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.huntsite = None
        self.huntuser = None
        self.huntpswd = None
        self.huntnexus = None
        self.huntfolder = None


    @commands.command(name='set')
    @commands.has_role('organiser')
    async def sethunt(self, ctx, *, change):
        if change[:4] == 'site':
            self.huntsite = change[5:]
            await ctx.send('Hunt site set to: '+self.huntsite)
        elif change[:4] == 'user':
            self.huntuser = change[5:]
            await ctx.send('Hunt username set to: '+self.huntuser)
        elif change[:4] == 'pswd':
            self.huntpswd = change[5:]
            await ctx.send('Hunt password set to: '+self.huntpswd)
        elif change[:5] == 'nexus':
            self.huntnexus = change[6:]
            await ctx.send('Hunt nexus set to: '+self.huntnexus)
        elif change[:6] == 'folder':
            self.huntfolder = change[7:]
            await ctx.send('Hunt folder set to: '+self.huntfolder)
        else:
            await ctx.send('Not a valid set keyword. Choose from site, user, pswd, nexus, or folder.')


    @commands.command(aliases=['info','hunt'])
    @commands.has_role(huntrole)
    async def huntinfo(self, ctx):
        embed = discord.Embed(
            colour=discord.Colour.magenta(),
            description="**Website**: "+self.huntsite+"\n**Username**: "+self.huntuser+" \n**Password**: "+self.huntpswd+"\n[**Nexus Link**]("+self.huntnexus+") \n[**Folder Link**]("+self.huntfolder+")"
        )
        await ctx.send(embed=embed)


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            command = ctx.command
            if command.name is 'sethunt':
                await ctx.send('You do not have the role for this command')
            if command.name is 'huntinfo':
                await ctx.send('You do not have the role for the current puzzlehunt. Do you want to join it?')



def setup(bot):
    bot.add_cog(HuntCog(bot))

