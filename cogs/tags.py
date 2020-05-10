# tags.py
import discord
from discord.ext import commands
import asyncio
from utils.db import DBase
from utils.paginator import Pages


# A cog with some useful hunt and puzzle organization commands

class TagsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    def checkguild(self,guildID):
        ''' guildID: string '''
        return guildID in ['669061724569206784']


    @commands.command(aliases=['tag'])
    @commands.guild_only()
    async def taginfo(self, ctx, *, query=None):
        helpstate = 'To use:\n`!tag list` will list all tags\n`!tag <name>` fetches a stored message\n`!tag <name> -new` saves your next message\n'\
            '`!tag <name> -update` overwrites existing tag with your next message\n`!tag <name> -delete`' \

        guildID = str(ctx.guild.id)

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        if not self.checkguild(guildID):
            await ctx.send('Nope')
            return

        if not query:
            await ctx.send(helpstate)
            return


        if query == 'list':
            db = DBase(ctx)
            result = await db.gettagall()
            if result:
                final = []
                for item in result:
                    final.append(item[0])

            embed = discord.Embed(title='Existing Tags', colour=discord.Colour.teal())
            
            p = Pages(ctx,solutions=final,embedTemp=embed)
            await p.pageLoop()
            return

        
        # initialize db
        db = DBase(ctx)      


        if '-' not in query:
            result = await db.gettagsingle(query)
            if result:
                tagcontent = result[0][0].replace('qqq',"'")
                await ctx.send('>>> '+tagcontent)
            else:
                await ctx.send('No tag found: `'+query+'`.')
            return
    
        # unpack modifiers
        tagname, action = query.split(' -',1)
        result = await db.gettagsingle(tagname)

        if action == 'new':
            if result:
                await ctx.send('Tag already exists: `'+tagname+'`.')
                return
            await ctx.send('Your next message will be saved under `'+tagname+'`.')
            try: 
                response = await self.bot.wait_for('message',check=check,timeout=900.0)
            except asyncio.TimeoutError:
                await ctx.send('You timed out to add a tag. That was 15 min.')
                return

            tagcontent = response.content.replace("'",'qqq')
            await db.inserttag(tagname,tagcontent)

            
        elif action == 'update':
            if not result:
                await ctx.send('No tag found: `'+tagname+'`. Make a new tag first.')
                return
            await ctx.send('Your next message will be saved under `'+tagname+'`.')
            try: 
                response = await self.bot.wait_for('message',check=check,timeout=900.0)
            except asyncio.TimeoutError:
                await ctx.send('You timed out to add a tag. That was 15 min.')
                return

            tagcontent = response.content.replace("'",'qqq')
            await db.updatetag(tagname,tagcontent)

        
        elif action == 'delete':
            if not result:
                await ctx.send('No tag found: `'+tagname+'`. Make a tag before you delete it.')
                return
            
            await db.deletetag(tagname)


        else:
            await ctx.send('I don\'t understand that...\n'+helpstate)




def setup(bot):
    bot.add_cog(TagsCog(bot))

