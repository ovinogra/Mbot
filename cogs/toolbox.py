# toolbox.py
import discord
from discord.ext import commands
import re
import urllib.request
import mechanize


# A cog with useful commands/tools

class ToolboxCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['n','nut','nutr'])
    async def nutrimatic(self, ctx, *, query: str):
        number = 15
        query = query[:]
        if query[-1].isdigit() == True and query[-2].isspace() == True:
            number = int(query[-1:])
            query = query[0:-2]
        elif query[-2:].isdigit() == True and query[-3].isspace() == True:
            number = int(query[-2:])
            query = query[0:-3]
        elif query[-3:].isdigit() == True and query[-4].isspace() == True:
            number = int(query[-3:])
            query = query[0:-4]
        if number > 50:
            await ctx.send('There are too many solutions for my mushroom powered processing. Choose something smaller.')
        else: 
            query_initial = query[:]
            query = query.replace('&','%26').replace('+','%2B').replace('#','%23').replace(' ','+') # not optional
            url = 'https://nutrimatic.org/?q='+query+'&go=Go'
            text = urllib.request.urlopen(url).read()
            text1 = text.decode()
            if text1.find('No results found, sorry') != -1:
                final = 'Error: No results found at all :('
            elif text1.find('error: can\'t parse') != -1:
                final = 'Error: I cannot parse that :('
            else:
                posA = [m.start() for m in re.finditer('<span',text1)]
                posB = [m.start() for m in re.finditer('</span',text1)]
                final1 = []
                if len(posA) < number:
                    number = len(posA)
                    if text1.find('Computation') != -1:
                        final1 = 'Error: Computation limit reached'
                    if text1.find('No more results found') != -1:
                        final1 = 'Error: No more results found here'
                listnew = []
                sizenew = []
                final = []
                for n in range(0,number):
                    word = text1[posA[n]+36:posB[n]]
                    size = text1[posA[n]+23:posA[n]+32]
                    listnew.append(word)
                    sizenew.append(size)
                sizenew = [round(float(sizenew[n]),3) for n in range(0,len(sizenew))]
                sizenew = [round(float(sizenew[n]),3) for n in range(0,len(sizenew))]
                for n in range(0,number):
                    final.append(listnew[n]+"...................."+str(sizenew[n]))
                final = '\n'.join(final)
                if len(final1) != 0:
                    final = final+'\n'+final1
            embed = discord.Embed(
                title='Your nutrimatic link',
                url=url,
                description=final,
                colour=discord.Colour.magenta()
            )
            embed.set_footer(text='Query: '+query_initial)
            await ctx.send(embed=embed)


    @commands.command(aliases=['s','sub','substitution'])
    async def substitution_cipher(self, ctx, *, query: str):
        query_initial = query[:].upper()
        query = query.replace(' ','+')
        url = 'http://www.oneacross.com/cgi-bin/search_crypt.cgi?p0='+query+'&s=+Go+'
        text = urllib.request.urlopen(url).read()
        text1 = text.decode()
        posA = [m.end() for m in re.finditer('<tt>',text1)]
        posB = [m.start() for m in re.finditer('</tt>',text1)]
        final = []
        for n in range(0,len(posA)):
            final.append(text1[posA[n]:posB[n]])
        final = '\n'.join(final)
        embed = discord.Embed(
            title='Your substitution link',
            url=url,
            description=final,
            colour=discord.Colour.purple()
        )
        embed.set_footer(text='Query: '+query_initial)
        await ctx.send(embed=embed)


    def shift(self,query,cluenumber,final):
        tempq = 'a'*len(query)
        tempk = cluenumber
        for n in range(0,len(query)):
            num = ord(query[n])+tempk
            if num < 123:
                tempq = tempq[:n] + chr(num) + tempq[n+1:]
            else:
                tempq = tempq[:n] + chr(num-26) + tempq[n+1:]
        final.append(tempq)
        return final


    @commands.command(aliases=['cc','caesar'])
    async def caesar_cipher(self, ctx, *, query0: str):
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
        final = []
        if key > 25 or key < -1:
            final = 'Choose a key guess between 0 and 25'
        elif key > 0 and key < 26:
            self.shift(query,key,final)    
            final = '\n'.join(final).upper()
        elif key == 0:
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
            title='Caesar cipher answer(s)',
            description=final,
            colour=discord.Colour.dark_teal()
        )
        embed.set_footer(text='Query: {} \nKey: {}'.format(query0,key))
        await ctx.send(embed=embed)





def setup(bot):
    bot.add_cog(ToolboxCog(bot))