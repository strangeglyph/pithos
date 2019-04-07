import discord
from config import Config


class PithosClient(discord.Client):
    def __init__(self, config: Config):
        super(PithosClient, self).__init__()
        self.config = config

    async def on_ready(self):
        tgt_server_id = self.config.discord.server_id
        target_server = discord.utils.find(lambda s: s.id == tgt_server_id, self.servers)
        if not target_server:
            print("Client not invited to target server! Follow this link:")
            print(discord.utils.oauth_url(
                self.config.discord.client_id,
                discord.Permissions(67648),
                discord.Server(id=str(tgt_server_id)))
            )
