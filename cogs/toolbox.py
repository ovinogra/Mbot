# toolbox.py
import discord
from discord.ext import commands
import re
import urllib.request
import requests
import json
import numpy as np 
from utils.paginator import Pages


# A cog with useful commands/tools

class ToolboxCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=['n','nu','nut','nutr','nutri','nutrim','nutrima','nutrimat','nutrimati'])
    async def nutrimatic(self, ctx, *, query=None):

        if not query:
            await ctx.send('Example regex: `!nut "<asympote_>"`')
            return

        # get html page - TODO change to requests?
        query_initial = query[:]
        query = query_initial.replace('&','%26').replace('+','%2B').replace('#','%23').replace(' ','+') # html syntax
        url = 'https://nutrimatic.org/?q='+query+'&go=Go'
        text = urllib.request.urlopen(url).read()
        text1 = text.decode()

        # set up embed template
        embed = discord.Embed(title='Your nutrimatic link', url=url, colour=discord.Colour.magenta())
        embed.set_footer(text='Query: '+query_initial)

        # parse for solution list
        posA = [m.start() for m in re.finditer('<span',text1)]
        posB = [m.start() for m in re.finditer('</span',text1)]

        # check for no solutions, send error
        if not posA:
            final = 'None'
            errA = [m.start() for m in re.finditer('<b>',text1)]
            errB = [m.start() for m in re.finditer('</b>',text1)]
            final = text1[errA[-1]+3:errB[-1]]
            if final.find('font') != -1:
                errA = [m.start() for m in re.finditer('<font',text1)]
                errB = [m.start() for m in re.finditer('</font>',text1)]
                final = text1[errA[-1]+16:errB[-1]]
            embed.description = final
            await ctx.send(embed=embed)
            return

        # check for ending error message, usually bolded
        # max number of solutions on a nutrimatic page is 100
        finalend = None
        if len(posA) < 100:
            try:
                errA = [m.start() for m in re.finditer('<b>',text1)]
                errB = [m.start() for m in re.finditer('</b>',text1)]
                finalend = text1[errA[-1]+3:errB[-1]]
            except:
                pass

        # prep solution and weights for paginator
        solutions = []
        weights = []
        for n in range(0,min(len(posA),200)):
            word = text1[posA[n]+36:posB[n]]
            size = float(text1[posA[n]+23:posA[n]+32])
            solutions.append(word)
            weights.append(size)

        p = Pages(ctx,solutions=solutions,weights=weights,embedTemp=embed,endflag=finalend)
        await p.pageLoop()





    def shift_cc(self,wordin,key):
        wordout = list('a'*len(wordin))
        for n in range(0,len(wordout)):
            if wordin[n] == ' ':
                wordout[n] = ' '
            else: 
                numnew = ord(wordin[n])+key
                if numnew < 123:
                    wordout[n] = chr(numnew)
                else:
                    wordout[n] = chr(numnew-26)
        return ''.join(wordout)

    @commands.command(aliases=['cc','caesar'])
    async def caesar_cipher(self, ctx, *, query0=None):

        if not query0:
            await ctx.send('Example: `!cc irargvna` or `!cc qvntenz -key=13`')
            return 

        # parse input
        query0 = query0.lower()
        if '-key=' in query0:
            query,key = query0.split(' -key=')
            key = int(key)%26
        else: 
            query = query0
            key = []

        # do the shift(s)
        final = ''
        if key:
            wordout = self.shift_cc(query,key)
            final = str(key)+': '+wordout.upper()
        else:
            for key in range(1,26):
                wordout = self.shift_cc(query,key)
                final += str(key)+': '+wordout.upper()+'\n'

        await ctx.send(final)



    # TODO: does not work since quipqiup upgraded to beta3
    @commands.command()
    @commands.is_owner()
    async def quipqiup_beta2(self, ctx, *, query=None):

        if not query:
            await ctx.send('Example: `!qq cbg bfabdbebfab` or `!qq cbg bfabdbebfab c=s b=a`')
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
        print(obj)

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



    @commands.command(aliases=['alpha'])
    async def alpha_numeric(self, ctx, *, query=None):

        if not query:
            await ctx.send('Example: `!alpha ferROUs` or `!alpha 58 31 18 18 15 47 19` (includes mod26)')
            return

        #...why did I not use chr and ord?
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


    @commands.command(aliases=['atom'])
    async def periodic_table(self, ctx, *, query=None):

        if not query:
            await ctx.send('Example: `!atom 1 45 22 34 1212` or `!atom Ti Pt Ni` or `!atom Ti`')
            return

        def find_by_abbrev(element):
            # return atomic number of element, if exists
            idx = False
            for n in range(0,len(elementlist)):
                if elementlist[n] == element.title():
                    idx = n 
            return idx

        f = open('./misc/periodicTable.json','r')
        data = json.load(f)
        headings = data['0']
        headings.insert(0,'Atomic Number')

        # convert atomic number to element abbrev
        if query.replace(' ','').isnumeric():
            query = query.split(' ')
            collect = []
            for item in query:
                try:
                    collect.append(data[item][0])
                except:
                    collect.append('nan')
            final = ' '.join(collect)

        # convert element abbrev to atomic number
        else:
            elements = query.split(' ')
            elementlist = [item[0] for item in list(data.values())]

            final = []
            for element in elements:
                final.append(str(find_by_abbrev(element)))
            final = ' '.join(final)
                
            if len(elements) == 1 and final != False:
                dataout = data[final]
                dataout.insert(0,final)
                final = ''
                for n in range(0,len(headings)):
                    final += headings[n]+': '+str(dataout[n])+'\n'

        await ctx.send(final)



    @commands.command(aliases=['atbash','atb','ab'])
    async def atbash_cipher(self, ctx, *, query=None):

        if not query:
            await ctx.send('Example: `!atbash uVIiLfh`')
            return

        alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        key = ''.join(np.flipud(list(alpha)))
        final = []
        for letter in list(query.upper()):
            if letter == ' ':
                newletter = ' '
            else:
                newletter = key[alpha.find(letter)]
            final.append(newletter)
        final = ''.join(final)
        await ctx.send(final)



    @commands.command(aliases=['vig','v'])
    async def vigenere_cipher(self, ctx, *, query=None):

        if not query:
            await ctx.send('Example: `!v encrypt ferrous -key=lemon` or `!v decrypt QIDFBFW -key=lemon`')
            return

        # assume 0 indexing (A1Z26)
        def char_to_idx(letter):
            return ord(letter.lower()) - 97

        def idx_to_char(pos):
            return chr(pos + 97).upper()

        action = query.split(' ')[0]
        key = query.split('-key=')[1].upper()
        key = key * round(200/len(key))
        message = ' '.join(query.split(' ')[1:-1])

        final = ''
        if action == 'encrypt':
            for n in range(0,len(message)):
                newletter = idx_to_char((char_to_idx(message[n])+char_to_idx(key[n]))%26)
                final += newletter

        elif action == 'decrypt':
            for n in range(0,len(message)):
                newletter = idx_to_char((char_to_idx(message[n])-char_to_idx(key[n])+26)%26)
                final += newletter
        

        await ctx.send(final)


async def setup(bot):
    await bot.add_cog(ToolboxCog(bot))