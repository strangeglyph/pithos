import discord

import config
from config import Config


class PithosClient(discord.Client):
    def __init__(self, config: Config):
        super(PithosClient, self).__init__()
        self.config = config

    async def on_ready(self):
        await self.send_message(discord.Object(config.discord.channel_id), "Hello world")


if __name__ == "__main__":
    config = config.load_config()

# PithosClient(config).run(config.discord.token)
