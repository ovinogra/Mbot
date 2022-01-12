A discord bot with tools and automatic puzzlehunt progress tracking for a small to medium sized team. For fun, the bot is named after a character from the works of Brandon Sanderson.

### Puzzle Manager
Puzzle progress stored in a master "Nexus" google sheet.
* With a `!createround` command: create a new category, general channel, voice channel, update nexus
* With one puzzle `!create` command: create puzzle channel, duplicate template google sheet, update nexus sheet, send links to discord
* Log answer in nexus sheet with `!solve`
* View and update `!login` info for team
* View puzzle progress in `!nexus`
* Store common resources in `!tag`

Example of auto-populated nexus sheet (answers removed)
![example](https://github.com/Moonrise55/Mbot/blob/master/misc/nexus_example.PNG)

### Toolbox 
* `!nu`: [Nutrimatic](https://nutrimatic.org/) for anagrams, regex search, patterns, etc
* ~~`!qq`: [Quipqiup](https://quipqiup.com/) cryptograms~~ TODO: update to beta3 version of site
* `!cc`: Caesar shift 
* `!alpha`: Alphanumeric A1Z26
* `!atom`: Periodic table
* `!atbash`: Atbash cipher
* `!v`: Vigenere cipher

### Bot setup
1. Create a `.env` with your bot token and postgreSQL database address.
```
DISCORD_TOKEN= ...   # your discord bot token
DATABASE_URL= ...     # address as postgres:yourdbconnectionURI
GOOGLE_CLIENT_SECRETS=...   # google service account credentials
```
Database connection needed for the puzzle manager only. Additionally, you would need to:

2. Enable Google API following instructions on [gspread documentation](https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account) to get a `client_secrets.json` for a service account.
3. Run `python3.6 db_launcher.py` to setup some simple db tables and hope nothing breaks.
4. Set up a google folder (shared w/ service account address) with Nexus and Puzzle Template sheets. 
5. Choose between hunt.py and bighunt.py cogs.
6. Happy to give more details if you want to adapt this to your server. Feel free to message. 


