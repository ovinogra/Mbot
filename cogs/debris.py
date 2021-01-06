# debris.py
import discord
from discord.ext import commands
import re
import numpy as np 
import time
import asyncio
import random


'''
A cog with a text adventure with five minipuzzles, made mostly for practice because I was bored. Requires some cosmere knowledge. 
Yes, code is a mess but making it was fun.  
Command is `engage cytonic hyperdrive` or just `engage`
'''


class DebrisCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.world = None
        self.mapkey = None
        self.mapzone = None
        self.timeout = None
        self.moon = None
        self.missionanswer = None
        self.masteranswer = 'OPHIUCHUS'


    def getMap(self, filename):
            with open(filename,'r') as f:
                rows = f.readlines()
            mapkey = []
            for n in range(0,len(rows)):
                mapkey.append(rows[n].split('\t'))
                mapkey[n][-1] = mapkey[n][-1].replace('\n','')
            r,c = np.shape(mapkey)
            for i in range(0,r):
                for j in range(0,c):
                    if mapkey[i][j] == 'Start':
                        r0 = i
                        c0 = j
            return mapkey, r0, c0


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        MoonID = '<@416656299661459458>'

        
        # Master tile organization function

        async def game(r,c):
            if r == 'cancel':
                await stop(r)
            elif r == 'correct':
                await stop(r)
            elif r == 'timer':
                await stop(r)
            else: 
                newTile = getTile(r,c)
                if newTile == 'Start':
                    r,c = await Start(r,c)
                    await game(r,c)
                elif newTile == 'Space':
                    r,c = await Space(r,c)
                    await game(r,c)
                elif newTile == 'Ship':
                    r,c = await Ship(r,c)
                    await game(r,c)
                elif newTile == 'Haven':
                    r,c = await Haven(r,c)
                    await game(r,c)
                elif newTile[:5] == 'Color':
                    r,c = await Color(r,c,newTile)
                    await game(r,c)
                elif newTile == 'Debris':
                    await stop('debris')
                elif newTile == 'Zone':
                    r,c = await Zone(r,c)
                    await game(r,c)
                elif newTile == 'Light':
                    r,c = await LightMatter(r,c)
                    await game(r,c)
                elif newTile == 'Dark':
                    r,c = await DarkMatter(r,c)
                    await game(r,c)
                elif newTile == 'Select':
                    r,c = await Select(r,c)
                    await game(r,c)
                elif newTile == 'Kress':
                    await Kress(r,c)
                    r,c = await checkanswermission(r,c)
                    await game(r,c)
                elif newTile == '0':
                    await stop('krell')


        # Map tile functions (need to be customized for each map notation)

        async def Start(r,c):
            if self.world == 'sel':
                prompt = 'I hear these space zones are full of Krell spaceships. Maybe we can learn something from their formations. '\
                    'Though you will have to fly fast! You have '+str(self.timeout)+' seconds to decide each movement, otherwise the Krell will catch us!'\
                    '\nWhich direction do you want to go?'
            elif self.world == 'roshar':
                prompt = 'I hear the heart of Roshar is occupied by strange entities, maybe we can find some and meet them? At least my maps are complete here. '\
                    'Krell could still sneak up on us so let\'s not use more than '+str(self.timeout)+' seconds per movement.\nWhich direction do you want to go?'
            elif self.world == 'nalthis':
                prompt = 'Ooh there are some very colorful planets and stars here! Let\'s find our way between all of them. '\
                    'Remember, every movement counts in avoiding the Krell! Do not use more than '+str(self.timeout)+' seconds per movement.'\
                    '\nWhich direction do you want to go?'
            elif self.world == 'taldain':
                prompt = 'I am picking up uneven distributions of ordinary and dark matter. These tendrils of matter are connected but no 4 zones are the same. '\
                    'But my sensors keep jamming up :strawberry: so I cannot get a good read on each space zone. Maybe you can figure out the rest? '\
                    'I really want to know what is at the undiscovered tips. You have '+str(self.timeout)+' seconds per movement.'\
                    '\nWhich direction do you want to go?'
            elif self.world == 'scadrial':
                prompt = 'We start floating in a vastless space. Too bad my database got damaged and the map is incomplete. Maybe you can deduce the rest. '\
                    'To avoid the Krell, let\'s use no more than '+str(self.timeout)+' seconds for each movement.'\
                    '\nWhich direction do you want to go?'
            debug(r,c)
            await message.channel.send(prompt)
            direction = await self.bot.wait_for('message',check=check,timeout=None)
            r,c = stepxy(r,c,direction.content)
            return r,c

        async def Kress(r,c):
            prompt = '[no timer] Hey look, there\'s a planet! Hmm, no Krell around here. My database recognizes it as Kress. '\
                'I want to explore it, but we need a password to land. Do you know it? Or we can continue flying. '\
                'If you want to try answering, send **P: YOURANSWER**. \nOtherwise, which direction do you want to go?'
            if self.world in ['roshar','taldain']:
                zonefetch = self.mapzone[r][c].upper()
                prompt = prompt+'\nBy the way, we are in space zone **'+str(zonefetch)+'**.' 
            await message.channel.send(prompt)

        async def Space(r,c):
            preprompt = [   'We see featureless space in all directions. ',\
                            'We are hurling through boring space. ',\
                            'All this empty space is mesmerizing... ',\
                            'Empty space is the perfect place to think about our place in life. ',\
                            'Here we are! No, false alarm. Still featureless space everywhere. ']
            prompt = random.choice(preprompt)+'\nWhich direction do you want to go?'
            debug(r,c)
            await message.channel.send(prompt)
            r,c = await timeanswer(r,c)
            return r,c

        async def Ship(r,c):
            prompt1 = 'We have encounted an enemy Krell ship! '
            promptN = 'We have encounted enemy Krell ships! '
            size1 =  ['You call that pipsqueak a real spaceship? More like an annoying fly. ',\
                     'That small spaceship is barely any challenge to us. ',\
                     'I would call that a perfectly average sized spaceship. Nothing we cannot handle. ',\
                     'Now that guy is larger than average. Finally, a challenge! ',\
                     'That is a HUGE spaceship! But the bigger they are, the harder they fall. If we had gravity that is. ']
            sizeN =  ['You call those pipsqueaks real spaceships? More like annoying flies. ',\
                     'Those small spaceships are barely any challenge to us. ',\
                     'I would call those perfectly average sized spaceships. Nothing we cannot handle. ',\
                     'Now these guys are larger than average. Finally, a challenge! ',\
                     'Those are HUGE spaceships! But the bigger they are, the harder they fall. If we had gravity that is. ']
            number = ['Ha! There\'s only one of them! Too easy. ',\
                      'Just two. Trying the pincer formation, eh? Come on, let\'s show them who is boss around here. ',\
                      'Huh, there\'s three now chasing us. Where do they keep coming from??? ',\
                      'They just keep multiplying! There\'s now four. Alright, it is time we stopped playing around. ',\
                      'FIVE?!? Who kicked the hive I wonder. *You and Mbot present a picture of innocence...* ']
            code = self.mapzone[r][c]
            codeletter = code[0]
            codenumber = int(code[1])
            if codeletter == 'F':
                if codenumber == 1:
                    prompt = prompt1+size1[0]+number[0]
                else:
                    prompt = promptN+sizeN[0]+number[codenumber-1]
            elif codeletter == 'L':
                if codenumber == 1:
                    prompt = prompt1+size1[1]+number[0]
                else:
                    prompt = promptN+sizeN[1]+number[codenumber-1]
            elif codeletter == 'Y':
                if codenumber == 1:
                    prompt = prompt1+size1[2]+number[0]
                else:
                    prompt = promptN+sizeN[2]+number[codenumber-1]
            elif codeletter == 'T':
                if codenumber == 1:
                    prompt = prompt1+size1[3]+number[0]
                else:
                    prompt = promptN+sizeN[3]+number[codenumber-1]
            elif codeletter == 'O':
                if codenumber == 1:
                    prompt = prompt1+size1[4]+number[0]
                else:
                    prompt = promptN+sizeN[4]+number[codenumber-1]
            prompt = prompt+'\nWhich direction do you want to go?'
            await message.channel.send(prompt)
            self.timeout = self.timeout + 8
            r,c = await timeanswer(r,c)
            self.timeout = self.timeout - 8
            return r,c
        
        async def Haven(r,c):
            prompt = '[timer+20] *Whew* We can take a breather here. This is quite a chase!\nWhich direction do you want to go?'
            debug(r,c)
            await message.channel.send(prompt)
            self.timeout = self.timeout + 20
            r,c = await timeanswer(r,c)
            self.timeout = self.timeout - 20
            return r,c

        async def Zone(r,c):
            zonefetch = self.mapzone[r][c].upper()
            preprompt = ['My database is saying we are in zone **'+str(zonefetch)+'**, whatever that means. The instruction manual is not loading.',\
                'We are in space zone **'+str(zonefetch)+'**! I hope it is correct.',\
                'Space zone **'+str(zonefetch)+'**. Who named these things anyway?? So sloppy, there are probably duplicates.',\
                '*routine mechanical voice* Space zone **'+str(zonefetch)+'**. Whoever named these things must be a sleep deprived boring person.',\
                'Space zone **'+str(zonefetch)+'**. Illogical zone naming schemes is how spaceships get lost in, well, space.',\
                'Space zone **'+str(zonefetch)+'**. Yes, that\'s what it says here. I don\'t know how anyone is supposed to find their way in space like this.',\
                'We are in space zone **'+str(zonefetch)+'**! So uncreative.',\
                'My database is saying we are in zone **'+str(zonefetch)+'**. Okay I guess.',\
                'My database is saying we are in zone **'+str(zonefetch)+'**. At least this data was not corrupted.',\
                '*routine mechanical voice* Space zone **'+str(zonefetch)+'**. Space is weird.']
            prompt = random.choice(preprompt)+'\nWhich direction do you want to go?'
            debug(r,c)
            await message.channel.send(prompt)
            r,c = await timeanswer(r,c)
            return r,c

        async def Color(r,c,newTile):
            tileColor = newTile[5:].lower()
            if   tileColor == 'red':
                preprompt = 'Ooh that is a pretty red giant in the distance! Otherwise we are still floating aimlessly in space.'
            elif tileColor == 'orange':
                preprompt = 'That strangely orange planet looks like it is covered almost entirely in desert sand dunes. *shudders* Looks inhospitable.'
            elif tileColor == 'yellow':
                preprompt = 'We flew into a binary star system with two perfectly average yellow stars. This is turning out to be quite educational. Because physics!'
            elif tileColor == 'green':
                preprompt = 'Ooh that planet currently has a green aurora borealis dancing along it\'s surface! I can just look at it endlessly...'
            elif tileColor == 'blue':
                preprompt = 'We are flying by a planet that looks as blue as the Old Earth. I wonder what happened to our ancesteral home?'
            elif tileColor == 'purple':
                preprompt = 'So many colors in a supernova!! But I think it purple. Let\'s find another one!'
            prompt = preprompt+'\nWhich direction do you want to go?'
            debug(r,c)
            await message.channel.send(prompt)
            r,c = await timeanswer(r,c)
            return r,c

        async def LightMatter(r,c):
            zonefetch = self.mapzone[r][c].upper()
            prompt = 'Looks like my matter detection sensor unjammed temporarily. I am picking up strong Ordinary Matter signals here. '\
                'Oh by the way, we are in space zone **'+zonefetch+'** if that helps.'\
                '\nWhich direction do you want to go?'
            debug(r,c)
            await message.channel.send(prompt)
            r,c = await timeanswer(r,c)
            return r,c

        async def DarkMatter(r,c):
            zonefetch = self.mapzone[r][c].upper()
            prompt = 'Ooh there is definitely a higher concentration of Dark Matter here! How exciting! I want to know where the rest lies. '\
                'Oh by the way, we are in space zone **'+zonefetch+'** if that helps.'\
                '\nWhich direction do you want to go?'
            debug(r,c)
            await message.channel.send(prompt)
            r,c = await timeanswer(r,c)
            return r,c

        async def Select(r,c):
            prompt = 'We see featureless space in all directions, except... the *eyes* are back! I wonder why they are watching here? Anyway, let\'s get out!\n'\
                'Which direction do you want to go?'
            debug(r,c)
            await message.channel.send(prompt)
            r,c = await timeanswer(r,c)
            return r,c


        # General functions for running the map tiles

        def getTile(r,c):
            if self.mapkey[r][c] != '0':
                nameTile = self.mapkey[r][c]
                return nameTile
            else: 
                nameTile = '0'
                return nameTile

        async def timeanswer(r0,c0):
            try: 
                direction = await self.bot.wait_for('message',check=check,timeout=self.timeout)
            except asyncio.TimeoutError:
                r = 'timer'
                return r,c
            else:
                r,c = stepxy(r0,c0,direction.content)
                try:
                    #if self.world == 'sel' and getTile(r,c) == '0':
                    if getTile(r,c) == '0':
                        prompt = 'We can\'t go there. Krell ships block the way on the edge of space. Choose another direction.' 
                        await message.channel.send(prompt)
                        r,c = await timeanswer(r0,c0)
                        return r,c
                except:
                    return r,c
                return r,c

        async def checkanswermission(r,c):
            msg = await self.bot.wait_for('message',check=check,timeout=None)
            query = msg.content
            if query[:2] == 'P:':
                if query[3:].upper() == self.missionanswer:
                    r = 'correct'
                    return r,c
                else:
                    await message.channel.send('{} is incorrect. Try again or let\'s continue flying.'.format(query[3:].upper()))
                    r,c = await checkanswermission(r,c)
                    return r,c
            else:
                r,c = stepxy(r,c,query)
                return r,c

        async def stop(criteria):
            self.world = None
            self.mapkey = None
            self.mapzone = None
            self.timeout = None
            if criteria == 'cancel':
                prompt = '**Mission Cancelled**'
                await message.channel.send(prompt)
            elif criteria == 'krell':
                prompt = 'Oh no! There is a Krell station in this direction and you flew us straight into it!\n**Mission Terminated**'
                await message.channel.send(prompt)
            elif criteria == 'timer':
                prompt = 'Oh no! The timer ran out and the Krell have caught up to us!\n**Mission Terminated**'
                await message.channel.send(prompt)
            elif criteria == 'debris':
                prompt = 'Oh no! We flew straight into floating space debris!\n**Mission Terminated**'
                await message.channel.send(prompt)
            elif criteria == 'correct':
                prompt = '**'+str(self.missionanswer)+'** is correct! Have a badge.\nAfter a brief stop on Kress, you realize you will '\
                    'not find the path to the Cosmere in this corner of space. Time to continue exploring elsewhere.\n**Mission Completed**'
                await message.channel.send(prompt)
                await message.channel.send(self.moon)
                self.missionanswer = None
                self.moon = None

        def debug(r,c):
            #print('You are at box '+self.mapkey[r][c]+' which is at '+str(r)+' '+str(c)+' and zone '+str(self.mapzone[r][c]))
            pass

        def stepxy(r,c,direction):
            if direction.lower() in ['forward','f','w']:
                r += -1; c += 0
                return r,c
            elif direction.lower() in ['backward','b','s']:
                r += 1;  c += 0
                return r,c
            elif direction.lower() in ['right','r','d']:
                r += 0;  c += 1
                return r,c
            elif direction.lower() in ['left','l','a']:
                r += 0;  c += -1
                return r,c
            elif direction.lower() == 'stop':
                r = 'cancel'; c = 0
                return r,c

        def check(m):
            return m.channel == message.channel and m.author == message.author
        
        async def checkanswermaster(query):

            if query.content.lower() == 'stop':
                await stop('cancel')

            elif query.content.upper() == self.masteranswer.upper():
                prompt =    'Flying to **OPHIUCHUS** is correct! And is also where Voyager 1 is currently heading.\n'\
                            'You have opened a portal into the Cosmere and escaped Detritus. Nice job :)\n'\
                            'If you are reading this, presumably my spagetti:ramen: text adventure worked.'                
                embed=discord.Embed()
                embed.set_image(url=url)
                await message.channel.send(prompt,embed=embed)  

            else: 
                prompt = '**ERROR: CYTONIC HYPERDRIVE OFFLINE**'
                directionprompt =   'Navigate me by sending directions **W**,**S**,**A**,**D** (case insen.)\n'\
                                    'Be careful and do not fly me into a Krell station or floating space junk! \n'\
                                    'You can exit the trip at any time by sending **stop**\n'\
                                    'Send **yes** if ready!'
                
                if query.content.lower() in ['sel']:
                    await message.channel.send(prompt)
                    await asyncio.sleep(1.0)
                    self.world = 'sel'
                    self.timeout = 5
                    self.moon = '```       _..._     \n     .\'   `::.   \n    :       :::  \n    :       :::  \n    `.     .::\'  \n      `-..:\'\'    \n```'
                    self.missionanswer = 'FLYTO'
                    introprompt =   '\nAh, bother. Let\'s just go to Sel the slow way. Maybe we can find a shortcut to the Cosmere somewhere... \n\n'
                    await message.channel.send(introprompt+directionprompt)
                    gotime = await self.bot.wait_for('message',check=check,timeout=None)
                    if gotime.content.lower() == 'yes':
                        mapzone,r0,c0 = self.getMap('misc/maps/selZone.txt')
                        mapkey,r0,c0 = self.getMap('misc/maps/selMap.txt')
                        #c0 = random.choice([3,11])
                        self.mapkey = mapkey
                        self.mapzone = mapzone
                        await game(r0,c0)
                    else: 
                        await stop('cancel')

                elif query.content.lower() in ['rosh','roshar']:
                    await message.channel.send(prompt)
                    await asyncio.sleep(1.0)
                    self.world = 'roshar'
                    self.timeout = 9
                    self.moon = '```       _..._     \n     .\' .::::.    \n    :  ::::::::  \n    :  ::::::::  \n    `. \'::::::\'  \n      `-.::\'\'     \n```'
                    self.missionanswer = 'CELESTIAL'
                    introprompt =   '\nI want to go to Roshar regardless! Who\'s going to stop us from trying anyway? I AM THE GREAT AND POWERFUL MBOT! Maybe we can find a shortcut to the Cosmere somewhere... \n\n'
                    await message.channel.send(introprompt+directionprompt)
                    gotime = await self.bot.wait_for('message',check=check,timeout=None)
                    if gotime.content.lower() == 'yes':
                        mapzone,r0,c0 = self.getMap('misc/maps/rosharZone.txt')
                        mapkey,r0,c0 = self.getMap('misc/maps/rosharMap.txt')
                        self.mapkey = mapkey
                        self.mapzone = mapzone
                        await game(r0,c0)
                    else: 
                        await stop('cancel')

                elif query.content.lower() in ['nal','nalthis']:
                    await message.channel.send(prompt)
                    await asyncio.sleep(1.0)
                    self.world = 'nalthis'
                    self.timeout = 6
                    self.moon = '```       _..._      \n     .:::::::.    \n    :::::::::::  \n    :::::::::::  \n    `:::::::::\'  \n      `\':::\'\'      \n```'
                    self.missionanswer = 'HELLEN'
                    introprompt =   '\nNo, I am determined that we find our way to the world of pretty colors. We\'ll just have to fly to Nalthis the slow way. Maybe we can find a shortcut to the Cosmere somewhere... \n\n'
                    await message.channel.send(introprompt+directionprompt)
                    gotime = await self.bot.wait_for('message',check=check,timeout=None)
                    if gotime.content.lower() == 'yes':
                        mapkey,r0,c0 = self.getMap('misc/maps/nalthisMap.txt')
                        self.mapkey = mapkey
                        await game(r0,c0)
                    else: 
                        await stop('cancel')

                elif query.content.lower() in ['tal','taldain']:
                    await message.channel.send(prompt)
                    await asyncio.sleep(1.0)
                    self.world = 'taldain'
                    self.timeout = 7
                    self.moon = '```       _..._      \n     .::::. `.    \n    :::::::.  :  \n    ::::::::  :  \n    `::::::\' .\'  \n      `\'::\'-\'     \n```'
                    self.missionanswer = 'SERPENT'
                    introprompt =   '\nAww but Taldain is such a fascinating world! I think we can get there manually. Are you with me? Maybe we can find a shortcut to the Cosmere somewhere... \n\n'
                    await message.channel.send(introprompt+directionprompt)
                    gotime = await self.bot.wait_for('message',check=check,timeout=None)
                    if gotime.content.lower() == 'yes':
                        mapzone,r0,c0 = self.getMap('misc/maps/taldainZone.txt')
                        mapkey,r0,c0 = self.getMap('misc/maps/taldainMap.txt')
                        self.mapkey = mapkey
                        self.mapzone = mapzone
                        await game(r0,c0)
                    else: 
                        await stop('cancel')

                elif query.content.lower() in ['scad','scadrial','scadriel']:
                    await message.channel.send(prompt)
                    await asyncio.sleep(1.0)
                    self.world = 'scadrial'
                    self.timeout = 6
                    self.moon = '```       _..._     \n     .::\'   `.   \n    :::       :  \n    :::       :  \n    `::.     .\'  \n      `\':..-\'    \n```'
                    self.missionanswer = 'BEARER'
                    introprompt =   '\nWell, the computer has spoken. We will have to fly to Scadrial manually. Maybe we can find a shortcut to the Cosmere somewhere... \n\n'
                    await message.channel.send(introprompt+directionprompt)
                    gotime = await self.bot.wait_for('message',check=check,timeout=None)
                    if gotime.content.lower() == 'yes':
                        mapzone,r0,c0 = self.getMap('misc/maps/scadrialZone.txt')
                        mapkey,r0,c0 = self.getMap('misc/maps/scadrialMap.txt')
                        self.mapkey = mapkey
                        self.mapzone = mapzone
                        await game(r0,c0)
                    else: 
                        await stop('cancel')

                elif query.content.lower() in ['detritus']: 
                    prompt = 'Why are you trying to go to Detritus. Don\'t we want to escape the place? Try again or send **stop** to exit.'
                    await message.channel.send(prompt)
                    query = await self.bot.wait_for('message',check=check, timeout=None)
                    await checkanswermaster(query)

                elif query.content.lower() in ['serpentarius','serpens','asclepius']: 
                    prompt = 'Close! But not quite. Try again?'
                    await message.channel.send(prompt)
                    query = await self.bot.wait_for('message',check=check, timeout=None)
                    await checkanswermaster(query)

                else: 
                    await message.channel.send('I cannot fly there (yet?) Try again or send **stop** to exit.')
                    query = await self.bot.wait_for('message',check=check, timeout=None)
                    await checkanswermaster(query)


        # BEGIN MAIN PROGRAM
        if message.content.lower() in ['engage','engage cytonic hyperdrive']:
            affirmative = [ 'SURE! Let\'s fly to a Cosmere world together :mushroom: \nWhere do you want to fly to?',\
                            'Affirmative, engaging cytonic hyperdrive bound for the Cosmere. \nWhere do you want to fly to?',\
                            'Engaging cytonic hyperdrive! With you, I\'ll fly anywhere. Let\'s escape this place. I always wanted to visit a Cosmere world. \nWhere do you want to fly to?',\
                            'I\'m all for that! Let\'s try finding the Cosmere!\nWhere do you want to fly to?',\
                            'You are right... the space winds of adventure call! I hear the Cosmere has interesting worlds... Engaging cytonic hyperdrive!\nWhere do you want to fly to?']
            await message.channel.send(random.choice(affirmative))
            query = await self.bot.wait_for('message',check=check, timeout=None)
            await checkanswermaster(query)



def setup(bot):
    bot.add_cog(DebrisCog(bot))


