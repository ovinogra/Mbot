# db.py
import psycopg2
from dotenv import load_dotenv
import os



# Connection to postgresql database

class DBase:

    def __init__(self, ctx):
        self.ctx = ctx
        self.bot = ctx.bot
        self.guildID = str(ctx.guild.id)
    

    
    ################ Main DB connection ################

    def connect(self):
        load_dotenv()
        DB_ADDRESS = os.getenv('DB_ADDRESS')
        connection = psycopg2.connect(DB_ADDRESS, sslmode='prefer')
        cursor = connection.cursor()        
        return connection, cursor


    def disconnect(self,connection,cursor):
        if connection:
            cursor.close()
            connection.close()



    ################ TABLE hunt ################

    ### Columns:
    # idx
    # guild_name
    # guild_id
    # hunt_role
    # hunt_role_id
    # hunt_username
    # hunt_password
    # hunt_url
    # hunt_folder
    # hunt_nexus
    # date_update


    async def gethuntdata(self,query):
        ''' query, guildID: string '''
        
        query1 = "SELECT "+query+" FROM hunt WHERE guild_id = '"+self.guildID+"';"

        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            results = cursor.fetchall()
            self.disconnect(connection,cursor)
            if results:
                return results[0]
        except psycopg2.Error as error: 
            await self.ctx.send(error)
            return 0 # have to return not None

    
    async def updatehuntdata(self,query):
        ''' query: string '''

        query1 = "UPDATE hunt SET "+query+" WHERE guild_id = '"+self.guildID+"';"

        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            connection.commit()
            self.disconnect(connection,cursor)
            await self.ctx.send('Login update successful')
        except psycopg2.Error as error: 
            await self.ctx.send(error)
    

    
    ################ TABLE hunt ################
    # db owner only


    async def inserthuntdata(self,guildname,guildID):
        ''' guildname, guildID: string of guild info '''

        query1 = "INSERT INTO hunt (guild_name, guild_id) VALUES ('"+guildname+"','"+guildID+"');" 

        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            connection.commit()
            self.disconnect(connection,cursor)
            await self.ctx.send('INSERT successful')
        except psycopg2.Error as error: 
            await self.ctx.send(error)


    async def deletehuntdata(self,guildID):
        ''' guildID: string of guild ID '''

        query1 = "DELETE FROM hunt WHERE guild_id = '"+guildID+"';" 

        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            connection.commit()
            self.disconnect(connection,cursor)
            await self.ctx.send('DELETE successful')
        except psycopg2.Error as error: 
            await self.ctx.send(error)



    ################ TABLE tags ################

    ### Columns:
    # idx
    # guild_id
    # tag_name
    # tag_content
    # date_update


    async def gettagall(self):
        
        query1 = "SELECT tag_name FROM tags WHERE guild_id = '"+self.guildID+"';"
        
        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            results = cursor.fetchall()
            self.disconnect(connection,cursor)
            if results:
                return results
        except psycopg2.Error as error: 
            await self.ctx.send(error)
    

    async def gettagsingle(self,tagname):
        ''' tagname: string '''
        
        query1 = "SELECT tag_content FROM tags WHERE guild_id = '"+self.guildID+"' AND tag_name = '"+tagname+"';"
        
        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            results = cursor.fetchall()
            self.disconnect(connection,cursor)
            if results:
                return results
        except psycopg2.Error as error: 
            await self.ctx.send(error)


    async def inserttag(self,tagname,tagcontent):
        ''' tagname, tagcontent: string '''

        query1 = "INSERT INTO tags (guild_id, tag_name, tag_content) VALUES ('"+self.guildID+"','"+tagname+"','"+tagcontent+"');" 

        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            connection.commit()
            self.disconnect(connection,cursor)
            await self.ctx.send('Tag added successfully')
        except psycopg2.Error as error: 
            await self.ctx.send(error)


    async def updatetag(self,tagname,tagcontent):
        ''' tagname, tagcontent: string '''

        query1 = "UPDATE tags SET guild_ID = '"+self.guildID+"', tag_content = '"+tagcontent+"' WHERE tag_name = '"+tagname+"';"

        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            connection.commit()
            self.disconnect(connection,cursor)
            await self.ctx.send('Tag updated successfully')
        except psycopg2.Error as error: 
            await self.ctx.send(error)


    async def deletetag(self,tagname):
        ''' tagname: string '''

        query1 = "DELETE FROM tags WHERE guild_id = '"+self.guildID+"' AND tag_name = '"+tagname+"';" 

        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            connection.commit()
            self.disconnect(connection,cursor)
            await self.ctx.send('Tag removed successfully')
        except psycopg2.Error as error: 
            await self.ctx.send(error)



