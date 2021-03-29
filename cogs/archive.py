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

from gspread import WorksheetNotFound

from utils.db import DBase
from google.oauth2 import service_account


# A cog for archiving channels and categories
# !archive

class ArchiveCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.mark = '✅'
        # self.mark = '✔'

        # TODO: has to be a less silly way to organize this
        load_dotenv()
        self.key = os.getenv('GOOGLE_CLIENT_SECRETS')
        self.googledata = json.loads(self.key)
        self.googledata['private_key'] = self.googledata['private_key'].replace("\\n", "\n")
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = service_account.Credentials.from_service_account_info(self.googledata, scopes=scopes)

    def gclient(self):
        client = gspread.authorize(self.credentials)
        return client

    def channel_get_by_id(self, ctx, channelid):
        try:
            channel = discord.utils.get(ctx.guild.channels, id=channelid)
            return channel
        except:
            return False

    @commands.command(aliases=['arc'])
    @commands.guild_only()
    async def archive(self, ctx, *args):
        if len(args) != 2:
            await ctx.send('`!archive <channel|category> <sheet>`')
            return

        if args[0] == 'channel':
            await self.archive_channel(ctx.channel, args[1], True)
        elif args[0] == 'category' or args[0] == 'cat':
            await self.archive_category(ctx, args[1])
        else:
            await ctx.send('`!archive <channel|category> <sheet>`')

    async def archive_category(self, ctx, sheet_url):
        category = ctx.message.channel.category
        status = await ctx.message.channel.send('Archiving category {}...'.format(category))
        for channel in category.text_channels:
            await self.archive_channel(channel, sheet_url, False)
        await status.edit(content='Category {} archived!'.format(category))

    async def archive_channel(self, ctx, channel, sheet_url, log):
        status = await ctx.message.channel.send('Archiving channel {}...'.format(channel.mention))

        messages = []
        async for msg in channel.history(limit=None, oldest_first=True):
            messages.append([
                msg.created_at.strftime('%m-%d-%Y, %H:%M:%S'),
                msg.author.display_name,
                msg.clean_content
            ])
            for attachment in msg.attachments:
                messages.append([
                    '->',
                    '->',
                    '=IMAGE("' + attachment.url + '")'
                ])

        sheet_key = max(sheet_url.split('/'), key=len)
        gclient = self.gclient()
        wkbook = gclient.open_by_key(sheet_key)
        try:
            sheet = wkbook.worksheet(channel.name)
            sheet.delete_rows(1, sheet.row_count - 1)
            sheet.clear()
        except WorksheetNotFound:
            sheet = wkbook.add_worksheet(channel.name, 1, 3)
        resize_cols_request = {
            'requests': [{
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': sheet.id,
                        'dimension': "COLUMNS",
                        'startIndex': 0,
                        'endIndex': 3
                    }
                }
            }]
        }

        sheet.insert_rows(messages, value_input_option='USER_ENTERED')
        wkbook.batch_update(resize_cols_request)

        await status.edit(content='Channel {} archived!'.format(channel.mention))
        if not log:
            status.delete()

def setup(bot):
    bot.add_cog(ArchiveCog(bot))

