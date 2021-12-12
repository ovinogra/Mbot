# puzzle.py

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import gspread
import random
import json
import numpy as np
from datetime import datetime, timedelta
from utils.db import DBase
from google.oauth2 import service_account


# This cog replaces 'hunt.py' for hunts where we care about organizing puzzles by round. 
# 'hunt.py' and 'bighunt.py' should not be run at the same time. Choose one. 

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



class BigHuntCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.mark = '✅'
        #self.mark = '✔'
        self.logfeed = 805502275107815466

        # import credentials
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

    ### channel action functions
    async def channel_create(self,ctx,name,position,category=None):
        if not category:
            category = ctx.message.channel.category        
        newchannnel = await category.create_text_channel(name=name,position=position)
        return newchannnel

    async def channel_rename(self,ctx,channel,newname):
        channel.name = newname
        await channel.edit(name=newname)




    ### check functions for puzzle or round name in nexus and server
    def check_nexus_round_list(self,wkbook,nametest=None,idtest=None):
        ''' bool: return [True] if round name exists in nexus '''

        data_all = wkbook.get_worksheet(2).get_all_values()
        if nametest:
            roundnames = [item[0] for item in data_all[3:]]
            if nametest in roundnames:
                return True
            else:
                return False
        if idtest:
            roundids = [item[1] for item in data_all[3:]]
            if str(idtest) in roundids:
                return True
            else:
                return False

    def check_nexus_puzzle_list(self,nexussheet,newpuzzle):
        ''' bool: return [True] if puzzle name exists in nexus '''

        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)
        data_name = [item[lib['Puzzle Name'][0]] for item in data_all[2:]]
        if newpuzzle in data_name:
            return True
        else:
            return False

    def check_server_category_list(self,ctx,name):
        ''' bool: return [True] if category/round name exists in server '''

        categoryall = ctx.guild.categories
        names = [item.name for item in categoryall]
        if name in names:
            return True
        else:
            return False

    def check_server_channel_list(self,ctx,name):
        ''' bool: return [True] if puzzle name exists in server '''

        channelall = ctx.message.channel.category.text_channels
        names = [item.name for item in channelall]
        if name in names:
            return True
        else:
            return False
        

    def fetch_round_category(self,ctx,wkbook,roundid=None,roundname=None):
        data_all = wkbook.get_worksheet(2).get_all_values()
        allroundnames = [item[0] for item in data_all[3:]]
        allroundidx = [item[1] for item in data_all[3:]]
        if roundname:
            category = discord.utils.get(ctx.guild.channels, id=int(allroundidx[allroundnames.index(roundname)]))
            return category
        if roundid:
            category = discord.utils.get(ctx.guild.channels, id=int(roundid))
            return category





    ### nexus action functions
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

    def nexus_get_wkbook(self,url):
        nexus_key = max(url.split('/'),key=len)
        gclient = self.gclient()
        wkbook = gclient.open_by_key(nexus_key)
        return wkbook

    def nexus_sort_columns(self,headings):
        """
        this messy way ensures that order of columns in nexus does not matter, nor do new columns
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

    def nexus_add_round(self,wkbook,categoryobject,generalchannelobject):
        """ add a row for the new round in third tab of nexus workbook """

        # fetch nexus data of rounds
        sheet = wkbook.get_worksheet(2)
        data_all = sheet.get_all_values()

        # new row for round
        temp = [categoryobject.name,str(categoryobject.id),str(generalchannelobject.id)]

        # append row to end of category/round list
        rownum = len(data_all)+1
        table_range = 'A'+str(rownum)+':'+gspread.utils.rowcol_to_a1(rownum,len(data_all[2]))
        sheet.append_row(temp,table_range=table_range)

    def nexus_add_puzzle(self,nexussheet,puzzlechannel,puzzlename,puzzlesheeturl,roundname):
        """ add channel id, puzzle name, link, priority=New """

        # fetch nexus data and sort headings
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # new row for puzzle
        temp = ['' for item in range(0,len(headings))]
        temp[lib['Channel ID'][0]] = str(puzzlechannel.id)
        temp[lib['Priority'][0]] = 'New'
        temp[lib['Puzzle Name'][0]] = puzzlename
        temp[lib['Spreadsheet Link'][0]] = puzzlesheeturl
        if roundname:
            temp[lib['Round'][0]] = roundname

        # append row to end of nexus puzzle list
        # TODO: appen row in correct round
        rownum = len(data_all)+1
        table_range = 'A'+str(rownum)+':'+gspread.utils.rowcol_to_a1(rownum,len(headings))
        nexussheet.append_row(temp,table_range=table_range)

        col_select = lib['Created At'][0]+1
        nexussheet.update_cell(rownum, col_select, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # @commands.command()
    # @commands.is_owner()
    # async def test(self,ctx):
    #     nexus_url = await self.nexus_get_url(ctx)
    #     wkbook = self.nexus_get_wkbook(nexus_url)
    #     data_all = wkbook.get_worksheet(2).get_all_values()
    #     roundname = [item[0] for item in data_all[3:]]
    #     roundid = [item[1] for item in data_all[3:]]

    #     print(roundname)
    #     print(roundid)




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


    ##### begin bot commands #####

    @commands.command()
    async def bighelp(self,ctx,*,query=None):
        embed = discord.Embed(
            title='Commands',
            colour=discord.Colour.dark_grey(),
            description='All our puzzle data is summarized in a google sheet called Nexus. '\
                'For the most part you should not have to edit it manually if these commands are used.'\
                ' Ping an organizer if you are ever uncertain about any of these :)'
        )
        embed.add_field(name='Puzzle Manager',value=
            '`!login` will show our team info and links\n'\
            '`!login update` to update our team info (mod only) \n'\
            '`!createround` will setup channels for a new round\n'\
            '`!createpuzzle` (`!create`) will setup channel/sheet for a new puzzle\n'\
            '`!createpuzzle Puzz Name -round=Round Name`\n'\
            '`!solve HERRING` will make a puzzle as solved\n'\
            '`!undosolve` if you messed up the channel?\n'\
            '`!note backsolve` to leave solving notes about the puzzle\n'\
            '`!listrounds` (`!rounds`) will show all rounds \n'\
            '`!nexus` will show all our progress\n'\
            '`!nexus -round=Round Name` show progress only from one round\n'\
            '`!nexus -unsolved` \n'\
            '`!check` bot setup during pre-hunt period (mod only)\n'\
            ,inline=True)
        await ctx.send(embed=embed)


    @commands.command()
    @commands.guild_only()
    async def nexus(self,ctx,*,query=None):
        """ 
        display list of puzzles and solutions
        can flag by round or unsolved 
        """

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

        # print('start')
        data_name = []
        for j, item in enumerate(data_channel):
            if item == '':
                data_name.append('-')
            else:
                try: 
                    channel = discord.utils.get(ctx.guild.channels, id=int(item))
                    data_name.append(channel.mention)
                except:
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

    @commands.command(aliases=['rounds','listround','listrounds'])
    @commands.guild_only()
    async def list_rounds(self,ctx,*,query=None):
        ''' list all rounds in nexus'''

        nexus_url = await self.nexus_get_url(ctx)
        data_all = self.nexus_get_wkbook(nexus_url).get_worksheet(2).get_all_values()

        embed = discord.Embed(
            title='Nexus Link',
            colour=discord.Colour(0xfffff0),
            url=nexus_url
        )

        roundnames = [item[0] for item in data_all[3:]]
        generalids = [item[2] for item in data_all[3:]]

        names = ''
        for idx,name in enumerate(roundnames):
            channel = discord.utils.get(ctx.guild.channels, id=int(generalids[idx]))
            names += name+': '+channel.mention+'\n'

        embed.add_field(name='All Rounds',value=names,inline=False)
        await ctx.send(embed=embed)


    @commands.command(aliases=['createround'])
    @commands.guild_only()
    async def create_round(self, ctx, *, query=None):
        """ round creation script to 
        1) make category named by round
        2) make a general text channel
        3) make a voice channel
        4) add category id... somewhere in nexus?
        """

        if not query:
            await ctx.send('`!round Some Round Name Here`')
            return
        
        # fetch nexus data
        nexus_url = await self.nexus_get_url(ctx)
        nexuswkbook = self.nexus_get_wkbook(nexus_url)
        nexussheet = nexuswkbook.sheet1

        # check if round name exists in server
        # if self.check_server_category_list(ctx,query):
        #     await ctx.send('Round named `{}` already exists in server.'.format(query))
        #     return
        # check if round name exists in nexus
        if self.check_nexus_round_list(nexuswkbook,query):
            await ctx.send('Round named `{}` already exists in Nexus.'.format(query))
            return

        # do the round creation things
        logchannel = discord.utils.get(ctx.guild.channels, id=self.logfeed)
        newcategory = await ctx.guild.create_category(query)
        newchannnel = await newcategory.create_text_channel(name=query+'-general')
        newvoicechannnel = await newcategory.create_voice_channel(name=query+'-general')
        self.nexus_add_round(nexuswkbook,newcategory,newchannnel)
        
        # send feedback on round creation
        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        await ctx.send(':green_circle: Round created: `{}` ~~~ Create new puzzles in this round from {}'.format(newcategory,newchannnel.mention))
        await logchannel.send('['+dt_string+' EST] :green_circle: Round created: `{}` ~~~ Create new puzzles in this round from {}'.format(newcategory,newchannnel.mention))
        



    @commands.command(aliases=['create','createpuzzle'])
    @commands.guild_only()
    async def create_puzzle(self, ctx, *, query=None):
        """ puzzle creation script to 
        1) make channel
        2) copy template sheet
        3) add nexus entry
        """

        if not query:
            await ctx.send('`!create Some Puzzle Name Here -round=1`')
            return

        nexus_url = await self.nexus_get_url(ctx)
        nexuswkbook = self.nexus_get_wkbook(nexus_url)


        if '-round=' in query:
            puzzlename, roundname = query.split(' -round=')
            # check if requested round exists in nexus, if it does assume the category exists
            if self.check_nexus_round_list(nexuswkbook,nametest=roundname):
                roundcategory = self.fetch_round_category(ctx,wkbook=nexuswkbook,roundname=roundname)
                pass
            else:
                await ctx.send('Round name `{}` does not exist in nexus. Please create it first using `!createround`'.format(roundname))
                return
        else:
            puzzlename = query
            roundname = ctx.channel.category.name
            roundid = ctx.channel.category.id
            print(roundid)
            # check if current category is a round in the nexus
            if self.check_nexus_round_list(wkbook=nexuswkbook,idtest=roundid):
                roundcategory = self.fetch_round_category(ctx,wkbook=nexuswkbook,roundid=roundid)
                pass
            else:
                await ctx.send('Cannot create a puzzle in this category. Current category `{}` is not a round. '.format(roundname))
                return
        
        nexussheet = nexuswkbook.sheet1

        # check existence of puzzle in channels and nexus
        if self.check_server_channel_list(ctx,puzzlename):
            await ctx.send('Channel named {} exists in current server.'.format(puzzlename))
            return
        if self.check_nexus_puzzle_list(nexussheet,puzzlename):
            await ctx.send('Puzzle named `{}` already exists in Nexus.'.format(puzzlename))
            return
        

        position = roundcategory.channels[0].position
        infomsg = await ctx.send('Creating puzzle `{}`'.format(puzzlename))

        # puzzle creation sequence
        newchannel = await self.channel_create(ctx,name=puzzlename,position=position,category=roundcategory)
        newsheet_url = self.puzzle_sheet_make(nexussheet,puzzlename)
        msg = await newchannel.send(newsheet_url)
        await msg.pin()
        self.nexus_add_puzzle(nexussheet=nexussheet,puzzlechannel=newchannel,puzzlename=puzzlename,puzzlesheeturl=newsheet_url,roundname=roundname)
        

        # send final feedback 
        await infomsg.edit(content=':yellow_circle: Puzzle created: {} (Round: `{}`)'.format(newchannel.mention,roundname))
        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        logchannel = discord.utils.get(ctx.guild.channels, id=self.logfeed)
        await logchannel.send('['+dt_string+' EST] :yellow_circle: Puzzle created: {} (Round: `{}`)'.format(newchannel.mention,roundname))




    
    @commands.command(aliases=['solve'])
    @commands.guild_only()
    async def solve_puzzle(self, ctx, *, query=None):
        """ update puzzle in nexus with answer and solved priority """

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
        nexussheet.update_cell(row_select, col_select, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # move channel down
        channels = ctx.message.channel.category.channels
        idx = channels[-2].position+1 # note the change due to voice channel in category
        # print(channels)
        # print('')
        for channel in channels:
            # print(channel.name)
            # print(channel.position)
            if self.mark in channel.name:
                idx = channel.position 
                break
        await ctx.channel.edit(position=idx)

        # update user of solve
        puzzlename = data_all[row_select-1][lib['Puzzle Name'][0]]
        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        logchannel = discord.utils.get(ctx.guild.channels, id=self.logfeed)
        
        if self.mark not in ctx.channel.name:
            emote = random.choice(['gemheart','bang','face_explode','face_hearts','face_openmouth','face_party','face_stars','party','rocket','star','mbot','slug'])
            filepath = './misc/emotes/'+emote+'.png'
            await ctx.send(content='`{}` marked as solved!'.format(puzzlename),file=discord.File(filepath))
            await ctx.channel.edit(name=self.mark+ctx.channel.name)
            await logchannel.send('['+dt_string+' EST] :tada: Puzzle solved: {} (Round: `{}`)'.format(ctx.message.channel.mention,ctx.message.channel.category))
        else:
            await ctx.send('Updated solution (again): {}'.format(puzzlename))
        


            
    

    @commands.command(aliases=['undosolve','imessedup'])
    @commands.guild_only()
    async def undo_solve_puzzle(self, ctx):
        """ remove solved puzzle changes in nexus (in case !solve is run in the wrong channel) """

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

        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        logchannel = discord.utils.get(ctx.guild.channels, id=self.logfeed)
        await logchannel.send('['+dt_string+' EST] Puzzle UNsolved: {} (Round: `{}`)'.format(ctx.message.channel.mention,ctx.message.channel.category))



    @commands.command(aliases=['note'])
    @commands.guild_only()
    async def update_nexus_note(self,ctx,*,query=None):
        """ update nexus row by flag of column name """

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
    bot.add_cog(BigHuntCog(bot))

