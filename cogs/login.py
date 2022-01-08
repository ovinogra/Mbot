# hunt.py
import discord
from discord.ext import commands, tasks
from utils.db import DBase
import datetime



# A cog for storing login info and google links for team
# !login
# !login update


class LoginCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    def get_flags(self):
        ''' return a dictionary with command vs sql flags '''

        # I could just format this by hand, but I'm lazy
        comfield = ['role','user','pswd','site','folder','nexus']
        sqlfield = ['hunt_role_id','hunt_username','hunt_password','hunt_url','hunt_folder','hunt_nexus']
        flags = {}
        for n in range(0,len(comfield)):
            flags[comfield[n]] = sqlfield[n]
        return flags

    def check_role(self,member,role):
        ''' member: ctx.author, role: integer discord ID '''

        return 
        #if isinstance(role,int):
        #    return discord.utils.get(member.roles, id=role)


    async def check_guild(self,ctx):
        ''' check that guild exists in db '''
        db = DBase(ctx)
        results = await db.hunt_get_row('Guild_id')
        if not results:
            await ctx.send('Not in this guild.')
        return results



    async def infofetch(self,ctx):        
        ''' fetch and display team login and links info '''
        
        query = 'hunt_url, hunt_username, hunt_password, hunt_folder, hunt_nexus, hunt_role_id'
        db = DBase(ctx)
        results = await db.hunt_get_row(query)
        if results == 0:
            await ctx.send('Unexpected error in database query? idk')
            return
        
        # parse results
        res = list(results)
        field1 = '**Website**: '+res[0]+'\n'
        field2 = '**Username**: '+res[1]+'\n'
        field3 = '**Password**: '+res[2]+'\n'
        if res[3].find('http') != -1:
            field4 = '**Folder**: [Link here]('+res[3]+')\n'
        else: 
            field4 = '**Folder**: '+res[3]+'\n'
        if res[4].find('http') != -1:
            field5 = '**Nexus**: [Link here]('+res[4]+')\n'
        else: 
            field5 = '**Nexus**: '+res[4]+'\n'
        final = field1+field2+field3+field4+field5
        role = res[5]

        # set up embed
        embed = discord.Embed(
                colour=discord.Colour.gold(),
                description=final
            )

        # role should be either 'none' or numeric ID       
        if role.lower() == 'none':
            embed.set_footer(text='Role: '+role)
            await ctx.send(embed=embed)
            return
        roleID = int(role)
        if self.check_role(ctx.author, roleID):
            roleName = discord.utils.get(ctx.guild.roles, id=roleID)
            embed.set_footer(text='Role: '+str(roleName))
            await ctx.send(embed=embed)
        else:
            await ctx.send('Missing role for the current hunt.')




    async def infoupdate(self,ctx,query):
        '''
        query: list of arguments to update in form ['field1=text1','field2=text2'] \n
        '''

        # parse argument flags
        flagdict = self.get_flags()
        updatestring = f""
        for item in query:
            field,value = item.split('=',1)
            if field not in flagdict:
                await ctx.send('Flag does not exist: '+field)
                return

            line = f""+flagdict[field]+" = '"+value+"'"

            if field == 'role':
                if value.lower() == 'none':
                    line += f", hunt_role = 'none'"
                else:
                    try:
                        roleID = int(value) 
                    except:
                        await ctx.send('Role must be either `none` or id number.')
                        return
                    roleName = discord.utils.get(ctx.guild.roles, id=roleID)
                    line += f", hunt_role = '"+str(roleName)+"'"
                
            if item != query[-1]:
                line += ", "
        
            updatestring += line

        # update db
        db = DBase(ctx)
        await db.hunt_update_row(updatestring)
            


    @commands.command(aliases=['info','login'])
    @commands.guild_only()
    async def huntinfo(self, ctx, *, query=None):
        helpstate = '`!login update '\
                    '[-role=<id>] [-user=<name>] [-pswd=<pswd>] [-site=<url>] [-folder=<url>] [-nexus=<url>]`'\
                        '\nNeed "Developer Mode" enabled on desktop to find role IDs.'

        if not await self.check_guild(ctx):
            return

        # fetch hunt info
        if not query:
            await self.infofetch(ctx)
            return

        # update hunt info
        quers = query.split(' -')
        if quers[0] in ['update','set']:
            
            # return help
            if len(quers) == 1:
                await ctx.send(helpstate)
                return

            await self.infoupdate(ctx,quers[1:])
            
        else:
            await ctx.send('I don\'t understand that...\n'+helpstate)







def setup(bot):
    bot.add_cog(LoginCog(bot))

