import config
from bot import PithosClient

if __name__ == "__main__":
    config = config.load_config()
    PithosClient(config).run(config.discord.token)
