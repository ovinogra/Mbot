# toolbox.py
import discord
from discord.ext import commands
import re
import urllib.request
import requests
import json
import mechanize
from utils.paginator import Pages


# A cog with useful commands/tools

class ToolboxCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=['n','nu','nut','nutr','nutri','nutrim','nutrima','nutrimat','nutrimati'])
    async def nutrimatic(self, ctx, *, query=None):

        if not query:
            await ctx.send('Send `!nut input` with the same **input** as you would use on nutrimatic.org\nExample: `!nut "<asympote_>"`')
            return

        # get html page - TODO change requests to aiohttp?
        query_initial = query[:]
        query = query_initial.replace('&','%26').replace('+','%2B').replace('#','%23').replace(' ','+') # html syntax
        url = 'https://nutrimatic.org/?q='+query+'&go=Go'
        text = urllib.request.urlopen(url).read()
        text1 = text.decode()

        # set up embed template
        embed = discord.Embed(title='Your nutrimatic link', url=url, colour=discord.Colour.magenta())
        embed.set_footer(text='Query: '+query_initial)

        # parse error messages
        if text1.find('No results found, sorry') != -1:
            final = 'Error: No results found at all :('
            embed.description(final)
            await ctx.send(embed=embed)
            return

        if text1.find('error: can\'t parse') != -1:
            final = 'Error: I cannot parse that :('
            embed.description(final)
            await ctx.send(embed=embed)
            return

        
        finalend = []
        if text1.find('Computation') != -1:
            finalend = 'Error: Computation limit reached'
        if text1.find('No more results found') != -1:
            finalend = 'Error: No more results found here'

        # compile solution list
        posA = [m.start() for m in re.finditer('<span',text1)]
        posB = [m.start() for m in re.finditer('</span',text1)]
        solutions = []
        weights = []
        for n in range(0,min(len(posA),200)):
            word = text1[posA[n]+36:posB[n]]
            size = float(text1[posA[n]+23:posA[n]+32])
            solutions.append(word)
            weights.append(size)

        if finalend:
            p = Pages(ctx,solutions=solutions,weights=weights,embedTemp=embed,endflag=finalend)
        else:
            p = Pages(ctx,solutions=solutions,weights=weights,embedTemp=embed)
        
        await p.pageLoop()




    def shift(self,query,cluenumber,final):
        tempq = 'a'*len(query)
        tempk = cluenumber
        for n in range(0,len(query)):
            if query[n] == ' ':
                tempq = tempq[:n] + ' ' + tempq[n+1:]
            else: 
                num = ord(query[n])+tempk
                if num < 123:
                    tempq = tempq[:n] + chr(num) + tempq[n+1:]
                else:
                    tempq = tempq[:n] + chr(num-26) + tempq[n+1:]
        final.append(tempq)
        return final


    @commands.command(aliases=['cc','caesar'])
    async def caesar_cipher(self, ctx, *, query0=None):

        if not query0:
            await ctx.send('Send `!cc input key` with a text **input** with an optional **key** shift between 1 to 25 or in the form of `x=y` (or choose 0 to guess a key)\n'\
                'Example: `!cc irargvna` or `!cc qvntenz 13` or `!cc qvntenz q=d`')
            return 

        # set up query - TODO fix the mess
        query0 = query0.lower()
        if query0[-1:].isnumeric() == True and query0[-2].isspace() == True:
            query = query0[:-2]
            key = int(query0[-1:])
        elif query0[-2:].isnumeric() == True and query0[-3].isspace() == True:
            query = query0[:-3]
            key = int(query0[-2:])
        elif query0[-2] == '=':
            cluefrom = query0[-3]
            clueto = query0[-1]
            query = query0[:-4]
            key = int(abs(ord(clueto)-ord(cluefrom)))
        else:
            query = query0
            key = -1
        
        # extract result
        final = []
        if key > 25 or key < -1:
            final = 'Choose a key between 1 and 25 or choose 0 for function to guess a key.'
        elif key > 0 and key < 26:
            self.shift(query,key,final)    
            final = '\n'.join(final).upper()
        elif key == 0:

            # TODO replace mechanize, with aiohttp?
            br = mechanize.Browser() 
            url = 'https://www.xarg.org/tools/caesar-cipher/'
            br.open(url)
            br.select_form(nr=0)
            br.form['text'] = query
            br.form['key'] = [str(key)]
            response = br.submit().read().decode("utf-8") 
            key = list(br.forms())[0].get_value('key')
            key = key[0]
            start = response.find('Output')
            end = response.find('</p>',start)
            final = response[start+22:end].upper()
        else:
            for m in range(0,26):
                self.shift(query,m,final)
            final = '\n'.join(final).upper()
        embed = discord.Embed(
            title='Caesar cipher',
            description=final,
            colour=discord.Colour.dark_teal()
        )
        embed.set_footer(text='Query: {} \nKey: {}'.format(query,key))
        await ctx.send(embed=embed)



    @commands.command(aliases=['qq'])
    async def quipqiup(self, ctx, *, query=None):

        if not query:
            await ctx.send('Send `!qq input key` with an **input** same as you would use on quipqiup.com with optional **key(s)** in the form of `x=y n=m`.\n'\
                'Example: `!qq cbg bfabdbebfab` or `!qq cbg bfabdbebfab c=s b=a`')
            return

        # set up query
        clues = ''
        poseq = [m.start() for m in re.finditer('=',query)]
        if poseq:
            clues = query[poseq[0]-1:]
            query = query[:poseq[0]-2]

        # data scrapper adapted from
        # https://github.com/cmpunches/NSA-CryptoChallenge-Solver/blob/340ba7f65072bf00bdc2a4d0cc313d50e3ba6070/cryptochallenge-solver.py
        client = requests.Session()
        client.headers.update({
            'Accept-Encoding': "gzip, deflate, br",
            'Referer': "https://quipqiup.com/",
            'Content-type': "application/x-www-form-urlencoded",
            'Origin': "https://quipqiup.com/"
        })
        body = {"ciphertext": query,"clues": clues,"time": 5}
        rawresult = client.post("https://6n9n93nlr5.execute-api.us-east-1.amazonaws.com/prod/dict",json.dumps(body)).content
        obj = json.loads(rawresult.decode())

        # set up embed template
        embed = discord.Embed(title='Quipqiup',colour=discord.Colour.dark_orange())
        if clues:
            embed.set_footer(text='Query: '+query+'\nKey: '+clues)
        elif not clues:
            embed.set_footer(text='Query: '+query)
        
        # send result
        if 'errorMessage' in obj:
            final = 'Exited with error message: \n'+obj['errorMessage']
            embed.description(final)
            await ctx.send(embed=embed)

        else:
            solnsort = sorted(obj['solutions'], key=lambda k: k['logp'], reverse=True)
            solns = []
            weights = []
            for n in range(0,len(solnsort)):
                solns.append(solnsort[n]['plaintext'])
                weights.append(solnsort[n]['logp'])
            p = Pages(ctx,solutions=solns,weights=weights,embedTemp=embed)
            await p.pageLoop()



    @commands.command(aliases=['letnum','let'])
    async def letternumber(self, ctx, *, query=None):

        if not query:
            await ctx.send('Send `!letnum input` with an **input** of either letters or numbers. Space separation needed for numeric input.\nExample: `!let ferROUs` or `!let 58 31 18 18 15 47 19`')
            return

        alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        final = []
        if query[0].isnumeric():
            query = query.split(' ')
            for n in range(0,len(query)):
                data = int(query[n])%26
                if data == 0:
                    data = 26
                data = alpha[data-1]
                final.append(data)
            final = ''.join(final)
        else:
            query = query[:].upper().replace(' ','')
            for n in range(0,len(query)):
                data = query[n]
                pos = alpha.find(data)
                final.append(str(pos+1))
            final = ' '.join(final)
        await ctx.send(final)



def setup(bot):
    bot.add_cog(ToolboxCog(bot))