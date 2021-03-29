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
    async def archive(self, ctx, *, query=None):
        await ctx.send('archive active')

def setup(bot):
    bot.add_cog(ArchiveCog(bot))

