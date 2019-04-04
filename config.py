from typing import TypeVar, Dict, Any, Union, List

from ruamel.yaml import yaml_object, YAML

T = TypeVar("T")
YamlDict = Dict[str, Any]
ConfigParam = Union[YamlDict, T]

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)


@yaml_object(yaml)
class DiscordSettings:
    def __init__(self, token: str, channel_id: int):
        self.token = token
        self.channel_id = channel_id

    @staticmethod
    def default() -> "DiscordSettings":
        return DiscordSettings(
            token="your_bot_token",
            channel_id=12345
        )


@yaml_object(yaml)
class Config:
    def __init__(self, default_generated: bool, discord: DiscordSettings):
        self.default_generated = default_generated
        self.discord = discord

    @staticmethod
    def default() -> "Config":
        return Config(
            default_generated=True,
            discord=DiscordSettings.default()
        )


def check_object_attributes(loaded: T, default: T) -> List[str]:
    """
    For each field in `default`, check if it's present in `loaded`. If not, copy the value from `default`. If yes and
    the field contains an object, apply this check recursively.
    :param loaded: The object to check
    :param default: The object containing the necessary fields and default values
    :return: The list of paths to the changed attributes
    """
    if not hasattr(default, "__dict__"):
        return []  # Some builtin type, like str

    changed = []

    for attr in default.__dict__:
        default_attr = getattr(default, attr)

        if not hasattr(loaded, attr):
            setattr(loaded, attr, default_attr)
            changed.append(attr)

        else:
            loaded_attr = getattr(loaded, attr)

            if not isinstance(loaded_attr, type(default_attr)):
                setattr(loaded, attr, default_attr)
                changed.append(attr)

            elif isinstance(default_attr, object):
                sub_changed = check_object_attributes(loaded_attr, default_attr)
                for sub_attr in sub_changed:
                    changed.append(attr + "." + sub_attr)

    return changed


def fill_missing_config_values(config: Config) -> List[str]:
    """
    Check if any values in the config are missing and if so, initialize them with default values
    :return: The list of paths to the changed attributes
    """
    default = Config.default()
    return check_object_attributes(config, default)


def load_config(path: str = "config.yml") -> Config:
    """
    Load the configuration file.
    If it does not exist, a default file is generated and the program exits.
    If the loaded file is missing some config values, the missing values are generated and the program exits.
    If the loaded file contains only the default values, the program exits.
    :param path: Path to the config file. Defaults to "config.yml" in working directory
    :return: The configuration file
    """
    try:
        with open(path) as config_file:
            config = yaml.load(config_file)
    except FileNotFoundError:
        with open(path, 'w+') as config_file:
            yaml.dump(config, config_file)
        print("Config file (config.yml) not found. A default config has been generated. "
              "Please adjust as needed and then set 'default_generated: false'")
        exit(1)

    changed_attributes = fill_missing_config_values(config)
    if changed_attributes:
        with open(path, 'w+') as config_file:
            yaml.dump(config, config_file)
        print("Some values were missing in the config. The following fields have been generated:")
        for attr in changed_attributes:
            print("  -", attr)
        print("Please check if the new values are ok")
        exit(1)

    if config.default_generated:
        print("You are using the default configuration file. This will not work - we need your bot "
              "token and you need to configure your channels. Please adjust your config file and then "
              "set 'default_generated: false'")
        exit(1)

    return config
