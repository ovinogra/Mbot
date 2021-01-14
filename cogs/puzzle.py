# puzzle.py

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import gspread
import random
import json
import numpy as np
import datetime
from utils.db import DBase
from google.oauth2 import service_account


# A cog for puzzle management
# !nexus
# !create
# !solve
# !update
# !checksetup

# 1) The "hunt" db table must be updated with nexus and folder links (through !login update in cogs/hunt.py)
# 2) Nexus sheet must have correct formatting
#      -columns: Channel ID, Round, Number, Puzzle Name, Answer, Spreadsheet Link, Priority, Notes, Created At, Solved At
#      -first entry under Spreadsheet Link must be url to a puzzle template sheet
# 3) Folder must be shared with google service account


class PuzzCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.mark = '✅'
        #self.mark = '✔'

        # TODO: has to be a less silly way to organize this
        load_dotenv()
        self.key = os.getenv('GOOGLE_CLIENT_SECRETS')
        self.googledata = json.loads(self.key)
        self.googledata['private_key'] = self.googledata['private_key'].replace("\\n","\n")
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = service_account.Credentials.from_service_account_info(self.googledata,scopes=scopes)





    def gclient(self):
        client = gspread.authorize(self.credentials)
        return client

    def channel_get_by_id(self,ctx,channelid):
        try:
            channel = discord.utils.get(ctx.guild.channels, id=channelid)
            return channel
        except:
            return False

    def check_puzzle_list(self,nexussheet,newpuzzle):
        ''' check if puzzle name already exists in nexus '''

        # fetch nexus data and sort headings
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)
        
        data_name = [item[lib['Puzzle Name'][0]] for item in data_all[2:]]
        if newpuzzle in data_name:
            return True
        else:
            return False

    def check_channel_list(self,ctx,name):
        ''' check if channel name already exists in current category '''

        category = ctx.message.channel.category
        channelall = category.text_channels
        names = [item.name for item in channelall]
        if name in names:
            return True
        else:
            return False

    async def check_hunt_role(self,ctx):
        ''' check if user has role for current hunt '''

        query = 'hunt_role_id'
        db = DBase(ctx)
        results = await db.hunt_get_row(query)

        # guild does not exist in db
        if not results:
            await ctx.send('Not in this guild.')
            return False

        res = list(results)
        # no hunt role set
        if res[0] == 'none':
            return True
        else:
            roleid = int(res[0])
            status = discord.utils.get(ctx.author.roles, id=roleid)
            # role is not correct
            if not status:
                await ctx.send('Missing role for current hunt. ')
                return False
            # role is correct
            else: 
                return True



    async def channel_create(self,ctx,name,position):
        category = ctx.message.channel.category        
        newchannnel = await category.create_text_channel(name=name,position=position)
        return newchannnel

    async def channel_rename(self,ctx,channel,newname):
        channel.name = newname
        await channel.edit(name=newname)
    
    @commands.command()
    @commands.is_owner()
    async def channel_delete(self,ctx,channelid):
        channel = ctx.guild.get_channel(int(channelid))
        await channel.delete()



    async def nexus_get_url(self,ctx):
        query = 'hunt_nexus'
        db = DBase(ctx)
        url = await db.hunt_get_row(query)
        return url[0]

    def nexus_get_sheet(self,url):
        nexus_key = max(url.split('/'),key=len)
        gclient = self.gclient()
        wkbook = gclient.open_by_key(nexus_key)
        sheet = wkbook.sheet1
        return sheet

    def nexus_sort_columns(self,headings):
        """
        make nexus column order independent
        return a dict of column names with their indicies
        assume all in label_key exists in nexus
        """

        label_key = ['Channel ID','Round','Number','Puzzle Name','Answer','Spreadsheet Link','Priority','Notes','Created At','Solved At']
        lib = {}
        for n in range(0,len(label_key)):
            label = label_key[n]
            index = int(headings.index(label))
            lib[label] = [index]

        return lib

    def nexus_add_row(self,nexussheet,puzzlechannel,puzzlename,puzzlesheeturl,roundname):
        """ add channel id, puzzle name, link, priority=New """

        # fetch nexus data and sort headings
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        temp = ['' for item in range(0,len(headings))]
        temp[lib['Channel ID'][0]] = str(puzzlechannel.id)
        temp[lib['Priority'][0]] = 'New'
        temp[lib['Puzzle Name'][0]] = puzzlename
        temp[lib['Spreadsheet Link'][0]] = puzzlesheeturl
        if roundname:
            temp[lib['Round'][0]] = roundname


        rownum = len(data_all)+1
        table_range = 'A'+str(rownum)+':'+gspread.utils.rowcol_to_a1(rownum,len(headings))
        nexussheet.append_row(temp,table_range=table_range)

        col_select = lib['Created At'][0]+1
        nexussheet.update_cell(rownum, col_select, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    def puzzle_sheet_make(self,nexussheet,puzzlename):
        """ copy template sheet from link in Nexus and return link to new sheet """

        # fetch nexus data and sort headings
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)
        
        # assume template url is in ROW 2 under Spreadsheet Link
        template_url = data_all[1][lib['Spreadsheet Link'][0]]
        template_key = max(template_url.split('/'),key=len)

        # make copy of template sheet
        gclient = self.gclient()
        newsheet = gclient.copy(template_key,title=puzzlename,copy_permissions=True)
        newsheet_url = "https://docs.google.com/spreadsheets/d/%s" % newsheet.id
        return newsheet_url



    @commands.command()
    @commands.guild_only()
    async def nexus(self,ctx,*,query=None):
        """ 
        display list of puzzles and solutions
        can flag by round or unsolved 
        """

        if not await self.check_hunt_role(ctx):
            return

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        nexussheet = self.nexus_get_sheet(nexus_url)
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)
        
        # want: puzzle channel mention (linked), answer, round
        data_channel = [item[lib['Channel ID'][0]] for item in data_all[2:]]
        data_round = ['Unsorted' if item[lib['Round'][0]] == '' else item[lib['Round'][0]] for item in data_all[2:]]
        data_number = ['-' if item[lib['Number'][0]] == '' else item[lib['Number'][0]] for item in data_all[2:]]
        #data_name = ['-' if item == '' else self.channel_get_by_id(ctx,int(item)).mention for item in data_channel]
        data_answer = ['-' if item[lib['Answer'][0]] == '' else item[lib['Answer'][0]] for item in data_all[2:]]

        print('start')
        data_name = []
        for j, item in enumerate(data_channel):
            if item == '':
                data_name.append('-')
            else:
                channelpick = self.channel_get_by_id(ctx,int(item))
                if channelpick:
                    data_name.append(channelpick.mention)
                else:
                    nameidx = lib['Puzzle Name'][0]
                    datatemp = data_all[2:][j]
                    data_name.append(datatemp[int(nameidx)])

        # remove empty rows
        while '' in data_channel:
            for n in range(0,len(data_channel)):
                if not data_channel[n]:
                    del data_channel[n]
                    del data_round[n]
                    del data_number[n]
                    del data_name[n]
                    del data_answer[n]
                    break

        embed = discord.Embed(
            title='Nexus Link',
            colour=discord.Colour(0xfffff0),
            url=nexus_url
        )

        if query:
            
            if query == '-unsolved':
                names = ''
                for n in range(0,len(data_name)):
                    if data_answer[n] == '-':
                        names += data_round[n]+'-'+data_number[n]+': '+data_name[n]+'\n'
                embed.add_field(name='Unsolved',value=names,inline=True)
                await ctx.send(embed=embed)
                return
            
            if '-round=' in query:
                roundnumber = query.split('=')[1]
                names = ''
                if roundnumber in data_round:
                    for n in range(0,len(data_name)):
                        if data_round[n] == query.split('=')[1]:
                            names += data_number[n]+': '+data_name[n]+' ('+data_answer[n]+')'+'\n'
                    embed.add_field(name='Round: '+query.split('=')[1],value=names,inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send('No such round found.')
                return

            await ctx.send('Accepted flags: `-round=` or `-unsolved`')
            return

        rounds = np.unique(data_round)
        for level in rounds:
            names = ''
            for n in range(0,len(data_name)):
                if data_round[n] == level:
                    names += data_number[n]+': '+data_name[n]+' ('+data_answer[n]+')'+'\n'
            embed.add_field(name='Round: '+str(level),value=names,inline=False)

        await ctx.send(embed=embed)






    @commands.command(aliases=['create'])
    @commands.guild_only()
    async def create_puzzle(self, ctx, *, query=None):
        """ puzzle creation script to 
        1) make channel
        2) copy template sheet
        3) add nexus entry
        """

        if not await self.check_hunt_role(ctx):
            return

        if not query:
            await ctx.send('`!create Some Puzzle Name Here -round=1`')
            return

        if '-round=' in query:
            puzzlename, roundname = query.split(' -round=')
        else:
            puzzlename = query
            roundname = False
        nexus_url = await self.nexus_get_url(ctx)
        nexussheet = self.nexus_get_sheet(nexus_url)

        # check existence of puzzle in channels and nexus
        if self.check_channel_list(ctx,puzzlename):
            await ctx.send('Channel named {} exists in current category.'.format(puzzlename))
            return
        if self.check_puzzle_list(nexussheet,puzzlename):
            await ctx.send('Puzzle named `{}` already exists in Nexus.'.format(puzzlename))
            return

        position = ctx.message.channel.category.channels[0].position

        # puzzle creation sequence
        infomsg = await ctx.send('Creating puzzle {}'.format(puzzlename))
        newchannel = await self.channel_create(ctx,puzzlename,position)
        newsheet_url = self.puzzle_sheet_make(nexussheet,puzzlename)
        msg = await newchannel.send(newsheet_url)
        await msg.pin()
        self.nexus_add_row(nexussheet=nexussheet,puzzlechannel=newchannel,puzzlename=puzzlename,puzzlesheeturl=newsheet_url,roundname=roundname)
        await infomsg.edit(content='Puzzle created at {}'.format(newchannel.mention))



    
    @commands.command(aliases=['solve'])
    @commands.guild_only()
    async def solve_puzzle(self, ctx, *, query=None):
        """ update puzzle in nexus with answer and solved priority """

        if not await self.check_hunt_role(ctx):
            return

        if not query:
            await ctx.send('`!solve Red Herring` in appropriate channel')
            return

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        nexussheet = self.nexus_get_sheet(nexus_url)
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # update column of choice (row_select) in correct row
        # 1) assume command was run in correct channel
        # 2) assume channel ID exists in nexus 
        data_id = [item[lib['Channel ID'][0]] for item in data_all]
        row_select = data_id.index(str(ctx.channel.id))+1
        col_select = lib['Answer'][0]+1
        nexussheet.update_cell(row_select, col_select, query.upper())
        col_select = lib['Priority'][0]+1
        nexussheet.update_cell(row_select, col_select, 'Solved')
        col_select = lib['Solved At'][0]+1
        nexussheet.update_cell(row_select, col_select, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # move channel down
        channels = ctx.message.channel.category.channels
        idx = channels[-1].position+1
        for channel in channels:
            if self.mark in channel.name:
                idx = channel.position 
                break
        await ctx.channel.edit(position=idx)

        # update user of solve
        puzzlename = data_all[row_select-1][lib['Puzzle Name'][0]]
        if self.mark not in ctx.channel.name:
            emote = random.choice(['gemheart','bang','face_explode','face_hearts','face_openmouth','face_party','face_stars','party','rocket','star','mbot','slug'])
            filepath = './misc/emotes/'+emote+'.png'
            await ctx.send(content='`{}` marked as solved!'.format(puzzlename),file=discord.File(filepath))
            await ctx.channel.edit(name=self.mark+ctx.channel.name)
        else:
            await ctx.send('Updated solution (again): {}'.format(puzzlename))
        


            
    

    @commands.command(aliases=['undosolve','imessedup'])
    @commands.guild_only()
    async def undo_solve_puzzle(self, ctx):
        """ remove solved puzzle changes in nexus (in case !solve is run in the wrong channel) """

        if not await self.check_hunt_role(ctx):
            return

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        nexussheet = self.nexus_get_sheet(nexus_url)
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # update column of choice (row_select) in correct row
        # assume channel ID exists in nexus 
        data_id = [item[lib['Channel ID'][0]] for item in data_all]
        row_select = data_id.index(str(ctx.channel.id))+1
        col_select = lib['Answer'][0]+1
        nexussheet.update_cell(row_select, col_select, '')
        col_select = lib['Priority'][0]+1
        nexussheet.update_cell(row_select, col_select, 'New')
        col_select = lib['Solved At'][0]+1
        nexussheet.update_cell(row_select, col_select, '')

        # update user of undosolve
        await ctx.channel.edit(name=ctx.channel.name.replace(self.mark,''))

            

            
        filepath = './misc/emotes/szeth.png'
        await ctx.send(content='Fixed.',file=discord.File(filepath))


    @commands.command(aliases=['note'])
    @commands.guild_only()
    async def update_nexus_note(self,ctx,*,query=None):
        """ update nexus row by flag of column name """

        if not await self.check_hunt_role(ctx):
            return

        if not query:
            await ctx.send('`!note backsolve` in appropriate channel')
            return

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        nexussheet = self.nexus_get_sheet(nexus_url)
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # select row of current channel
        # 1) assume command was run in correct channel
        # 2) assume channel ID exists in nexus 
        data_id = [item[lib['Channel ID'][0]] for item in data_all]
        row_select = data_id.index(str(ctx.channel.id))+1

        # update requested columns/fields
        puzzlename = data_all[row_select-1][lib['Puzzle Name'][0]]

        col_select = lib['Notes'][0]+1
        data_notes = [item[lib['Notes'][0]] for item in data_all[2:]]
        if data_notes[row_select-3]:
            nexussheet.update_cell(row_select, col_select, data_notes[row_select-3]+'; '+query)
        else:
            nexussheet.update_cell(row_select, col_select, query)

        await ctx.send('Updated column Notes for puzzle: {}'.format(puzzlename))




    @commands.command(aliases=['update'])
    @commands.guild_only()
    async def update_nexus(self,ctx,*,query=None):
        """ update nexus row by flag of column name """

        if not await self.check_hunt_role(ctx):
            return

        if not query:
            await ctx.send('`!update [-round=<>] [-number=<>] [-name=<>] [-priority=<>] [-notes=<>]` in appropriate channel')
            return

        # get dict of fields to be changed
        query = query.split('-')
        updatedict = {}
        for item in query:
            try:
                quer = item.split('=')
                updatedict[quer[0]] = quer[1]
            except:
                continue

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        nexussheet = self.nexus_get_sheet(nexus_url)
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # select row of current channel
        # 1) assume command was run in correct channel
        # 2) assume channel ID exists in nexus 
        data_id = [item[lib['Channel ID'][0]] for item in data_all]
        row_select = data_id.index(str(ctx.channel.id))+1

        # update requested columns/fields
        puzzlename = data_all[row_select-1][lib['Puzzle Name'][0]]
        for item in updatedict:

            if item == 'round':
                col_select = lib['Round'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item])
                await ctx.send('Updated column Round for puzzle: {}'.format(puzzlename))
            
            elif item == 'number':
                col_select = lib['Number'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item])
                await ctx.send('Updated column Number for puzzle: {}'.format(puzzlename))
            
            elif item == 'name':
                col_select = lib['Puzzle Name'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item])
                await self.channel_rename(ctx,ctx.channel,updatedict[item])
                await ctx.send('Updated column Name for puzzle: {}'.format(puzzlename))

            elif item == 'priority':
                col_select = lib['Priority'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item].title())
                await ctx.send('Updated column Priority for puzzle: {}'.format(puzzlename))

            elif item == 'notes':
                col_select = lib['Notes'][0]+1
                nexussheet.update_cell(row_select, col_select, updatedict[item])
                await ctx.send('Updated column Notes for puzzle: {}'.format(puzzlename))

            else:
                await ctx.send('Check key name. Column {} not updateable via bot.'.format(item))





    @commands.command(aliases=['check','checksetup'])
    @commands.guild_only()
    async def hunt_setup(self,ctx):
        """
        This awful sequence of checks and API calls presumably makes sure stuff won't break later
        """

        if not await self.check_hunt_role(ctx):
            return

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
            nexus_url = await self.nexus_get_url(ctx)
            nexussheet = self.nexus_get_sheet(nexus_url)
            checks['Nexus Sheet Access'] = ':+1:'
        except:
            checks['Nexus Sheet Access'] = ':x:'

        # nexus sheet check hardcoded columns
        try:
            data_all = nexussheet.get_all_values()
            headings = data_all[0]
            lib = self.nexus_sort_columns(headings)
            checks['Nexus Sheet Format'] = ':+1:'
        except:
            checks['Nexus Sheet Format'] = ':x:'

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
            description='Share hunt folder with\n`'+self.googledata['client_email']+'`\n')
        embed.add_field(name='Topic',value=topic,inline=True)
        embed.add_field(name='Status',value=status,inline=True)

        await ctx.send(embed=embed)








def setup(bot):
    bot.add_cog(PuzzCog(bot))

