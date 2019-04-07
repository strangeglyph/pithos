# Pithos - Liquid Democracy for Discord

Pithos is a discord bot to manage liquid democracy votes on discord. More to follow.

## Setting up your own bot

First, start the bot once with `pipenv run python main.py`. This will generate a configuration file which we will need to edit in further steps.

### Getting your discord bot a token

You need a user id and a token for your bot. Think of this as a username and password, except for digital lifeforms.

Visit [Discord's application site](https://discordapp.com/developers/applications/). Create a new application. You will find the client id on the "General Information" tab, right under the field for the name.

Then, switch to the "Bot" tab. Create a new bot and give it a name. Click on "Reveal Token" to receive your token. Keep this secret! With it, anyone can log in as your bot.

Put the client id into `discord -> client_id` and the token into `discord -> token`

### Telling your bot which server to monitor

Monitoring more than one server is currently not supported, please hold.

Activate developer mode, if you haven't yet. In discord, open up your settings, select "Appearance", scroll down a bit and activate developer mode.

Right click the server where you want the bot to be active and select "copy id", all the way at the bottom. Put that into `discord -> server_id`.

### Finalize the config

Set `default_generated` to `false`.

### Invite the bot to the server

Run the bot again (`pipenv run python main.py`). A link will be printed to the console that you can use to invite the bot to your server. Follow it to invite the bot and it will automatically join.

