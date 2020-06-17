# db_launcher.py

import psycopg2
from dotenv import load_dotenv
import os

## Make simple database tables, only needs to be run once.


# check connection to database
load_dotenv()
DB_ADDRESS = os.getenv('DB_ADDRESS')
connection = psycopg2.connect(DB_ADDRESS, sslmode='prefer')
print(connection.get_dsn_parameters(),"\n")

cursor = connection.cursor()
cursor.execute("SELECT version();")
record = cursor.fetchone()
print("You are connected to - ", record,"\n")




### make HUNT table to store basic guild info for puzzle login, also needed for puzzle management command
# referenced in:    cogs/hunt.py
#                   cogs/puzzle.py
#                   cogs/admin.py


create_table_query = '''
CREATE TABLE hunt (
	idx serial PRIMARY KEY,
	guild_name VARCHAR (255) NOT NULL,
	guild_id VARCHAR (255) NOT NULL,
	hunt_role VARCHAR (255) DEFAULT 'None',
	hunt_role_id VARCHAR (255) DEFAULT 'None',
	hunt_username VARCHAR (255) DEFAULT 'None',
	hunt_password VARCHAR (255) DEFAULT 'None',
	hunt_url VARCHAR (255) DEFAULT 'None',
	hunt_folder VARCHAR (255) DEFAULT 'None',
	hunt_nexus VARCHAR (255) DEFAULT 'None',
	date_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	UNIQUE(guild_id)
);'''
cursor.execute(create_table_query)

setup_table = '''
CREATE OR REPLACE FUNCTION update_timestamp_column() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_update = now();
    RETURN NEW; 
END;
$$ language 'plpgsql';

CREATE TRIGGER update_timestamp_trigger 
BEFORE UPDATE ON hunt FOR EACH ROW EXECUTE PROCEDURE  update_timestamp_column();
'''
cursor.execute(setup_table)

# initialize_table = '''
# INSERT INTO hunt (guild_name, guild_id)
# VALUES
# 	('ServerName','ID of your server');
# '''
# cursor.execute(initialize_table)




### make TAGS table to store stuff in, well, tags
# referenced in:    cogs/tags.py


create_table_query = '''
CREATE TABLE tags (
	idx serial PRIMARY KEY,
	guild_id VARCHAR (255) NOT NULL,
	tag_name VARCHAR (255) NOT NULL,
	tag_content VARCHAR (255) NOT NULL,
	date_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

cursor.execute(create_table_query)

setup_table = '''
CREATE OR REPLACE FUNCTION update_timestamp_column() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_update = now();
    RETURN NEW; 
END;
$$ language 'plpgsql';

CREATE TRIGGER update_timestamp_trigger 
BEFORE UPDATE ON tags FOR EACH ROW EXECUTE PROCEDURE  update_timestamp_column();
'''
cursor.execute(setup_table)

# initialize_table = '''
# INSERT INTO tags (guild_id, tag_name, tag_content)
# VALUES
# 	('ID of your server','test','I made a tag!');
# '''
# cursor.execute(initialize_table)




# write and commit changes to db

connection.commit()

if(connection):
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")



