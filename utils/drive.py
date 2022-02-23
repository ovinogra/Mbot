import gspread
import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account


# Google Drive API functionality that is required by various cogs

class Drive:

    instance = None

    # override to ensure that only one Drive object is ever created
    def __new__(cls):
        if not cls.instance:
            cls.instance = super(Drive, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        # TODO: has to be a less silly way to organize this
        load_dotenv()
        self.key = os.getenv('GOOGLE_CLIENT_SECRETS')
        self.googledata = json.loads(self.key)
        self.googledata['private_key'] = self.googledata['private_key'].replace("\\n", "\n")
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = service_account.Credentials.from_service_account_info(self.googledata, scopes=scopes)

    def gclient(self):
        return gspread.authorize(self.credentials)
