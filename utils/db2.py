
#%%
import boto3 
import os 
from dotenv import load_dotenv
import json 
from boto3.dynamodb.conditions import Key, Attr


#%%




class DBase:

    def __init__(self, ctx):
        self.ctx = ctx
        # self.bot = ctx.bot
        # self.guildID = str(ctx.guild.id)
        # self.guildID = 123 # for testing

    
    ################ Main DB connection ################

    def connect(self):
        load_dotenv()
        AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
        AWS_REGION = "us-east-1"

        dynamodb = boto3.resource(
            'dynamodb',
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            region_name=AWS_REGION)

        return dynamodb



    def hunt_get_row(self,guildID):
        ''' query, guildID: int '''

        dynamodb = self.connect()
        table = dynamodb.Table('hunt')
        response = table.scan(
            FilterExpression=Attr('guild_id').eq(guildID)
        )
        return response['Items'][0]



    
    async def hunt_update_row(self,updatedata,guildID):
        ''' updatedata: list of tuples [(fieldname, value),(fieldname, value)] '''

        dynamodb = self.connect()
        table = dynamodb.Table('hunt')
        currentdata = self.hunt_get_row(guildID)

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
                    'guild_name': currentdata['guild_name']
                },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=dict(update_values)
            )
        await self.ctx.send('Login update successful')
        return

    async def hunt_insert_row(self,guildname,guildID):
        ''' guildname, guildID: string and int of guild info '''

        dynamodb = self.connect()
        table = dynamodb.Table('hunt')

        table.put_item(
        Item={
            'guild_name': guildname,
            'guild_id': int(guildID),
            'hunt_role': 'none',
            'hunt_role_id': 'none',
            'hunt_username': 'none',
            'hunt_password': 'none',
            'hunt_url': 'none',
            'hunt_folder': 'none',
            'hunt_nexus': 'none',
            }
        )
        await self.ctx.send('INSERT ROW successful')
        return 

    async def hunt_delete_row(self,guildID):
        ''' guildID: int of guild ID '''

        dynamodb = self.connect()
        table = dynamodb.Table('hunt')

        guilddata = self.hunt_get_row(int(guildID))

        table.delete_item(
            Key={
                'guild_id': int(guildID),
                'guild_name': guilddata['guild_name']
            }
        )
        await self.ctx.send('DELETE ROW successful')
        return



#%%

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

#%%

########################################
### RECREATE TABLES JSON TO DYNAMODB ###
########################################

# with open('PATH/hunt.json', 'r') as myfile:
#     data=myfile.read()

# objhunt = json.loads(data)


# # Create the DynamoDB table.
# table = dynamodb.create_table(
#     TableName='hunt',
#     KeySchema=[
#         {
#             'AttributeName': 'guild_name',
#             'KeyType': 'HASH'
#         },
#         {
#             'AttributeName': 'guild_id',
#             'KeyType': 'RANGE'
#         }
#     ],
#     AttributeDefinitions=[
#         {
#             'AttributeName': 'guild_name',
#             'AttributeType': 'S'
#         },
#         {
#             'AttributeName': 'guild_id',
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





