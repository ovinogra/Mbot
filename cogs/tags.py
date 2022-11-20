# tags.py
import discord
from discord.ext import commands
import asyncio
from utils.db2 import DBase
from utils.paginator import Pages


# A cog with some useful hunt and puzzle organization commands

class TagsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    def checkguild(self,guildID):
        ''' guildID: string, this function exists mostly for testing '''

        #return guildID in ['669061724569206784','555663169612283904']
        return True


    @commands.command(aliases=['tag','tags'])
    @commands.guild_only()
    async def taginfo(self, ctx, *, query=None):
        helpstate = '`!tag list`\n`!tag [create] [update] [delete] <name>`'

        guildID = str(ctx.guild.id)

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        if not self.checkguild(guildID):
            await ctx.send('Nope, not in this server.')
            return

        if not query:
            await ctx.send(helpstate)
            return

        db = DBase(ctx)  
        quers = query.split(' ',1)

        if quers[0] == 'list':
            result = db.tag_get_all()
            if result:
                final = []
                for item in result:
                    final.append(item['tag_name'])
            final.sort()
            embed = discord.Embed(title='Existing Tags', colour=discord.Colour.teal())
            
            p = Pages(ctx,solutions=final,embedTemp=embed)
            await p.pageLoop()
            return

        if quers[0] == 'create':
            tagname = quers[1]
            result = db.tag_get_row(tagname)
            if result:
                await ctx.send('Tag already exists: `'+tagname+'`.')
                return
            await ctx.send('Your next message will be saved under `'+tagname+'`.')
            try: 
                response = await self.bot.wait_for('message',check=check,timeout=900.0)
            except asyncio.TimeoutError:
                await ctx.send('You timed out to add a tag. That was 15 min you know.')
                return

            tagcontent = response.content.replace("'",'qqq')
            await db.tag_insert_row(tagname,tagcontent,ctx.guild.id)
            return

        if quers[0] == 'update':
            tagname = quers[1]
            result = db.tag_get_row(tagname)
            if not result:
                await ctx.send('No tag found: `'+tagname+'`')
                return
            await ctx.send('Your next message will overwrite message under `'+tagname+'`.')
            try: 
                response = await self.bot.wait_for('message',check=check,timeout=900.0)
            except asyncio.TimeoutError:
                await ctx.send('You timed out to add a tag. That was 15 min you know.')
                return

            tagcontent = response.content.replace("'",'qqq')
            await db.tag_update_row(tagname,tagcontent)
            return
        
        if quers[0] == 'delete':
            tagname = quers[1]
            result = db.tag_get_row(tagname)
            if not result:
                await ctx.send('No tag found: `'+tagname+'`. Make a tag before you delete it.')
                return
            await db.tag_delete_row(tagname)
            return
        

        result = db.tag_get_row(query)
        if result:
            tagcontent = result['tag_content'].replace('qqq',"'")
            await ctx.send('>>> '+tagcontent)
        else:
            await ctx.send('No tag found: `'+query+'`.')
        return

        




def setup(bot):
    bot.add_cog(TagsCog(bot))

