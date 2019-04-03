import discord
import yaml
from typing import Dict, Any


class DiscordSettings:
    def __init__(self, token: str, channel_id: int):
        self.token = token
        self.channel_id = channel_id


class Config:
    def __init__(self, discord: Dict[str, Any]):
        self.discord = DiscordSettings(**discord)


class PithosClient(discord.Client):
    def __init__(self, config: Config):
        super(PithosClient, self).__init__()
        self.config = config

    async def on_ready(self):
        await self.send_message(discord.Object(config.discord.channel_id), "Hello world")


try:
    with open("config.yml") as config_file:
        config = Config(**yaml.safe_load(config_file))
except FileNotFoundError:
    print("Config file (config.yml) not found. Please copy config.yml.template and adjust as needed")

PithosClient(config).run(config.discord.token)
