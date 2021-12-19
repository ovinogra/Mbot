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
        DATABASE_URL = os.getenv('DATABASE_URL')
        connection = psycopg2.connect(DATABASE_URL, sslmode='prefer')
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


    async def hunt_get_row(self,query):
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

    
    async def hunt_update_row(self,query):
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
    # for db owner


    async def hunt_insert_row(self,guildname,guildID):
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


    async def hunt_delete_row(self,guildID):
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


    async def tag_get_all(self):
        
        query1 = "SELECT tag_name FROM tags;"
        
        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            results = cursor.fetchall()
            self.disconnect(connection,cursor)
            if results:
                return results
        except psycopg2.Error as error: 
            await self.ctx.send(error)
    

    async def tag_get_row(self,tagname):
        ''' tagname: string '''
        
        query1 = "SELECT tag_content FROM tags WHERE tag_name = '"+tagname+"';"
        
        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            results = cursor.fetchall()
            self.disconnect(connection,cursor)
            if results:
                return results
        except psycopg2.Error as error: 
            await self.ctx.send(error)


    async def tag_insert_row(self,tagname,tagcontent):
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


    async def tag_update_row(self,tagname,tagcontent):
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


    async def tag_delete_row(self,tagname):
        ''' tagname: string '''

        query1 = "DELETE FROM tags WHERE tag_name = '"+tagname+"';" 

        try:
            connection, cursor = self.connect()
            cursor.execute(query1)
            connection.commit()
            self.disconnect(connection,cursor)
            await self.ctx.send('Tag removed successfully')
        except psycopg2.Error as error: 
            await self.ctx.send(error)



