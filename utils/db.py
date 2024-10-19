# %%
from base64 import b64encode
from datetime import datetime
from hashlib import pbkdf2_hmac

import os
from dotenv import load_dotenv
import sqlite3


# %%


def connect():
    load_dotenv()
    conn = sqlite3.connect(os.path.join(os.getcwd(), os.getenv('DATABASE_PATH')))
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    salt = b64encode(os.urandom(16)).decode('utf-8')
    return 'pbkdf2_sha256$260000$'\
        + salt + '$'\
        + b64encode((pbkdf2_hmac('sha256', bytes(password, 'utf-8'), bytes(salt, 'utf-8'), 260000))).decode('utf-8')


def make_updates(update_data):
    updates = update_data[0][0] + ' = ?'
    values = [update_data[0][1]]
    for i in range(1, len(update_data)):
        updates += ", " + update_data[i][0] + ' = ?'
        values.append(update_data[i][1])
    updates += ' '
    return updates, values


class DBase:

    def __init__(self, ctx):
        self.ctx = ctx
        self.conn = connect()

    # Hunts

    def hunt_get_row(self, guild_id, category_id):
        cursor = self.conn.cursor()
        res = cursor.execute("""
            SELECT * FROM hunts_Hunt WHERE guild_id = ? AND category_id = ?
        """, (guild_id, category_id))
        row = res.fetchone()
        if row is not None:
            return row
        round_res = cursor.execute("""
            SELECT * FROM hunts_Hunt WHERE
                (SELECT hunt_id FROM hunts_Round
                    WHERE (SELECT guild_id FROM hunts_Hunt WHERE id = hunt_id) = ? AND category_id = ?
                ) = id
        """, (guild_id, category_id))
        row = round_res.fetchone()
        cursor.close()
        if row is None:
            raise Exception('This is not a hunt category!')
        return row

    def hunt_update_row(self, update_data, guild_id, category_id):
        cursor = self.conn.cursor()
        updates, values = make_updates(update_data)
        values.append(guild_id)
        values.append(category_id)
        cursor.execute("""
            UPDATE hunts_Hunt SET """ + updates + """WHERE guild_id = ? AND category_id = ?
        """, tuple(values))
        self.conn.commit()
        cursor.close()
        return

    def hunt_insert_row(self, guild_id, hunt_name, category_id, hunt_role_id, hunt_folder, hunt_nexus, is_bighunt, hunt_logfeed, bighunt_pass):
        cursor = self.conn.cursor()
        web_user_id = None
        if is_bighunt:
            cursor.execute("""
                INSERT INTO auth_user
                (username, password, date_joined, is_superuser, is_staff, is_active, first_name, last_name, email)
                VALUES
                (?, ?, ?, 0, 0, 1, "", "", "")
            """, (hunt_name, hash_password(bighunt_pass), datetime.now()))
            web_user_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO hunts_Hunt
                (guild_id, name, category_id, role_id, folder, nexus, is_bighunt, logfeed, web_user_id)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, hunt_name, category_id, hunt_role_id, hunt_folder, hunt_nexus, is_bighunt, hunt_logfeed, web_user_id))
        self.conn.commit()
        cursor.close()
        return

    def round_get_row(self, guild_id, category_id=None, name=None, marker=None):
        cursor = self.conn.cursor()
        if category_id is not None:
            res = cursor.execute("""
                SELECT * FROM hunts_Round WHERE (SELECT guild_id FROM hunts_Hunt WHERE id = hunt_id) = ? AND category_id = ?
            """, (guild_id, category_id))
            rnd = res.fetchone()
            if rnd is not None:
                return rnd
        elif name is not None:
            res = cursor.execute("""
                SELECT * FROM hunts_Round WHERE (SELECT guild_id FROM hunts_Hunt WHERE id = hunt_id) = ? AND name = ?
            """, (guild_id, name))
            rnd = res.fetchone()
            if rnd is not None:
                return rnd
        elif marker is not None:
            res = cursor.execute("""
                SELECT * FROM hunts_Round WHERE (SELECT guild_id FROM hunts_Hunt WHERE id = hunt_id) = ? AND marker = ?
            """, (guild_id, marker))
            rnd = res.fetchone()
            if rnd is not None:
                return rnd
        return None

    def round_insert_row(self, guild_id, category_id, hunt_category_id, name, marker):
        cursor = self.conn.cursor()
        res = cursor.execute("""
            SELECT id FROM hunts_Hunt WHERE guild_id = ? AND category_id = ?
        """, (guild_id, hunt_category_id))
        hunt = res.fetchone()
        if hunt is None:
            raise Exception('Could not find a hunt!')
        cursor.execute("""
            INSERT INTO hunts_Round (name, marker, category_id, hunt_id) VALUES (?, ?, ?, ?)
        """, (name, marker, category_id, hunt['id']))
        self.conn.commit()
        cursor.close()
        return

    def puzzle_get_row(self, guild_id, channel_id=None, name=None):
        cursor = self.conn.cursor()
        if channel_id is not None:
            res = cursor.execute("""
                SELECT * FROM hunts_Puzzle WHERE (SELECT guild_id FROM hunts_Hunt WHERE id = hunt_id) = ? AND channel_id = ?
            """, (guild_id, channel_id))
            puzzle = res.fetchone()
            if puzzle is not None:
                return puzzle
        elif name is not None:
            res = cursor.execute("""
                SELECT * FROM hunts_Puzzle WHERE (SELECT guild_id FROM hunts_Hunt WHERE id = hunt_id) = ? AND name = ?
            """, (guild_id, name))
            puzzle = res.fetchone()
            if puzzle is not None:
                return puzzle
        return None

    def puzzle_insert_row(self, guild_id, hunt_category_id, channel_id, voice_channel_id, name, spreadsheet_link, is_meta, round_name):
        cursor = self.conn.cursor()
        res = cursor.execute("""
            SELECT id FROM hunts_Hunt WHERE guild_id = ? AND category_id = ?
        """, (guild_id, hunt_category_id))
        hunt = res.fetchone()
        if hunt is None:
            raise Exception('Could not find a hunt!')
        cursor.execute("""
            INSERT INTO hunts_Puzzle
                (name, channel_id, voice_channel_id, spreadsheet_link, priority, is_meta, unlock_time, hunt_id)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, channel_id, voice_channel_id, spreadsheet_link, 'New', is_meta, datetime.now(), hunt['id']))
        if round_name is not None:
            cursor.execute("""
                INSERT INTO hunts_Puzzle_Rounds
                    (puzzle_id, round_id)
                    VALUES
                    (?, (SELECT id FROM hunts_Round WHERE (SELECT guild_id FROM hunts_Hunt WHERE id = hunt_id) = ? AND name = ?))
            """, (cursor.lastrowid, guild_id, round_name))
        self.conn.commit()
        cursor.close()
        return

    def puzzle_update_row(self, update_data, guild_id, hunt_category_id, channel_id):
        cursor = self.conn.cursor()
        updates, values = make_updates(update_data)
        values.append(guild_id)
        values.append(hunt_category_id)
        values.append(channel_id)
        cursor.execute("""
            UPDATE hunts_Puzzle SET """ + updates + """WHERE hunt_id = (SELECT id FROM hunts_Hunt WHERE guild_id = ? AND category_id = ?) AND channel_id = ?
        """, tuple(values))
        self.conn.commit()
        cursor.close()
        return

    # Tags
    # TODO port this over to new db schema
    '''
    def tag_get_all(self):
        dynamodb = connect()
        table = dynamodb.Table('tags')
        response = table.scan()
        data = response['Items']
        return data

    def tag_get_row(self, tagname):
        dynamodb = connect()
        table = dynamodb.Table('tags')

        try:
            response = table.scan(
                FilterExpression=Attr('tag_name').eq(tagname)
            )
            items = response['Items']

            return items[0]
        except:
            return False

    async def tag_insert_row(self, tagname, tagcontent, guildID):
        dynamodb = connect()
        table = dynamodb.Table('tags')
        table.put_item(
            Item={
                'tag_name': tagname,
                'guild_id': int(guildID),
                'tag_content': tagcontent
            }
        )
        await self.ctx.send('Tag added successful')
        return

    async def tag_update_row(self, tagname, tagcontent):
        dynamodb = connect()
        table = dynamodb.Table('tags')
        currentdata = self.tag_get_row(tagname)
        table.update_item(
            Key={
                'guild_id': int(currentdata['guild_id']),
                'tag_name': tagname
            },
            UpdateExpression='set tag_content = :val1',
            ExpressionAttributeValues={
                ':val1': tagcontent
            }
        )
        await self.ctx.send('Tag updated successful')
        return

    async def tag_delete_row(self, tagname):
        dynamodb = connect()
        table = dynamodb.Table('tags')
        currentdata = self.tag_get_row(tagname)
        table.delete_item(
            Key={
                'guild_id': int(currentdata['guild_id']),
                'tag_name': tagname
            }
        )

        await self.ctx.send('Tag deleted successful')
        return
    '''
