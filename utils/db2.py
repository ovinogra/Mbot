# %%
import random
from base64 import b64encode
from datetime import datetime
from hashlib import pbkdf2_hmac

import boto3
import os
from dotenv import load_dotenv
import sqlite3


# %%


def connect():
    load_dotenv()
    return sqlite3.connect(os.path.join(os.getcwd(), os.getenv('DATABASE_PATH')))


def hash_password(password):
    salt = b64encode(os.urandom(16)).decode('utf-8')
    return 'pbkdf2_sha256$260000$'\
        + salt + '$'\
        + b64encode((pbkdf2_hmac('sha256', bytes(password, 'utf-8'), bytes(salt, 'utf-8'), 260000))).decode('utf-8')


class DBase:

    def __init__(self, ctx):
        self.ctx = ctx
        self.conn = connect()

    def hunt_get_row(self, guildID, category_id):
        ''' query, guildID: int '''

        dynamodb = connect()
        table = dynamodb.Table('multi-hunt')
        response = table.scan(
            FilterExpression=Attr('guild_id').eq(guildID) & Attr('hunt_category_id').eq(category_id)
        )
        if len(response['Items']) < 1:
            try:
                round_row = self.round_get_row(guildID, category_id)
                response_from_round = table.scan(
                    FilterExpression=Attr('guild_id').eq(guildID) & Attr('hunt_category_id').eq(round_row['hunt_category_id'])
                )
                if len(response_from_round['Items']) < 1:
                    raise Exception('This is not a hunt category!')
                return response_from_round['Items'][0]
            except Exception:
                pass
            raise Exception('This is not a hunt category!')
        return response['Items'][0]

    async def hunt_update_row(self, updatedata, guildID, category_id):
        ''' updatedata: list of tuples [(fieldname, value),(fieldname, value)] '''

        dynamodb = connect()
        table = dynamodb.Table('multi-hunt')

        # format update fields
        update_expression = ["set "]
        update_values = dict()
        for item in updatedata:
            update_expression.append(f" {item[0]} = :{item[0]},")
            update_values[f":{item[0]}"] = item[1]
        update_expression = "".join(update_expression)[:-1]

        table.update_item(
            Key={
                'guild_id': guildID,
                'hunt_category_id': category_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=dict(update_values)
        )
        await self.ctx.send('Login update successful')
        return

    async def hunt_insert_row(self, guild_id, hunt_name, category_id, hunt_role_id, hunt_folder, hunt_nexus, is_bighunt, hunt_logfeed, bighunt_pass):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO hunts_Hunt
                (guild_id, name, category_id, role_id, folder, nexus, is_bighunt, logfeed)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (guild_id, hunt_name, category_id, hunt_role_id, hunt_folder, hunt_nexus, is_bighunt, hunt_logfeed))
        if is_bighunt:
            cursor.execute("""
                INSERT INTO auth_user
                (username, password, date_joined, is_superuser, is_staff, is_active, first_name, last_name, email)
                VALUES
                (?, ?, ?, 0, 0, 1, "", "", "")
            """, (hunt_name, hash_password(bighunt_pass), datetime.now()))
        self.conn.commit()
        cursor.close()
        return

    async def hunt_delete_row(self, guildID, category_id):
        ''' guildID: int of guild ID '''

        dynamodb = connect()
        table = dynamodb.Table('multi-hunt')

        table.delete_item(
            Key={
                'guild_id': int(guildID),
                'hunt_category_id': category_id
            }
        )
        await self.ctx.send('DELETE ROW successful')
        return

    def round_get_row(self, guild_id, category_id):
        dynamodb = connect()
        table = dynamodb.Table('multi-hunt-rounds')

        response = table.scan(
            FilterExpression=Attr('guild_id').eq(guild_id) & Attr('round_category_id').eq(category_id)
        )
        if len(response['Items']) < 1:
            raise Exception('This is not a hunt category!')
        return response['Items'][0]

    async def round_insert_row(self, guild_id, category_id, hunt_category_id):
        dynamodb = connect()
        table = dynamodb.Table('multi-hunt-rounds')

        table.put_item(
            Item={
                'guild_id': int(guild_id),
                'round_category_id': int(category_id),
                'hunt_category_id': int(hunt_category_id),
            }
        )
        # await self.ctx.send('INSERT ROW successful')
        return

    ################ TABLE tags ################

    def tag_get_all(self):
        dynamodb = connect()
        table = dynamodb.Table('tags')
        response = table.scan()
        data = response['Items']
        return data

    def tag_get_row(self, tagname):
        ''' tagname: string '''

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
        ''' tagname, tagcontent: string '''

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
        ''' tagname, tagcontent: string '''

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
        ''' tagname: string '''

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

# %%

# testing stuff:
# db = DBase(0)
# table = db.Table('hunt')
# db.hunt_insert_row('test',123)
# guildID = 123
# res = db.hunt_get_row(guildID)
# print(res)
# db.hunt_delete_row(guildID)
# t = [('hunt_username', 'test'), ('hunt_password', 'urithit'), ('hunt_url', 3)]
# db.hunt_update_row(t,guildID)

# %%

########################################
### RECREATE TABLES JSON TO DYNAMODB ###
########################################

# with open('PATH/hunt.json', 'r') as myfile:
#     data=myfile.read()

# objhunt = json.loads(data)


# # Create the DynamoDB table.
# table = dynamodb.create_table(
#     TableName='multi-hunt',
#     KeySchema=[
#         {
#             'AttributeName': 'guild_id',
#             'KeyType': 'RANGE'
#         },
#         {
#             'AttributeName': 'hunt_category_id',
#             'KeyType': 'RANGE'
#         }
#     ],
#     AttributeDefinitions=[
#         {
#             'AttributeName': 'guild_id',
#             'AttributeType': 'N'
#         },
#         {
#             'AttributeName': 'hunt_category_id',
#             'AttributeType': 'N'
#         },
#     ],
#     ProvisionedThroughput={
#         'ReadCapacityUnits': 10,
#         'WriteCapacityUnits': 10
#     }
# )

# table.wait_until_exists()

# fields = objhunt['fields']
# values = objhunt['values']

# for item in values:
#     name = item[fields.index('guild_name')]
#     print(name)

#     table.put_item(
#     Item={
#             'guild_name': item[fields.index('guild_name')],
#             'guild_id': int(item[fields.index('guild_id')]),
#             'hunt_category_id: int(item[fields.index('hunt_category_id')]),
#             'hunt_role': item[fields.index('hunt_role')],
#             'hunt_role_id': item[fields.index('hunt_role_id')],
#             'hunt_username': item[fields.index('hunt_username')],
#             'hunt_password': item[fields.index('hunt_password')],
#             'hunt_url': item[fields.index('hunt_url')],
#             'hunt_folder': item[fields.index('hunt_folder')],
#             'hunt_nexus': item[fields.index('hunt_nexus')]
#         }
#     )


# with open('PATH/tags.json', 'r') as myfile:
#     data=myfile.read()

# objtags = json.loads(data)

# # Create the DynamoDB table.
# table = dynamodb.create_table(
#     TableName='tags',
#     KeySchema=[
#         {
#             'AttributeName': 'tag_name',
#             'KeyType': 'HASH'
#         },
#         {
#             'AttributeName': 'guild_id',
#             'KeyType': 'RANGE'
#         }
#     ],
#     AttributeDefinitions=[
#         {
#             'AttributeName': 'tag_name',
#             'AttributeType': 'S'
#         },
#         {
#             'AttributeName': 'guild_id',
#             'AttributeType': 'N'
#         },
#     ],
#     ProvisionedThroughput={
#         'ReadCapacityUnits': 5,
#         'WriteCapacityUnits': 5
#     }
# )

# table.wait_until_exists()

# fields = objtags['fields']
# values = objtags['values']

# # count = 0
# for item in values:
#     name = item[fields.index('tag_name')]
#     print(name)

#     # count += 1
#     table.put_item(
#     Item={
#             # 'idx': count,
#             'tag_name': item[fields.index('tag_name')],
#             'guild_id': int(item[fields.index('guild_id')]),
#             'tag_content': item[fields.index('tag_content')]
#         }
#     )
