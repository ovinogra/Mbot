A discord bot with puzzlehunt solving tools and puzzle management functions. This method of puzzle organization uses google sheets to store progress and seems to work for a small virtual team. For fun, the bot is partly themed around the works of Brandon Sanderson.

### Toolbox
* [Nutrimatic](https://nutrimatic.org/) for anagrams, regex search, patterns, etc
* [Quipqiup](https://quipqiup.com/) cryptograms
* Caesar shift with or without key -- without a key has option of guessing an answer via a [web tool from Robert Eisele](https://www.xarg.org/tools/caesar-cipher/)
* Letter <-> number alphanumeric converter

### Other Features
* Store shared hunt login info for team
* Puzzle manager command (make a channel per puzzle, copy a google sheet template per puzzle, update summary sheet with solutions/links/notes, rename channels, fetch puzzle summary info)
* A tags database for storing common resources
* A Cosmere-themed text adventure game with mini puzzles, interfaced to run within discord
* Other random practice commands

### Running
Most commands like website queries run without dependencies (only need the bot token in step 1). Anything related to puzzle management also needs a Google service account and a PostgreSQL database (the other steps). Although some tweaking might be needed, basic steps are as follows:
1. Create a `.env` with your bot token, postgreSQL database URI, and service account address.
```
DISCORD_TOKEN= ..   # your discord bot token
DB_ADDRESS= ...     # address as postgres:yourdbconnectionasURI
CLIENT_EMAIL= ...   # copy the service account address from client_secrets.json USER@PROJECT.iam.gserviceaccount.com 
```
2. Enable Google API following instructions on [gspread documentation](https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account) to get a `client_secrets.json` for a service account.
3. Run `python3.6 db_launcher.py` in terminal to configure simple tables in database.
4. Once you deploy bot to a server, run `!ins YourServerName YourServerID` *once* in any channel to initialize database storage for server. Or uncomment and update relevant lines in `db_launcher.py` before running it.

## Requirements
python v3.6+
discord.py v1.2.5
python-dotenv
asyncio
regex
numpy v1.18.1
mechanize v0.4.5
requests v2.22.0
psycopg2 v2.8.4
gspread v3.6.0




