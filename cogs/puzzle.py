# puzzle.py

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import gspread
import random

from utils.db import DBase


# A cog with some useful hunt and puzzle organization commands


# TODO this file is a mess, should probably clean it


class PuzzCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot




    def client_email(self):
        load_dotenv()
        return os.getenv('CLIENT_EMAIL')


    def gclient(self):
        client = gspread.service_account('client_secrets.json')
        return client


    def channel_get_by_id(self,ctx,channelid):
        channel = discord.utils.get(ctx.guild.channels, id=channelid)
        return channel


    


    async def channel_create(self,ctx,name):
        # create channel in current category, return newchannel
        category = ctx.message.channel.category
        channelall = category.text_channels
        names = [item.name for item in channelall]
        if name in names:
            await ctx.send('Channel named `{}` already exists in category `{}`.'.format(name,category.name))
            return
        
        newchannnel = await category.create_text_channel(name)
        await ctx.send('(1/3) Channel {} created'.format(newchannnel.mention))
        return newchannnel


    async def channel_rename(self,ctx,channel,newname):
        #channel = ctx.guild.get_channel(int(channelid))
        channel.name = newname
        await channel.edit(name=newname)
        

    async def channel_delete(self,ctx,channelid):
        channel = ctx.guild.get_channel(int(channelid))
        await channel.delete()



    async def nexus_get_sheet(self,ctx):
        ''' fetch nexus sheet from hunt table, return sheet obj and url '''

        # fetch nexus url
        query = 'hunt_nexus'
        db = DBase(ctx)
        url = await db.hunt_get_row(query)
        nexus_key = max(url[0].split('/'),key=len)

        # authenticate connection
        gclient = self.gclient()
        wkbook = gclient.open_by_key(nexus_key)
        sheet = wkbook.sheet1
        return sheet, url[0]
    


    async def nexus_display(self,ctx):

        # fetch nexus data and sort headings
        nexussheet, nexus_url = await self.nexus_get_sheet(ctx)
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.sort_nexus_columns(headings)
        
        # want: Puzzle Name (linked), Answer, Priority
        data_channel = [item[lib['Channel ID'][0]] for item in data_all[2:]]
        #data_name = ['-' if item[lib['Puzzle Name'][0]] == '' else item[lib['Puzzle Name'][0]] for item in data_all[2:]]
        data_name = ['-' if item == '' else self.channel_get_by_id(ctx,int(item)).mention for item in data_channel]
        data_answer = ['-' if item[lib['Answer'][0]] == '' else item[lib['Answer'][0]] for item in data_all[2:]]
        data_priority = ['-' if item[lib['Priority'][0]] == '' else item[lib['Priority'][0]] for item in data_all[2:]]

        # sometimes, I think embeds are more trouble than they're worth
        # linking to gsheets not possible due to discord field limits: https://discord.com/developers/docs/resources/channel#embed-limits
        embed = discord.Embed(
            title='NEXUS Link',
            colour=discord.Colour(0xfffff0),
            url=nexus_url
        )

        names = ''
        answers = ''
        priority = ''
        for n in range(0,len(data_name)):
            names += data_name[n]+'\n'
            answers += data_answer[n]+'\n'
            priority += data_priority[n]+'\n'
        embed.add_field(name='Name',value=names,inline=True)
        embed.add_field(name='Answer',value=answers,inline=True)
        embed.add_field(name='Priority',value=priority,inline=True)

        await ctx.send(embed=embed)



    def check_puzzle_list(self,nexussheet,newpuzzle):
        ''' check if puzzle name already exists in nexus '''

        # fetch nexus data and sort headings
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.sort_nexus_columns(headings)
        
        data_name = [item[lib['Puzzle Name'][0]] for item in data_all[2:]]
        if newpuzzle in data_name:
            return True
        else:
            return False



    async def puzzle_sheet_make(self,ctx,nexussheet,puzzlename):

        # fetch nexus data and sort headings
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.sort_nexus_columns(headings)
        
        # assume template url is in ROW 2 under Spreadsheet Link
        template_url = data_all[1][lib['Spreadsheet Link'][0]]
        template_key = max(template_url.split('/'),key=len)

        gclient = self.gclient()
        newsheet = gclient.copy(template_key,title=puzzlename,copy_permissions=True)

        await ctx.send('(2/3) Google sheet made, sending link')

        newsheet_url = "https://docs.google.com/spreadsheets/d/%s" % newsheet.id
        return newsheet_url



    def sort_nexus_columns(self,headings):
        # return a dict of column names with their indicies
        # such that order of columns in nexus does not matter
        # assume all in label_key exists in nexus

        label_key = ['Channel ID','Round','Number','Puzzle Name','Answer','Spreadsheet Link','Priority','Notes']
        lib = {}
        for n in range(0,len(label_key)):
            label = label_key[n]
            index = int(headings.index(label))
            lib[label] = [index]

        return lib


    async def nexus_add_row(self,ctx,nexussheet,puzzlechannel,puzzlename,puzzlesheeturl):
        ''' add channel id, puzzle name, link, priority '''

        # fetch nexus data and sort headings
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.sort_nexus_columns(headings)

        temp = ['' for item in range(0,len(headings))]
        temp[lib['Channel ID'][0]] = str(puzzlechannel.id)
        temp[lib['Priority'][0]] = 'New'
        temp[lib['Puzzle Name'][0]] = puzzlename
        temp[lib['Spreadsheet Link'][0]] = puzzlesheeturl
        
        rownum = len(data_all)+1
        table_range = 'A'+str(rownum)+':'+gspread.utils.rowcol_to_a1(rownum,len(headings))
        nexussheet.append_row(temp,table_range=table_range)

        await ctx.send('(3/3) Nexus row added')




    async def check_puzz_command(self,ctx):
      
        # this awful sequence of checks and API calls presumably makes sure stuff won't break later
        checks = {}

        # channel category check
        category = ctx.message.channel.category.name
        checks['Category for Hunt'] = '`'+category+'`'

        # permissions check
        perms = ctx.channel.category.permissions_for(ctx.me)
        checks['Manage Messages'] = ':+1:' if perms.manage_messages else ':x:'
        checks['Manage Channels'] = ':+1:' if perms.manage_channels else ':x:'
        checks['Add Reactions'] = ':+1:' if perms.add_reactions else ':x:'

        # db hunt fetch links
        query = 'hunt_folder, hunt_nexus'
        db = DBase(ctx)
        results = await db.hunt_get_row(query)
        res = list(results)
        checks['Google Folder'] = '[Link]('+res[0]+')' if 'http' in res[0] else res[0]
        checks['Nexus Sheet'] = '[Link]('+res[1]+')' if 'http' in res[1] else res[1]

        # nexus sheet check API call
        try:
            nexussheet, nexus_url = await self.nexus_get_sheet(ctx)
            checks['Nexus Sheet Access'] = ':+1:'
        except:
            checks['Nexus Sheet Access'] = ':x:'

        # nexus sheet check hardcoded columns
        try:
            data_all = nexussheet.get_all_values()
            headings = data_all[0]
            lib = self.sort_nexus_columns(headings)
            checks['Nexus Sheet Columns'] = ':+1:'
        except:
            checks['Nexus Sheet Columns'] = ':x:'

        # nexus sheet fetch puzzle template link
        try:
            template_url = data_all[1][lib['Spreadsheet Link'][0]]
            checks['Template Sheet'] = '[Link]('+template_url+')' if 'http' in template_url else template_url
        except:
            checks['Template Sheet'] = ':x:'

        # template sheet check API call
        try:
            template_key = max(template_url.split('/'),key=len)
            gclient = self.gclient()
            wkbook = gclient.open_by_key(template_key)
            wkbook.sheet1
            checks['Template Sheet Access'] = ':+1:'
        except:
            checks['Template Sheet Access'] = ':x:'

        # format checks
        topic = ''
        status = ''
        for item in checks:
            topic += item+'\n'
            status += checks[item]+'\n'

        # set up embed
        embed = discord.Embed(
            title='Checks',
            colour=discord.Colour(0xfffff0),
            description='Note: New puzzle channels keep role permissions of listed category')
        embed.add_field(name='Topic',value=topic,inline=True)
        embed.add_field(name='Status',value=status,inline=True)

        await ctx.send(embed=embed)




    async def nexus_update_row(self,ctx,query):

        # fetch nexus data and sort headings
        nexussheet, nexus_url = await self.nexus_get_sheet(ctx)
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.sort_nexus_columns(headings)


        updatedict = {}
        for item in query:
            quer = item.split('=')
            updatedict[quer[0]] = quer[1]

        channel = ctx.channel
        channelid = str(channel.id)
        

        # search for puzzle by Channel ID
        data_id = [item[lib['Channel ID'][0]] for item in data_all]

        try:
            row_select = data_id.index(channelid)+1
        except:
            await ctx.send('Channel ID = {} does not exist in Nexus.'.format(channelid))
            return

        puzzlename = data_all[row_select-1][lib['Puzzle Name'][0]]

        # there's probably a way to udpate all of this in one row
        for item in updatedict:

            if item == 'round':
                col_select = lib['Round'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item])
                await ctx.send('Updated round for puzzle: {}'.format(puzzlename))
            
            if item == 'number':
                col_select = lib['Number'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item])
                await ctx.send('Updated number for puzzle: {}'.format(puzzlename))
            
            if item == 'name':
                col_select = lib['Puzzle Name'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item])
                await self.channel_rename(ctx,channel,updatedict[item])
                await ctx.send('Updated name for puzzle: {}'.format(puzzlename))
            
            if item == 'answer':
                col_select = lib['Answer'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item].upper())
                col_select = lib['Priority'][0]+1
                nexussheet.update_cell(row_select, col_select, 'Solved')
                
                if '✔' in channel.name:
                    await ctx.send('Updated solution (again): {}'.format(puzzlename))
                else:
                    emote = random.choice(['bang','face_explode','face_hearts','face_openmouth','face_party','face_stars','party','rocket','star','mbot','slug'])
                    filepath = './misc/emotes/'+emote+'.png'
                    await ctx.send(content='`{}` marked as solved!'.format(puzzlename),file=discord.File(filepath))
                    await self.channel_rename(ctx,channel,'✔'+channel.name)
            
            if item == 'priority':
                col_select = lib['Priority'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item].title())
                await ctx.send('Updated priority for puzzle: {}'.format(puzzlename))

            if item == 'notes':
                col_select = lib['Notes'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item])
                await ctx.send('Updated notes for puzzle: {}'.format(puzzlename))



    async def solve(self, ctx, solution):

        # fetch nexus data and sort headings
        nexussheet, nexus_url = await self.nexus_get_sheet(ctx)
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.sort_nexus_columns(headings)

        channel = ctx.channel
        channelid = str(channel.id)
        
        # search for puzzle by Channel ID
        data_id = [item[lib['Channel ID'][0]] for item in data_all]

        try:
            row_select = data_id.index(channelid)+1
        except:
            await ctx.send('Channel ID {} does not exist in Nexus.'.format(channelid))
            return

        puzzlename = data_all[row_select-1][lib['Puzzle Name'][0]]


        col_select = lib['Answer'][0]+1
        nexussheet.update_cell(row_select, col_select, solution.upper())
        col_select = lib['Priority'][0]+1
        nexussheet.update_cell(row_select, col_select, 'Solved')
        
        if '✔' in channel.name:
            await ctx.send('Updated solution (again): {}'.format(puzzlename))
        else:
            emote = random.choice(['bang','face_explode','face_hearts','face_openmouth','face_party','face_stars','party','rocket','star','mbot','slug'])
            filepath = './misc/emotes/'+emote+'.png'
            await ctx.send(content='`{}` marked as solved!'.format(puzzlename),file=discord.File(filepath))
            await self.channel_rename(ctx,channel,'✔'+channel.name)



    @commands.command()
    @commands.guild_only()
    async def nexus(self, ctx):
        await self.nexus_display(ctx)



    # !puzz manager requires:
    # 1) A google folder with a Nexus sheet and a Template sheet
    # 2) Hardcoded columns in Nexus: Channel ID, Round, Number, Puzzle Name, Answer, Spreadsheet Link, Priority, Notes
    # 3) Template sheet link as the first entry under Spreadsheet Link



    @commands.command(aliases=['puzz'])
    @commands.guild_only()
    async def puzzle(self, ctx, *, query=None):
        helpstate = '`!puzz create <Puzzle Name>` make new channel, copy template sheet, send link, add nexus row\n'\
            '`!puzz solve <answer>`\n'\
            '`!puzz nexus`\n\n'\
                'Before using `!puzz`:\n'\
                    '1) Check for correct links in `!login`\n'\
                    '2) Share folder with `'+self.client_email()+'`\n'\
                    '3) Check permissions with `!puzz check`'


        if not query:
            await ctx.send(helpstate)
            return

        quers = query.split(' ',1)
        
        if quers[0] == 'nexus':
            await self.nexus_display(ctx)
        
        elif quers[0] == 'check':
            await self.check_puzz_command(ctx)

        elif quers[0] == 'create':
            if len(quers) == 1:
                await ctx.send('Give a name to initiate a new puzzle.')
                return

            puzzlename = quers[1]
            nexussheet,nexusheet_url = await self.nexus_get_sheet(ctx)
            if self.check_puzzle_list(nexussheet,puzzlename):
                await ctx.send('Puzzle named `{}` already exists in Nexus.'.format(puzzlename))
                return

            # run puzzle creation sequence
            newchannel = await self.channel_create(ctx,puzzlename)
            if newchannel:
                newsheet_url = await self.puzzle_sheet_make(ctx,nexussheet,puzzlename)
                msg = await newchannel.send(newsheet_url)
                await msg.pin()
                await self.nexus_add_row(ctx,nexussheet,newchannel,puzzlename,newsheet_url)


        elif quers[0] == 'solve':
            if len(quers) == 1:
                await ctx.send('Need a solution here.')
                return

            await self.solve(ctx,quers[1])

        elif quers[0] == 'update':
            if len(quers) == 1:
                await ctx.send('`!puzz update [-round=<>] [-number=<>] [-name=<>] [-answer=<>] [-priority=<>] [-notes=<>]`')
                return
            
            prequery = query.split(' -')
            updatequery = prequery[1:]
            await self.nexus_update_row(ctx,updatequery)


        else:
            await ctx.send('I don\'t understand that...\n'+helpstate)





def setup(bot):
    bot.add_cog(PuzzCog(bot))

