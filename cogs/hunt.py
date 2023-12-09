# puzzle.py
import asyncio

import discord
from discord import HTTPException
from discord.ext import commands
import gspread
import random
import numpy as np
from datetime import datetime, timedelta

from dotenv import load_dotenv
from matplotlib import pyplot
import io
import math
import time

from utils.db2 import DBase
from utils.drive import Drive
import os


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


class HuntCog(commands.Cog):

    def __init__(self, bot):
        load_dotenv()
        self.bot = bot
        self.mark = '✅'
        self.drive = Drive()
        self.vc_delete_queue = []

    # discord management functions

    def channel_get_by_id(self,ctx,channelid):
        try:
            channel = discord.utils.get(ctx.guild.channels, id=channelid)
            return channel
        except:
            return False

    def check_category_channel_list(self, ctx, name):
        ''' check if channel name already exists in current category '''

        category = ctx.message.channel.category
        channelall = category.text_channels
        names = [item.name for item in channelall]
        if name in names:
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

    async def channel_create(self,ctx,name,position,category=None):
        if not category:
            category = ctx.message.channel.category
        textchannnel = await category.create_text_channel(name=name,position=position)
        voicechannnel = await category.create_voice_channel(name=name,position=position) if self.is_bighunt(ctx) else None
        return [textchannnel,voicechannnel]

    async def channel_rename(self,ctx,channel,newname):
        channel.name = newname
        await channel.edit(name=newname)

    async def channel_delete(self,ctx,channelid):
        channel = ctx.guild.get_channel(int(channelid))
        await channel.delete()

    async def voice_channel_delayed_delete(self, ctx, vc, puzzlename, solve_message):
        # delete the vc after 2 minutes
        await asyncio.sleep(120)
        try:
            await discord.utils.get(ctx.guild.channels, id=vc).delete()
        except AttributeError:
            pass
        await solve_message.edit(content='`{}` marked as solved!'.format(puzzlename))

    async def send_log_message(self, ctx, msg):
        db = DBase(ctx)
        logchannel = discord.utils.get(ctx.guild.channels, id=int(db.hunt_get_row(ctx.guild.id, ctx.message.channel.category.id)['hunt_logfeed']))
        # if the log channel doesn't exist, just fail silently
        if logchannel is None:
            return
        await logchannel.send(msg)

    # nexus management functions

    def is_bighunt(self, ctx):
        return DBase(ctx).hunt_get_row(ctx.guild.id, ctx.message.channel.category.id)['is_bighunt'] or False

    def check_nexus_round_list(self, round_data, nametest=None, idtest=None):
        ''' bool: return [True] if round name exists in nexus '''

        if nametest:
            roundnames = [item[0] for item in round_data[3:]]
            if nametest in roundnames:
                return True
            else:
                return False
        if idtest:
            roundids = [item[1] for item in round_data[3:]]
            if str(idtest) in roundids:
                return True
            else:
                return False

    def check_nexus_puzzle_list(self, nexus_data, newpuzzle):
        ''' check if puzzle name already exists in nexus '''

        headings = nexus_data[0]
        lib = self.nexus_sort_columns(headings)

        data_name = [item[lib['Puzzle Name'][0]] for item in nexus_data[2:]]
        if newpuzzle in data_name:
            return True
        else:
            return False

    async def get_hunt_role_id(self,ctx):
        db = DBase(ctx)
        try:
            res = db.hunt_get_row(ctx.guild.id, ctx.message.channel.category.id)
        except Exception as e:
            await ctx.send(str(e))
            return False

        if res['hunt_role_id'] == 'none' and not self.is_bighunt(ctx):
            await ctx.send('Update the role id in the login info.')
            return False
        else:
            roleid = int(res['hunt_role_id'])
            return roleid


    async def check_hunt_role(self,ctx):
        ''' check if user has role for current hunt '''

        db = DBase(ctx)
        try:
            res = db.hunt_get_row(ctx.guild.id, ctx.message.channel.category.id)
        except Exception as e:
            await ctx.send(str(e))
            return False

        # res = list(results)
        # no hunt role set
        if res['hunt_role_id'] == 'none':
            return True
        else:
            roleid = int(res['hunt_role_id'])
            status = discord.utils.get(ctx.author.roles, id=roleid)
            # role is not correct
            if not status:
                await ctx.send('Missing role for current hunt. ')
                return False
            # role is correct
            else: 
                return True

    def fetch_round_category(self, ctx, round_data, roundid=None, roundname=None):
        allroundnames = [item[0] for item in round_data[3:]]
        allroundidx = [item[1] for item in round_data[3:]]
        if roundname:
            category = discord.utils.get(ctx.guild.channels, id=int(allroundidx[allroundnames.index(roundname)]))
            return category
        if roundid:
            category = discord.utils.get(ctx.guild.channels, id=int(roundid))
            return category

    def fetch_round_marker(self, ctx, round_data, roundid=None, roundname=None):
        allroundnames = [item[0] for item in round_data[3:]]
        allroundidx = [item[1] for item in round_data[3:]]
        allroundmarker = [item[3] for item in round_data[3:]]
        if roundname:
            marker = allroundmarker[allroundnames.index(roundname)]
            return marker
        if roundid:
            marker = allroundmarker[allroundidx.index(str(roundid))]
            return marker

    # relies on column order in rounds sheet
    def get_round_name_from_marker(self, data, marker):
        for item in data[3:]:
            if marker == item[3]:
                return item[0]
        return 'Unsorted'

    async def nexus_get_url(self,ctx):
        db = DBase(ctx)
        try:
            res = db.hunt_get_row(ctx.guild.id, ctx.message.channel.category.id)
        except Exception as e:
            await ctx.send(str(e))
            return False
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
        make nexus column order independent
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

    def nexus_add_round(self, sheet, round_data, categoryobject, generalchannelobject, marker):
        """ add a row for the new round in third tab of nexus workbook """

        # new row for round
        temp = [categoryobject.name,str(categoryobject.id),str(generalchannelobject.id),marker]

        # append row to end of category/round list
        rownum = len(round_data)+1
        table_range = 'A'+str(rownum)+':'+gspread.utils.rowcol_to_a1(rownum,len(round_data[2]))
        sheet.append_row(temp,table_range=table_range)

    def nexus_add_puzzle(self, ctx, nexussheet, nexus_data, puzzlechannel, voicechannel, puzzlename, puzzlesheeturl, roundmarker):
        """ add channel id, puzzle name, link, priority=New """

        # sort headings
        headings = nexus_data[0]
        lib = self.nexus_sort_columns(headings)

        # new row for puzzle
        temp = ['' for item in range(0,len(headings))]
        temp[lib['Channel ID'][0]] = str(puzzlechannel.id)
        if self.is_bighunt(ctx):
            temp[lib['Voice Channel ID'][0]] = str(voicechannel.id)
        temp[lib['Priority'][0]] = 'New'
        temp[lib['Puzzle Name'][0]] = puzzlename
        temp[lib['Spreadsheet Link'][0]] = puzzlesheeturl
        temp[lib['Created At'][0]] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if roundmarker:
            temp[lib['Round'][0]] = roundmarker

        # append row to end of nexus puzzle list
        rownum = len(nexus_data)+1
        table_range = 'A'+str(rownum)+':'+gspread.utils.rowcol_to_a1(rownum,len(headings))
        nexussheet.append_row(temp,table_range=table_range)

    def puzzle_sheet_make(self,nexus_data,puzzlename):
        """ copy template sheet from link in Nexus and return link to new sheet """

        # sort headings
        headings = nexus_data[0]
        lib = self.nexus_sort_columns(headings)
        
        # assume template url is in ROW 2 under Spreadsheet Link
        template_url = nexus_data[1][lib['Spreadsheet Link'][0]]
        template_key = max(template_url.split('/'),key=len)

        # make copy of template sheet
        gclient = self.drive.gclient()
        newsheet = gclient.copy(template_key,title=puzzlename, copy_permissions=False)
        newsheet_url = "https://docs.google.com/spreadsheets/d/%s" % newsheet.id
        return newsheet_url

    def make_hunt_nexus(self, hunt_name, hunt_folder):
        hunt_folder_id = max(hunt_folder.split('/'), key=len)
        hunt_folder_id = hunt_folder_id.split('?')[0]
        nexus_id = os.getenv('BASE_NEXUS_ID') if os.getenv('BASE_NEXUS_ID') is not None else '1JssBgYG4w5YXVn9MFLlv4vvzT8UiGnj5h35YdvPyTus'
        template_id = os.getenv('BASE_TEMPLATE_ID') if os.getenv('BASE_TEMPLATE_ID') is not None else '1n8zCDjLHC8p1R2Jw_c3TDaNOpip52fZhVtNqA1hU9bg'
        nexus = self.drive.gclient().copy(nexus_id, title='#NEXUS ' + hunt_name, folder_id=hunt_folder_id, copy_permissions=False)
        template = self.drive.gclient().copy(template_id, title='#TEMPLATE ' + hunt_name, folder_id=hunt_folder_id, copy_permissions=False)
        nexus.get_worksheet(0).update('G2', 'https://docs.google.com/spreadsheets/d/%s' % template.id)
        return 'https://docs.google.com/spreadsheets/d/%s' % nexus.id

    # begin bot commands #

    @commands.command()
    async def help(self,ctx,*,query=None):
        if not self.is_bighunt(ctx):
            embed = discord.Embed(
                title='Commands',
                colour=discord.Colour.dark_grey(),
                description='Generally you only need the basic functions. Typing a command will usually give more details for it. '
            )
            embed.add_field(name=' Basic Functions',value=
                '`!login`\n'\
                '`!nexus [-unsolved]`\n'\
                '`!create Puzzle Name`\n'\
                '`!solve ANSWER`\n',inline=False)
            embed.add_field(name='Other Functions',value=
                '`!multicreate [Puzzle Names (split by line)]`\n'\
                '`!note [backsolve]`\n'\
                '`!update [-name=New Puzzle Name]`\n'\
                '`!undosolve`\n'\
                '`!graph [fill]`\n'\
                'Admin: `!login update`, `!checksetup`, `!bighunt`, `!stat`, `!rmc check`, `!arc`',inline=False)
            embed.add_field(name='Tools',value=
                '`!n`: Nutrimatic; `!cc`: Caesar; `!vig`: Vigenere; `!alpha`: A1Z26; `!atbash`: atbash; `!atom`: Elements\n'\
                '`!tag topic`: Cheatsheets and links (topic=braille,morse,etc)',inline=False)
            embed.add_field(name='Fun',value='`!sz`, `!flip`, `!dice [N S]`, `engage`, talk to M-Bot :)',inline=False)
            embed.set_footer(text='https://github.com/Moonrise55/Mbot')
            await ctx.send(embed=embed)
        else: 
            embed = discord.Embed(
                title='Commands',
                colour=discord.Colour.dark_grey(),
                description='All our solving data is summarized in a google sheet called `#Nexus`. Do **not** edit it directly. '\
                'Generally you only need the basic functions. Typing a command will usually give more details for it, but ask if you are uncertain about anything :) '
            )
            embed.add_field(name=' Basic Functions',value=
                '`!login` to show our team info and drive links\n'\
                '`!nexus` to show all puzzles list\n'\
                '`!createround Round Name -marker=:emoji:` to setup category for a new round\n'\
                '`!create Puzzle Name` to setup channel/sheet for a new puzzle (use in the general channel for the correct round!)\n'\
                '`!solve ANSWER` to mark a puzzle as solved\n',inline=False)
            embed.add_field(name='Other Functions',value=
                '`!nexus -unsolved` to show only unsolved puzzles \n'\
                '`!nexus -round=Round Name` to show puzzles from only one round\n'\
                '`!listrounds` (`!rounds`) to show all hunt rounds \n'\
                '`!multicreate [Puzzle Names (split by line)]`\n'\
                '`!note backsolve` to leave short solving notes about the puzzle\n'\
                '`!update [-name=Name]` to update a field in Nexus\n'\
                '`!undosolve` in case you marked the wrong puzzle solved\n'\
                '`!graph [fill]` to generate a progress graph\n'\
                'Admin: `!login update`, `!checksetup`, `!bighunt`, `!stat`',inline=False)
            embed.add_field(name='Tools',value=
                '`!n`: Nutrimatic; `!cc`: Caesar; `!vig`: Vigenere; `!alpha`: A1Z26; `!atbash`: atbash; `!atom`: Elements\n'\
                '`!tag topic`: Cheatsheets and links (topic=braille,morse,etc)',inline=False)
            embed.add_field(name='Fun',value='`!iihy`, `!sz`, `!flip`, `!dice [N S]`, `engage`, talk to M-Bot :)',inline=False)
            embed.set_footer(text='https://github.com/Moonrise55/Mbot')
            await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def nexus(self,ctx,*,query=None):
        """ 
        display list of puzzles and solutions
        can flag by round or unsolved 
        """

        if not await self.check_hunt_role(ctx):
            return

        async def send_nexus(nexus):
            try:
                await ctx.send(embed=nexus)
            except HTTPException:
                new_embed = discord.Embed(
                    title='Nexus Link',
                    colour=discord.Colour(0xfffff0),
                    url=nexus_url
                )
                new_embed.add_field(name="Note",
                                    value="Puzzle list exceeds the Discord character limit. Try using `-unsolved` or `-round=[round]` instead.")
                await ctx.send(embed=new_embed)

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        if not nexus_url:
            return
        nexus_wkbook = self.nexus_get_wkbook(nexus_url)
        nexus_sheet = nexus_wkbook.get_worksheet(0)
        data_all = nexus_sheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        round_sheet = None
        round_data = None
        if self.is_bighunt(ctx):
            # fetch nexus data of rounds
            round_sheet = nexus_wkbook.get_worksheet(2)
            round_data = round_sheet.get_all_values()

        # want: puzzle channel mention (linked), answer, round
        data_channel = [item[lib['Channel ID'][0]] for item in data_all[2:]]
        data_round = ['Unsorted' if item[lib['Round'][0]] == '' else item[lib['Round'][0]] for item in data_all[2:]]
        data_round_name = ['Unsorted' if item[lib['Round'][0]] == '' else item[lib['Round'][0]] if not self.is_bighunt(ctx)
            else self.get_round_name_from_marker(round_data, item[lib['Round'][0]]) for item in data_all[2:]]
        data_number = ['-' if item[lib['Number'][0]] == '' else item[lib['Number'][0]] for item in data_all[2:]]
        data_answer = ['-' if item[lib['Answer'][0]] == '' else item[lib['Answer'][0]] for item in data_all[2:]]

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
            for n in range(0, len(data_channel)):
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

        current_round_token = ''
        if self.is_bighunt(ctx):
            # check if current category is a round in the nexus
            current_round_id = ctx.channel.category.id
            if self.check_nexus_round_list(round_data=round_data, idtest=current_round_id):
                current_round_token = self.fetch_round_marker(ctx, round_data=round_data, roundid=current_round_id)
            # if not in a category and no flags specified, go for "all"
            elif not query:
                query = "-all"
        # if hunt is not a bighunt and no flags specified, also go for "all"
        elif not query:
            query = "-all"

        if query:
            if query == '-unsolved':
                names = ''
                for n in range(0, len(data_name)):
                    if data_answer[n] == '-':
                        names += data_round[n] + '-' + data_number[n] + ': ' + data_name[n] + '\n'
                embed.add_field(name='Unsolved', value=names, inline=True)
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

        # this block will be reached if -round is in the query OR if no flags are used in a bighunt category
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

        if not self.is_bighunt(ctx):
            await ctx.send("This command is only available in bighunt mode.")

        nexus_url = await self.nexus_get_url(ctx)
        if not nexus_url:
            return
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

    @commands.command(aliases=['createround', 'round'])
    @commands.guild_only()
    async def create_round(self, ctx, *, query=None):
        """ round creation script to
        1) make category named by round
        2) make a general text channel
        3) make a voice channel
        4) add category id... somewhere in nexus?
        """

        if not self.is_bighunt(ctx):
            await ctx.send("This command is only available in bighunt mode.")
            return

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
        if not nexus_url:
            return
        nexuswkbook = self.nexus_get_wkbook(nexus_url)
        nexussheet = nexuswkbook.sheet1
        round_sheet = nexuswkbook.get_worksheet(2)
        round_data = round_sheet.get_all_values()

        # check if round name exists in server
        # if self.check_server_category_list(ctx,name):
        #     await ctx.send('Round named `{}` already exists in server.'.format(name))
        #     return
        # check if round name exists in nexus
        if self.check_nexus_round_list(round_data, name):
            await ctx.send('Round named `{}` already exists in Nexus.'.format(name))
            return

        db = DBase(ctx)
        hunt_infos = db.hunt_get_row(ctx.guild.id, ctx.message.channel.category.id)
        # do the round creation things
        roleid = await self.get_hunt_role_id(ctx)
        log_channel = discord.utils.get(ctx.guild.channels, id=int(hunt_infos['hunt_logfeed']))
        if log_channel is not None:
            position = log_channel.category.position
        else:
            position = ctx.message.channel.category.position
        if roleid != "none":
            rolehunt = discord.utils.get(ctx.guild.roles, id=roleid)
            botmember = self.bot.user
            overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
                    rolehunt: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True),
                    botmember: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True,connect=True,manage_messages=True)
                    }
            newcategory = await ctx.guild.create_category(name,overwrites=overwrites,position=position)
        else:
            newcategory = await ctx.guild.create_category(name,position=position)
        newchannnel = await newcategory.create_text_channel(name=marker + '-' + name + '-general')
        newvoicechannnel = await newcategory.create_voice_channel(name='ROUND: ' + name)
        self.nexus_add_round(round_sheet, round_data, newcategory, newchannnel, marker)

        await db.round_insert_row(ctx.guild.id, newcategory.id, hunt_infos['hunt_category_id'])

        # send feedback on round creation
        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        await ctx.send(':orange_circle: Round created: `{}` ~~~ Create new puzzles in this round from {}'.format(newcategory, newchannnel.mention))
        await self.send_log_message(ctx, '[' + dt_string + ' EST] :orange_circle: Round created: `{}` ~~~ Create new puzzles in this round from {}'.format(newcategory, newchannnel.mention))

    @commands.command(aliases=['create','createpuzzle'])
    @commands.guild_only()
    async def create_puzzle(self, ctx, *, query=None, is_multi=False):
        """ puzzle creation script to
        1) make channel
        2) copy template sheet
        3) add nexus entry
        """

        if not query:
            await ctx.send('`!create Some Puzzle Name Here -round=1`')
            return False

        nexus_url = await self.nexus_get_url(ctx)
        if not nexus_url:
            return
        nexuswkbook = self.nexus_get_wkbook(nexus_url)
        roundcategory = None
        roundmarker = None

        round_data = nexuswkbook.get_worksheet(2).get_all_values()
        if '-round=' in query:
            puzzlename, roundname = query.split(' -round=')
            if self.is_bighunt(ctx):
                # check if requested round exists in nexus, if it does assume the category exists
                if self.check_nexus_round_list(round_data, nametest=roundname):
                    roundcategory = self.fetch_round_category(ctx, round_data=round_data, roundname=roundname)
                    roundmarker = self.fetch_round_marker(ctx, round_data=round_data, roundname=roundname)
                else:
                    await ctx.send('Round name `{}` does not exist in nexus. Please create it first using `!createround`'.format(roundname))
                    return False
        elif self.is_bighunt(ctx):
            puzzlename = query
            roundname = ctx.channel.category.name
            roundid = ctx.channel.category.id
            # check if current category is a round in the nexus
            if self.check_nexus_round_list(round_data=round_data, idtest=roundid):
                roundcategory = self.fetch_round_category(ctx, round_data=round_data, roundid=roundid)
                roundmarker = self.fetch_round_marker(ctx, round_data=round_data, roundid=roundid)
                pass
            else:
                await ctx.send(
                    'Cannot create a puzzle in this category. Current category `{}` is not a round. '.format(roundname))
                return False
        else:
            puzzlename = query
            roundname = None

        nexus_sheet = nexuswkbook.sheet1
        nexus_data = nexus_sheet.get_all_values()

        # check existence of puzzle in channels and nexus
        if not self.is_bighunt(ctx) and self.check_category_channel_list(ctx, puzzlename):
            await ctx.send('Channel named `{}` already exists in current category.'.format(puzzlename))
            return False
        elif self.is_bighunt(ctx) and self.check_server_channel_list(ctx, puzzlename):
            await ctx.send('Channel named `{}` already exists in current server.'.format(puzzlename))
            return False
        if self.check_nexus_puzzle_list(nexus_data, puzzlename):
            await ctx.send('Puzzle named `{}` already exists in Nexus.'.format(puzzlename))
            return False

        position = roundcategory.channels[0].position if self.is_bighunt(ctx) else ctx.message.channel.category.channels[0].position
        if not is_multi:
            infomsg = await ctx.send(':yellow_circle: Creating puzzle `{}`'.format(puzzlename))

        # puzzle creation sequence
        newchannels = await self.channel_create(ctx, name=puzzlename, position=position, category=roundcategory)
        newsheet_url = self.puzzle_sheet_make(nexus_data, puzzlename)
        msg = await newchannels[0].send(newsheet_url)
        await msg.pin()
        self.nexus_add_puzzle(nexussheet=nexus_sheet, ctx=ctx, nexus_data=nexus_data, puzzlechannel=newchannels[0], voicechannel=newchannels[1], puzzlename=puzzlename, puzzlesheeturl=newsheet_url, roundmarker=roundmarker)

        # send final feedback
        if not is_multi:
            if self.is_bighunt(ctx):
                await infomsg.edit(content=':yellow_circle: Puzzle created: {} (Round: `{}`)'.format(newchannels[0].mention, roundname))
                now = datetime.utcnow() - timedelta(hours=5)
                dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
                await self.send_log_message(ctx, '[' + dt_string + ' EST] :yellow_circle: Puzzle created: {} (Round: `{}`)'.format(newchannels[0].mention, roundname))
            else:
                await infomsg.edit(content=':yellow_circle: Puzzle created: {}'.format(newchannels[0].mention))

        return [newchannels[0].mention, roundname]

    @commands.command(aliases=['multicreate'])
    @commands.guild_only()
    async def multicreate_puzzles(self, ctx, *, query=None):
        """ create multiple puzzles with one command """
        lines = query.splitlines()
        info_content = [':yellow_circle: Creating puzzle `{}`'.format(line.split('-round=')[0]) for line in lines]
        infomsg = await ctx.send('\n'.join(info_content))
        rets = [await self.create_puzzle(ctx, query=line, is_multi=True) for line in lines]
        msg_edit = []
        log_message = []
        now = datetime.utcnow() - timedelta(hours=5)
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        for i in range(len(info_content)):
            if self.is_bighunt(ctx):
                msg_edit.append(':yellow_circle: Puzzle created: {} (Round: `{}`)'.format(rets[i][0], rets[i][1]) if rets[i] else info_content[i])
                # no original status in log channel -- just ignore if failed
                if rets[i]:
                    log_message.append('[' + dt_string + ' EST] :yellow_circle: Puzzle created: {} (Round: `{}`)'.format(rets[i][0], rets[i][1]))
            else:
                msg_edit.append(':yellow_circle: Puzzle created: {}'.format(rets[i][0]) if rets[i] else info_content[i])
        await infomsg.edit(content='\n'.join(msg_edit))
        if self.is_bighunt(ctx):
            await self.send_log_message(ctx, '\n'.join(log_message))

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
        if not nexus_url:
            return
        nexus_sheet = self.nexus_get_sheet(nexus_url)
        data_all = nexus_sheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # update column of choice (row_select) in correct row
        # 1) assume command was run in correct channel
        # 2) assume channel ID exists in nexus 
        data_id = [item[lib['Channel ID'][0]] for item in data_all]
        row_select = data_id.index(str(ctx.channel.id))+1
        edit_row = "A" + str(row_select) + ":" + gspread.utils.rowcol_to_a1(row_select, len(headings))
        row_data = nexus_sheet.get(edit_row)
        col_select = lib['Answer'][0]
        row_data[0][col_select] = query.upper()
        col_select = lib['Priority'][0]
        row_data[0][col_select] = 'Solved'
        col_select = lib['Solved At'][0]
        time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        try:
            row_data[0][col_select] = time
        except IndexError:
            row_data[0].append(time)
        nexus_sheet.update(edit_row, row_data)

        # update sheet to indicate solve
        col_select = lib['Puzzle Name'][0]
        puzzle_name = data_all[row_select - 1][col_select]
        col_select = lib['Spreadsheet Link'][0]
        puzzle_sheet = self.drive.gclient().open_by_url(data_all[row_select - 1][col_select])
        tabs = puzzle_sheet.worksheets()
        requests = [{
            "updateSheetProperties": {
                "properties": {
                    "sheetId": tab.id,
                    "tabColor": {
                        "red": 0.0,
                        "green": 1.0,
                        "blue": 0.0
                    }
                },
                "fields": "tabColor"
            }
        } for tab in tabs]
        requests.append({
            "updateSpreadsheetProperties": {
                "properties": {
                    "title": "SOLVED: " + puzzle_name
                },
                "fields": "title"
            }
        })
        for tab in tabs:
            if tab.title.upper() == "MAIN":
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": tab.id,
                            "startRowIndex": 0,
                            "endRowIndex": 4,
                            "startColumnIndex": 0
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.0,
                                    "green": 1.0,
                                    "blue": 0.0
                                }
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                })
        puzzle_sheet.batch_update({"requests": requests})

        # prepare to move channel down
        channels = ctx.message.channel.category.channels
        idx = channels[-2 if self.is_bighunt(ctx) else -1].position+1
        for channel in channels:
            if self.mark in channel.name:
                idx = channel.position 
                break

        # update user of solve
        puzzlename = data_all[row_select - 1][lib['Puzzle Name'][0]]
        if self.mark not in ctx.channel.name:
            emote = random.choice(
                ['gemheart', 'bang', 'face_explode', 'face_hearts', 'face_openmouth', 'face_party', 'face_stars',
                 'party', 'rocket', 'star', 'mbot', 'slug'])
            filepath = './misc/emotes/' + emote + '.png'
            solve_message = await ctx.send(content=('`{}` marked as solved!' + (' Voice chat will be deleted in **2 minutes**.' if self.is_bighunt(ctx) else '')).format(puzzlename), file=discord.File(filepath))
            await ctx.channel.edit(name=self.mark + ctx.channel.name, position=idx)

            if self.is_bighunt(ctx):
                now = datetime.utcnow() - timedelta(hours=5)
                dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
                await self.send_log_message(ctx, '[' + dt_string + ' EST] :green_circle: Puzzle solved: {} (Round: `{}` ~ Answer: `{}`)'.format(ctx.message.channel.mention, ctx.message.channel.category, query.upper()))
                deletion = (ctx.channel.id,
                            asyncio.create_task(self.voice_channel_delayed_delete(ctx, int(
                                data_all[row_select - 1][lib['Voice Channel ID'][0]]), puzzlename, solve_message)))
                self.vc_delete_queue.append(deletion)
                await deletion[1]
                self.vc_delete_queue.remove(deletion)

        else:
            await ctx.send('Updated solution (again): {}'.format(puzzlename))

    @commands.command(aliases=['undosolve','imessedup','unsolve'])
    @commands.guild_only()
    async def undo_solve_puzzle(self, ctx):
        """ remove solved puzzle changes in nexus (in case !solve is run in the wrong channel) """

        if not await self.check_hunt_role(ctx):
            return

        # cancel VC deletion if necessary
        if self.is_bighunt(ctx):
            for vc in self.vc_delete_queue:
                if vc[0] == ctx.channel.id:
                    vc[1].cancel()
                    self.vc_delete_queue.remove(vc)
                    break

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        if not nexus_url:
            return
        nexus_sheet = self.nexus_get_sheet(nexus_url)
        data_all = nexus_sheet.get_all_values()
        headings = data_all[0]
        lib = self.nexus_sort_columns(headings)

        # update column of choice (row_select) in correct row
        # assume channel ID exists in nexus 
        data_id = [item[lib['Channel ID'][0]] for item in data_all]
        row_select = data_id.index(str(ctx.channel.id))+1
        edit_row = "A" + str(row_select) + ":" + gspread.utils.rowcol_to_a1(row_select, len(headings))
        row_data = nexus_sheet.get(edit_row)
        col_select = lib['Answer'][0]
        row_data[0][col_select] = ''
        col_select = lib['Priority'][0]
        row_data[0][col_select] = 'New'
        col_select = lib['Solved At'][0]
        row_data[0][col_select] = ''
        nexus_sheet.update(edit_row, row_data)

        # undo the coloring stuff
        col_select = lib['Puzzle Name'][0]
        puzzle_name = data_all[row_select - 1][col_select]
        col_select = lib['Spreadsheet Link'][0]
        puzzle_sheet = self.drive.gclient().open_by_url(data_all[row_select - 1][col_select])
        tabs = puzzle_sheet.worksheets()
        requests = [{
            "updateSheetProperties": {
                "properties": {
                    "sheetId": tab.id
                },
                "fields": "tabColor"
            }
        } for tab in tabs]
        requests.append({
            "updateSpreadsheetProperties": {
                "properties": {
                    "title": puzzle_name
                },
                "fields": "title"
            }
        })
        for tab in tabs:
            if tab.title.upper() == "MAIN":
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": tab.id,
                            "startRowIndex": 0,
                            "endRowIndex": 4,
                            "startColumnIndex": 0
                        },
                        "cell": {
                            "userEnteredFormat": {}
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                })
        puzzle_sheet.batch_update({"requests": requests})

        # remake vc if necessary
        if self.is_bighunt(ctx) and discord.utils.get(ctx.guild.channels, id=int(data_all[row_select - 1][lib['Voice Channel ID'][0]])) is None:
            vc = await ctx.channel.category.create_voice_channel(name=puzzle_name)
            # this is a separate api edit request, but it should be infrequent enough not to matter
            nexus_sheet.update_cell(row_select, lib['Voice Channel ID'][0]+1, str(vc.id))

        # update user of undosolve
        await ctx.channel.edit(name=ctx.channel.name.replace(self.mark,''))
        filepath = './misc/emotes/szeth.png'
        await ctx.send(content='Fixed.',file=discord.File(filepath))

        if self.is_bighunt(ctx):
            now = datetime.utcnow() - timedelta(hours=5)
            dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
            await self.send_log_message(ctx, '[' + dt_string + ' EST] Puzzle Unsolved: {} (Round: `{}`)'.format(ctx.message.channel.mention, ctx.message.channel.category))

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
        if not nexus_url:
            return
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

    @commands.command(aliases=['unnote', 'undonote', 'removenote'])
    @commands.guild_only()
    async def remove_nexus_note(self,ctx,*,query=None):
        """ update nexus row by flag of column name """

        if not await self.check_hunt_role(ctx):
            return

        # fetch nexus data and sort headings
        nexus_url = await self.nexus_get_url(ctx)
        if not nexus_url:
            return
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
            notes = data_notes[row_select-3].split(';')
            notes.pop()
            nexussheet.update_cell(row_select, col_select, '; '.join(notes))
            await ctx.send('Removed last note from puzzle: {}'.format(puzzlename))
        else:
            await ctx.send('No notes to remove from puzzle: {}'.format(puzzlename))

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
        if not nexus_url:
            return
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
        db = DBase(ctx)
        try:
            res = db.hunt_get_row(ctx.guild.id, ctx.message.channel.category.id)
        except Exception as e:
            await ctx.send(str(e))
            return
        # res = list(results)
        checks['Google Folder'] = '[Link]('+res['hunt_folder']+')' if 'http' in res['hunt_folder'] else res['hunt_folder']
        checks['Nexus Sheet'] = '[Link]('+res['hunt_nexus']+')' if 'http' in res['hunt_nexus'] else res['hunt_nexus']

        # nexus sheet check API call
        try:
            nexus_url = await self.nexus_get_url(ctx)
            if not nexus_url:
                return
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

    @commands.command(aliases=['graph', 'solvegraph'])
    @commands.guild_only()
    async def generate_solve_graph(self, ctx, *, query=None):
        # fetch solve data
        try:
            team_name = DBase(ctx).hunt_get_row(ctx.guild.id, ctx.message.channel.category.id)['hunt_team_name']
        except Exception as e:
            await ctx.send(str(e))
            return
        nexus_url = await self.nexus_get_url(ctx)
        if not nexus_url:
            return
        nexus_sheet = self.nexus_get_sheet(nexus_url)
        nexus_data = nexus_sheet.get_all_values()
        headings = nexus_data[0]
        lib = self.nexus_sort_columns(headings)
        create_times = [item[lib['Created At'][0]] for item in nexus_data[2:]]
        solve_times = [item[lib['Solved At'][0]] for item in nexus_data[2:]]

        def dt_str_to_ms(dt_str):
            try:
                return time.mktime(datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').timetuple())
            except ValueError:
                return -1

        create_ms = list(filter(lambda h: h != -1, [dt_str_to_ms(dt_str) for dt_str in create_times]))
        hunt_start_ms = min(create_ms)

        def dt_str_to_hours(dt_str):
            solve_ms = dt_str_to_ms(dt_str)
            if solve_ms == -1:
                return -1
            return (solve_ms - hunt_start_ms) / 3600

        # generate x-axis values
        solve_hours = list(filter(lambda h: h != -1, [dt_str_to_hours(dt_str) for dt_str in solve_times]))
        solve_hours.sort()
        solve_hours.insert(0, 0.0)
        max_x = math.ceil(solve_hours[len(solve_hours) - 1] + (solve_hours[len(solve_hours) - 1] / 25))
        solve_hours.append(max_x)

        # generate the graph
        font = {
            'family': 'serif',
            'color': 'black',
            'weight': 'normal',
            'size': 16,
        }
        fig = pyplot.figure(figsize=(14, 7))
        plot = fig.subplots()
        plot.set_title(ctx.message.channel.category.name + ' Solves (' + team_name + ')', fontdict=font)
        plot.set_xlabel("Hours", fontdict=font)
        plot.set_ylabel("Solves", fontdict=font)
        if query == '-fill' or query == 'fill':
            plot.fill_between(solve_hours, list(range(0, len(solve_hours) - 1)) + [len(solve_hours) - 2], color='#e8bfff', step='post')
        plot.step(solve_hours, list(range(0, len(solve_hours) - 1)) + [len(solve_hours) - 2], color='#e8bfff', linewidth=2.5, where='post')
        plot.set_xlim(left=0.0, right=max_x)
        plot.set_ylim(bottom=0.0, top=len(create_ms))

        # send it to a byte buffer for messaging
        buf = io.BytesIO()
        fig.savefig(buf, bbox_inches='tight')
        buf.seek(0)
        await ctx.send(file=discord.File(fp=buf, filename="solve_graph.png"))

    @commands.command(aliases=['hunt', 'createhunt'])
    @commands.guild_only()
    async def create_hunt(self, ctx, *, query=None):
        """ hunt creation script to
        1) make category
        2) copy nexus and template sheets
        """

        if not query or ('-role=' not in query and '-bighunt' not in query) or '-folder' not in query:
            await ctx.send('Usage: `!createhunt <huntname> -folder=<folder> -role=<roleid> [-bighunt] [-logfeed=<logfeedid>]`')
            return False

        query_parts = query.split(' -')
        hunt_name = query_parts[0]
        hunt_role_id = ''
        hunt_folder = ''
        is_bighunt = False
        logfeed_id = '0'
        for part in query_parts[1:]:
            if part.startswith('role'):
                hunt_role_id = part.split('=')[1]
            elif part.startswith('folder'):
                hunt_folder = part.split('=')[1]
            elif part.startswith('bighunt'):
                is_bighunt = True
            elif part.startswith('logfeed'):
                logfeed_id = part.split('=')[1]
        info_msg = await ctx.send(':orange_circle: Creating hunt `{}`...'.format(hunt_name))

        position = ctx.message.channel.category.position
        hunt_role = discord.utils.get(ctx.guild.roles, id=int(hunt_role_id))
        bot_member = self.bot.user
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
            hunt_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True),
            bot_member: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, connect=True, manage_messages=True)
        }
        hunt_category = await ctx.guild.create_category(hunt_name, overwrites=overwrites, position=position)
        hunt_channel = await hunt_category.create_text_channel(hunt_name + '-discussion')
        await hunt_category.create_voice_channel(name=hunt_name + ' VC')

        nexus_url = self.make_hunt_nexus(hunt_name, hunt_folder)
        db = DBase(ctx)
        await db.hunt_insert_row(ctx.guild.id, hunt_category.id, hunt_role_id, hunt_folder, nexus_url, is_bighunt, logfeed_id)

        nexus_msg = await hunt_channel.send('Nexus sheet: {}'.format(nexus_url))
        await nexus_msg.pin()

        await info_msg.edit(content=':orange_circle: Hunt created: {}'.format(hunt_channel.mention))
        return


async def setup(bot):
    await bot.add_cog(HuntCog(bot))

