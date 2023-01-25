# puzzle.py
import asyncio

import discord
from discord import HTTPException
from discord.ext import commands
import gspread
import random
import numpy as np
from datetime import datetime, timedelta

from gspread import WorksheetNotFound

from utils.db2 import DBase
from utils.drive import Drive


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
        self.drive = Drive()
        self.logfeed = 1033881264895316119
        self.vc_delete_queue = []

    ### channel action functions
    async def channel_create(self,ctx,name,position,category=None):
        if not category:
            category = ctx.message.channel.category
        textchannnel = await category.create_text_channel(name=name,position=position)
        voicechannnel = await category.create_voice_channel(name=name,position=position)
        return [textchannnel,voicechannnel]

    async def channel_rename(self,ctx,channel,newname):
        channel.name = newname
        await channel.edit(name=newname)

    async def voice_channel_delayed_delete(self, ctx, vc, puzzlename, solve_message):
        # delete the vc after 2 minutes
        await asyncio.sleep(120)
        try:
            await discord.utils.get(ctx.guild.channels, id=vc).delete()
        except AttributeError:
            pass
        await solve_message.edit(content='`{}` marked as solved!'.format(puzzlename))


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


    def fetch_round_marker(self,ctx,wkbook,roundid=None,roundname=None):
        data_all = wkbook.get_worksheet(2).get_all_values()
        allroundnames = [item[0] for item in data_all[3:]]
        allroundidx = [item[1] for item in data_all[3:]]
        allroundmarker = [item[3] for item in data_all[3:]]
        if roundname:
            marker = allroundmarker[allroundnames.index(roundname)]
            return marker
        if roundid:
            marker = allroundmarker[allroundidx.index(str(roundid))]
            return marker


    ### nexus action functions
    async def nexus_get_url(self,ctx):
        db = DBase(ctx)
        res = db.hunt_get_row(ctx.guild.id)
        return res['hunt_nexus']

    def nexus_get_wkbook(self,url):
        nexus_key = max(url.split('/'),key=len)
        gclient = self.drive.gclient()
        wkbook = gclient.open_by_key(nexus_key)
        return wkbook

    def nexus_get_sheet(self,url):
        nexus_key = max(url.split('/'),key=len)
        gclient = self.drive.gclient()
        wkbook = gclient.open_by_key(nexus_key)
        sheet = wkbook.sheet1
        return sheet



    def nexus_sort_columns(self,headings):
        """
        this messy way ensures that order of columns in nexus does not matter, nor do new columns
        return a dict of column names with their indicies
        assume all in label_key exists in nexus
        """
        label_key = ['Channel ID','Voice Channel ID','Round','Number','Puzzle Name','Answer','Spreadsheet Link','Priority','Notes','Created At','Solved At']
        lib = {}
        for n in range(0,len(label_key)):
            label = label_key[n]
            index = int(headings.index(label))
            lib[label] = [index]

        return lib

    def nexus_add_round(self,wkbook,categoryobject,generalchannelobject,marker):
        """ add a row for the new round in third tab of nexus workbook """

        # fetch nexus data of rounds
        sheet = wkbook.get_worksheet(2)
        data_all = sheet.get_all_values()

        # new row for round
        temp = [categoryobject.name,str(categoryobject.id),str(generalchannelobject.id),marker]

        # append row to end of category/round list
        rownum = len(data_all)+1
        table_range = 'A'+str(rownum)+':'+gspread.utils.rowcol_to_a1(rownum,len(data_all[2]))
        sheet.append_row(temp,table_range=table_range)

    def nexus_add_puzzle(self,nexussheet,puzzlechannel,voicechannel,puzzlename,puzzlesheeturl,roundmarker,roundname):
        """ add channel id, puzzle name, link, priority=New """

        # fetch nexus data and sort headings
        data_all = nexussheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # new row for puzzle
        temp = ['' for item in range(0,len(headings))]
        temp[lib['Channel ID'][0]] = str(puzzlechannel.id)
        temp[lib['Voice Channel ID'][0]] = str(voicechannel.id)
        temp[lib['Priority'][0]] = 'New'
        temp[lib['Puzzle Name'][0]] = puzzlename
        temp[lib['Spreadsheet Link'][0]] = puzzlesheeturl
        if roundmarker:
            temp[lib['Round'][0]] = roundmarker

        # append row to end of nexus puzzle list
        rownum = len(data_all)+1
        table_range = 'A'+str(rownum)+':'+gspread.utils.rowcol_to_a1(rownum,len(headings))
        nexussheet.append_row(temp,table_range=table_range)

        col_select = lib['Created At'][0]+1
        nexussheet.update_cell(rownum, col_select, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))


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
        gclient = self.drive.gclient()
        newsheet = gclient.copy(template_key,title=puzzlename,copy_permissions=False)
        newsheet_url = "https://docs.google.com/spreadsheets/d/%s" % newsheet.id
        return newsheet_url

    # relies on column order in rounds sheet
    def get_round_name_from_marker(self, data, marker):
        for item in data[3:]:
            if marker == item[3]:
                return item[0]
        return 'Unsorted'

    async def send_log_message(self, ctx, msg):
        logchannel = discord.utils.get(ctx.guild.channels, id=self.logfeed)
        # if the log channel doesn't exist, just fail silently
        if logchannel is None:
            return
        await logchannel.send(msg)

    ##### begin bot commands #####

    @commands.command()
    async def bighelp(self,ctx,*,query=None):
        embed = discord.Embed(
            title='Commands for the puzzle manager',
            colour=discord.Colour.dark_grey(),
            description='All our puzzle data is summarized in a google sheet called `#Nexus`. '\
                'There are two types of bot commands: (1) those that show our info/progress and (2) those that update it. '\
                'Do **not** edit the Nexus directly unless you know what you are doing! Use these commands instead so everything is tracked consistently. '\
                'If you are new, then generally you only need to know `!login`, `!nexus`, and `!solve`. Ping an organizer if you are ever uncertain about a command :)'
        )
        embed.add_field(name='Display hunt/puzzle data',value=
            '`!login` to show our team info and drive links\n'\
            '`!nexus` to show all puzzles unlocked/solved\n'\
            '`!nexus -round=Round Name` to show puzzles from only one round\n'\
            '`!nexus -unsolved` to show only unsolved puzzles \n'\
            '`!listrounds` (`!rounds`) to show all hunt rounds \n'\
            '`!check` that bot is setup during pre-hunt period (mod only)\n'\
            ,inline=False)
        embed.add_field(name='Update hunt/puzzle data',value=
            '`!login update` to update our team info (mod only) \n'\
            '`!createround RoundName` to setup a category for a new round\n'\
            '`!createpuzzle PuzzName` (`!create`) to setup channel/sheet for a new puzzle\n'\
            '`!createpuzzle PuzzName -round=Round Name`\n'\
            '`!solve HERRING` to mark a puzzle as solved\n'\
            '`!undosolve` to unsolve a puzzle if you marked a solve in the wrong channel\n'\
            '`!note Backsolve` to leave any short solving notes about the puzzle\n'\
            '`!update [-round=<>] [-number=<>] [-name=<>] [-priority=<>] [-notes=<>]` to update a field in Nexus\n'\
            ,inline=False)
        await ctx.send(embed=embed)


    @commands.command()
    @commands.guild_only()
    async def nexus(self,ctx,*,query=None):
        """ 
        display list of puzzles and solutions
        can flag by round or unsolved 
        """

        async def send_nexus(nexus):
            try:
                await ctx.send(embed=nexus)
            except HTTPException:
                new_embed = discord.Embed(
                    title='Nexus Link',
                    colour=discord.Colour(0xfffff0),
                    url=nexus_url
                )
                new_embed.add_field(name="Note", value="Puzzle list exceeds character limit. Try using `-unsolved` or `-round=[round]` instead.")
                await ctx.send(embed=new_embed)

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        nexus_wkbook = self.nexus_get_wkbook(nexus_url)
        nexus_sheet = nexus_wkbook.get_worksheet(0)
        data_all = nexus_sheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # fetch nexus data of rounds
        round_sheet = nexus_wkbook.get_worksheet(2)
        round_data_all = round_sheet.get_all_values()
        
        # want: puzzle channel mention (linked), answer, round
        data_channel = [item[lib['Channel ID'][0]] for item in data_all[2:]]
        data_round = ['Unsorted' if item[lib['Round'][0]] == '' else item[lib['Round'][0]] for item in data_all[2:]]
        data_round_name = ['Unsorted' if item[lib['Round'][0]] == '' else self.get_round_name_from_marker(round_data_all, item[lib['Round'][0]]) for item in data_all[2:]]
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

        current_round_id = ctx.channel.category.id
        current_round_token = ''
        # check if current category is a round in the nexus
        if self.check_nexus_round_list(wkbook=nexus_wkbook, idtest=current_round_id):
            current_round_token = self.fetch_round_marker(ctx, wkbook=nexus_wkbook, roundid=current_round_id)
        # if not in a category and no flags specified, go for "all"
        elif not query:
            query = "-all"

        if query:
            if query == '-unsolved':
                names = ''
                for n in range(0,len(data_name)):
                    if data_answer[n] == '-':
                        names += data_round[n]+'-'+data_number[n]+': '+data_name[n]+'\n'
                embed.add_field(name='Unsolved',value=names,inline=True)
                await send_nexus(nexus=embed)
                return
            elif query == '-all':
                rounds = np.unique(data_round)
                for level in rounds:
                    names = ''
                    for n in range(0, len(data_name)):
                        if data_round[n] == level:
                            names += data_number[n] + ': ' + data_name[n] + ' (' + data_answer[n] + ')' + '\n'
                    embed.add_field(name='Round: ' + str(level), value=names, inline=False)
                await send_nexus(nexus=embed)
                return
            elif '-round=' in query:
                round_token = query.split('=')[1]
                if round_token in data_round or round_token in data_round_name:
                    current_round_token = round_token
                else:
                    await ctx.send('No such round found.')
            else:
                await ctx.send('Accepted flags: `-round=`, `-all`, or `-unsolved`')
                return

        names = ''
        for n in range(0, len(data_name)):
            if data_round[n] == current_round_token or data_round_name[n] == current_round_token:
                names += data_number[n] + ': ' + data_name[n] + ' (' + data_answer[n] + ')' + '\n'
        embed.add_field(name='Round: ' + current_round_token, value=names, inline=False)

        await send_nexus(nexus=embed)

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


    @commands.command(aliases=['createround','round'])
    @commands.guild_only()
    async def create_round(self, ctx, *, query=None):
        """ round creation script to 
        1) make category named by round
        2) make a general text channel
        3) make a voice channel
        4) add category id... somewhere in nexus?
        """

        if not query:
            await ctx.send('`!round Some Round Name Here -marker=marker`')
            return

        if '-marker=' in query:
            name, marker = query.split(' -marker=')
        else:
            await ctx.send('`!round Some Round Name Here -marker=marker`')
            return
        
        # fetch nexus data
        nexus_url = await self.nexus_get_url(ctx)
        nexuswkbook = self.nexus_get_wkbook(nexus_url)
        nexussheet = nexuswkbook.sheet1


        # check if round name exists in server
        # if self.check_server_category_list(ctx,name):
        #     await ctx.send('Round named `{}` already exists in server.'.format(name))
        #     return
        # check if round name exists in nexus
        if self.check_nexus_round_list(nexuswkbook,name):
            await ctx.send('Round named `{}` already exists in Nexus.'.format(name))
            return

        # do the round creation things
        newcategory = await ctx.guild.create_category(name)
        newchannnel = await newcategory.create_text_channel(name=marker+'-'+name+'-general')
        newvoicechannnel = await newcategory.create_voice_channel(name='ROUND: '+name)
        self.nexus_add_round(nexuswkbook,newcategory,newchannnel,marker)
        
        # send feedback on round creation
        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        await ctx.send(':orange_circle: Round created: `{}` ~~~ Create new puzzles in this round from {}'.format(newcategory,newchannnel.mention))
        await self.send_log_message(ctx, '['+dt_string+' EST] :orange_circle: Round created: `{}` ~~~ Create new puzzles in this round from {}'.format(newcategory,newchannnel.mention))
        



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
                roundmarker = self.fetch_round_marker(ctx,wkbook=nexuswkbook,roundname=roundname)
                pass
            else:
                await ctx.send('Round name `{}` does not exist in nexus. Please create it first using `!createround`'.format(roundname))
                return
        else:
            puzzlename = query
            roundname = ctx.channel.category.name
            roundid = ctx.channel.category.id
            # check if current category is a round in the nexus
            if self.check_nexus_round_list(wkbook=nexuswkbook,idtest=roundid):
                roundcategory = self.fetch_round_category(ctx,wkbook=nexuswkbook,roundid=roundid)
                roundmarker = self.fetch_round_marker(ctx,wkbook=nexuswkbook,roundid=roundid)
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
        newchannels = await self.channel_create(ctx,name=puzzlename,position=position,category=roundcategory)
        newsheet_url = self.puzzle_sheet_make(nexussheet,puzzlename)
        msg = await newchannels[0].send(newsheet_url)
        await msg.pin()
        self.nexus_add_puzzle(nexussheet=nexussheet,puzzlechannel=newchannels[0],voicechannel=newchannels[1],puzzlename=puzzlename,puzzlesheeturl=newsheet_url,roundmarker=roundmarker,roundname=roundname)
        

        # send final feedback 
        await infomsg.edit(content=':yellow_circle: Puzzle created: {} (Round: `{}`)'.format(newchannels[0].mention,roundname))
        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        await self.send_log_message(ctx, '['+dt_string+' EST] :yellow_circle: Puzzle created: {} (Round: `{}`)'.format(newchannels[0].mention,roundname))


    @commands.command(aliases=['multicreate'])
    @commands.guild_only()
    async def multicreate_puzzles(self, ctx, *, query=None):
        """ create multiple puzzles with one command """
        for puzz in query.splitlines():
            await self.create_puzzle(ctx, query=puzz)

    
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
        nexussheet.update_cell(row_select, col_select, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

        # update sheet to indicate solve
        col_select = lib['Puzzle Name'][0]
        puzzle_name = data_all[row_select - 1][col_select]
        col_select = lib['Spreadsheet Link'][0]
        puzzle_sheet = self.drive.gclient().open_by_url(data_all[row_select - 1][col_select])
        puzzle_sheet.update_title("SOLVED: " + puzzle_name)
        for wksheet in puzzle_sheet.worksheets():
            wksheet.update_tab_color({ "red": 0.0, "green": 1.0, "blue": 0.0 })
        try:
            puzzle_sheet.worksheet("MAIN").format("1:4", { "backgroundColor": { "red": 0.0, "green": 1.0, "blue": 0.0 } })
        except WorksheetNotFound:
            pass

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
        
        if self.mark not in ctx.channel.name:
            emote = random.choice(['gemheart','bang','face_explode','face_hearts','face_openmouth','face_party','face_stars','party','rocket','star','mbot','slug'])
            filepath = './misc/emotes/'+emote+'.png'
            solve_message = await ctx.send(content='`{}` marked as solved! Voice chat will be deleted in **2 minutes**.'.format(puzzlename),file=discord.File(filepath))
            await ctx.channel.edit(name=self.mark+ctx.channel.name)
            await self.send_log_message(ctx, '['+dt_string+' EST] :green_circle: Puzzle solved: {} (Round: `{}` ~ Answer: `{}`)'.format(ctx.message.channel.mention,ctx.message.channel.category,query.upper()))

            self.vc_delete_queue.append(
                (ctx.channel.id,
                 asyncio.create_task(self.voice_channel_delayed_delete(ctx, int(data_all[row_select - 1][lib['Voice Channel ID'][0]]), puzzlename, solve_message))))
        else:
            await ctx.send('Updated solution (again): {}'.format(puzzlename))

    @commands.command(aliases=['undosolve','unsolve','imessedup'])
    @commands.guild_only()
    async def undo_solve_puzzle(self, ctx):
        """ remove solved puzzle changes in nexus (in case !solve is run in the wrong channel) """

        # cancel VC deletion if necessary
        for vc in self.vc_delete_queue:
            if vc[0] == ctx.channel.id:
                vc[1].cancel()
                break

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

        # undo the coloring stuff
        col_select = lib['Puzzle Name'][0]
        puzzle_name = data_all[row_select - 1][col_select]
        col_select = lib['Spreadsheet Link'][0]
        puzzle_sheet = self.drive.gclient().open_by_url(data_all[row_select - 1][col_select])
        puzzle_sheet.update_title(puzzle_name.replace("SOLVED: ", ""))
        for wksheet in puzzle_sheet.worksheets():
            # sadly we can't actually unset the tab color with this
            # TODO call the API directly here
            wksheet.update_tab_color({ "red": 1.0, "green": 1.0, "blue": 1.0 })
        try:
            puzzle_sheet.worksheet("MAIN").format("1:4", { "backgroundColor": { "red": 1.0, "green": 1.0, "blue": 1.0 } })
        except WorksheetNotFound:
            pass

        # remake vc if necessary
        if discord.utils.get(ctx.guild.channels, id=int(data_all[row_select - 1][lib['Voice Channel ID'][0]])) is None:
            vc = await ctx.channel.category.create_voice_channel(name=puzzle_name)
            nexussheet.update_cell(row_select, lib['Voice Channel ID'][0]+1, str(vc.id))

        # update user of undosolve
        await ctx.channel.edit(name=ctx.channel.name.replace(self.mark,''))

        filepath = './misc/emotes/szeth.png'
        await ctx.send(content='Fixed.',file=discord.File(filepath))

        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        await self.send_log_message(ctx, '['+dt_string+' EST] Puzzle Unsolved: {} (Round: `{}`)'.format(ctx.message.channel.mention,ctx.message.channel.category))



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
                await self.channel_rename(ctx,ctx.guild.get_channel(int(data_all[row_select-1][lib['Voice Channel ID'][0]])),updatedict[item])
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
        db = DBase(ctx)
        res = db.hunt_get_row(ctx.guild.id)
        # res = list(results)
        checks['Google Folder'] = '[Link]('+res['hunt_folder']+')' if 'http' in res['hunt_folder'] else res['hunt_folder']
        checks['Nexus Sheet'] = '[Link]('+res['hunt_nexus']+')' if 'http' in res['hunt_nexus'] else res['hunt_nexus']

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
            gclient = self.drive.gclient()
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
            description='Share hunt folder with\n`'+self.drive.googledata['client_email']+'`\n')
        embed.add_field(name='Topic',value=topic,inline=True)
        embed.add_field(name='Status',value=status,inline=True)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(BigHuntCog(bot))

