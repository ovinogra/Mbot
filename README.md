A discord bot with tools and automatic puzzlehunt progress tracking for a small to medium sized team. For fun, the bot is named after a character from the works of Brandon Sanderson.

### Puzzle Manager
Puzzle progress stored in a master "Nexus" google sheet.
* With a `!createround` command: create a new category, general channel, voice channel, update nexus
* With one puzzle `!create` command: create puzzle channel, duplicate template google sheet, update nexus sheet, send links to discord
* Log answer in nexus sheet with `!solve`
* View and update `!login` info for team
* View puzzle progress in `!nexus`
* Store and update common resources in `!tag`

Example of auto-populated nexus sheet (answers removed)
![example](https://github.com/Moonrise55/Mbot/blob/master/misc/nexus_example.PNG)

### Toolbox 
* `!n`: [Nutrimatic](https://nutrimatic.org/) for anagrams, regex search, patterns, etc
* `!cc`: Caesar shift 
* `!alpha`: Alphanumeric A1Z26
* `!atom`: Periodic table
* `!atbash`: Atbash cipher
* `!v`: Vigenere cipher

### Bot setup
The setup relies on a Google service account and a AWS DynamoDB connection. 
1. Create a `.env` with your tokens.
```
DISCORD_TOKEN= ...   # your discord bot token
GOOGLE_CLIENT_SECRETS=...   # google service account credentials
BASE_NEXUS_ID= ... # for !createhunt, the stuff in your nexus URL after /d/ and before /edit?=
BASE_TEMPLATE_ID= ... # for !createhunt, the stuff in your template URL after /d/ and before /edit?=
DATABASE_PATH= ... # the relative path to your database file
```
2. Enable Google API following instructions on [gspread documentation](https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account) to get a `client_secrets.json` for a service account.
3. Initialize the database tables.  This can either be done:
   1. [forthcoming] on the M-Bot side (or for standalone M-Bot) via `python utils/db_init.py`. Note that this may require replacing the database or generating your own update scripts if new changes are made in the future.
   2. on the Shardboard side via the usual Django database commands (`python manage.py makemigrations`/`python manage.py migrate`)
4. Set up base Nexus and Puzzle Template sheets (shared w/ service account address). 
5. Feel free to message me for details/help. 


