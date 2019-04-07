import abc
import datetime
from typing import Dict, List, Any, Optional

import discord

import liquid_democracy
from config import Config
from liquid_democracy import Motion, MotionOptions


class Command:
    """
    Abstract base class for commands. Subclass this and implement `name`, `short_help` and `execute_direct`, then
    register this with :code:`bot.register_command`
    """

    def __init__(self):
        self.subcommands: Dict[str, "Command"] = {}

    @abc.abstractmethod
    def name(self) -> str:
        """
        The name used to activate this command
        """
        ...

    def add_sub_command(self, command: "Command"):
        """
        Add a sub command to this command
        :param command: The sub command
        """
        self.subcommands[command.name()] = command

    @abc.abstractmethod
    def short_help(self) -> str:
        """
        Return a single line help message for this command
        :return: The help message
        """
        ...

    def long_help(self) -> str:
        """
        List all sub commands and their descriptions
        :return: A longer help message
        """
        if not self.subcommands:
            return self.short_help()

        help = f"**{self.name()}** offers the following services:"
        for subcommand in self.subcommands.values():
            help += f"\n- {subcommand.short_help()}"

        return help

    @abc.abstractmethod
    async def execute_direct(self, input: List[str], bot: "PithosClient", conversation: discord.Message):
        """
        Execute this command directly with the provided arguments, not calling any subcommands
        :param input: The input, split along whitespace.
        :param bot: The bot
        :param conversation: The conversation in which this command was executed
        """
        ...

    async def execute(self, input: List[str], bot: "PithosClient", conversation: discord.Message):
        """
        Execute this command. Directly, if no subcommands are registered, otherwise dispatches the matching subcommand
        :param input: The input, split along whitespace
        :param bot: The bot
        :param conversation: The conversation in which this command was executed
        """
        if not self.subcommands:
            await self.execute_direct(input, bot, conversation)
            return

        if not input:
            await bot.send_message(conversation.channel, f"Missing sub-command:\n{self.long_help()}")
            return

        cmd = input[0].lower()
        if cmd not in self.subcommands:
            await bot.send_message(conversation.channel, f"Not a valid sub-command:\n{self.long_help()}")
            return

        await self.subcommands[cmd].execute(input[1:], bot, conversation)


class Flow:
    """
    An interaction sequence with a user
    """

    def __init__(self, bot: "PithosClient", user: discord.User):
        self.bot = bot
        self.user = user

    @abc.abstractmethod
    async def step(self, input: str):
        """
        Step through the flow
        :param input: The input to the flow at this stage: The message as sent by the user.
        """
        ...

    @abc.abstractmethod
    def is_finished(self) -> bool:
        """
        Check whether the flow is finished. If it is finished, the flow will automatically be removed from the bot.
        :return: whether the flow is finished
        """
        ...


class CmdHelp(Command):
    def name(self) -> str:
        return "help"

    def short_help(self) -> str:
        return "**help** - Help with operating this bot. Try `help <command>`"

    def long_help(self) -> str:
        return "`help` - List all commands\n" \
               "`help <command>` - Show more detailed information for a command"

    async def execute_direct(self, input: List[str], bot: "PithosClient", conversation: discord.Message):
        if not input:
            help = ""
            for command in bot.commands.values():
                help += f"{command.short_help()}\n"
            await bot.send_message(conversation.channel, help)
            return

        cmd_str = input[0].lower()
        if cmd_str not in bot.commands:
            await bot.send_message(conversation.channel, f"No such command: {cmd_str} - try help")
            return

        cmd = bot.commands[cmd_str]

        i = 1
        while i < len(input):
            cmd_str = input[i].lower()
            if cmd_str not in cmd.subcommands:
                so_far = " ".join(input[:i])
                await bot.send_message(conversation.channel,
                                       f"({so_far}) No such command: {cmd_str} - try 'help {so_far}'?")
                return
            cmd = cmd.subcommands[cmd_str]

        await bot.send_message(conversation.channel, cmd.long_help())


class CmdCancel(Command):
    def name(self) -> str:
        return "cancel"

    def short_help(self) -> str:
        return "**cancel** - Cancel an ongoing command"

    async def execute_direct(self, input: List[str], bot: "PithosClient", conversation: discord.Message):
        if conversation.author.id not in bot.flows:
            await bot.send_message(conversation.channel, "Nothing to cancel")
            return

        bot.cancel_flow(conversation.author)
        await bot.send_message(conversation.channel, "Cancelled")


class CmdMotion(Command):
    class CmdMotionList(Command):
        def name(self) -> str:
            return "list"

        def short_help(self) -> str:
            return "**motion list** - List running motions"

        async def execute_direct(self, input: List[str], bot: "PithosClient", conversation: discord.Message):
            now = datetime.datetime.now()
            results = liquid_democracy.get_session().query(Motion).filter(Motion.expires > now).all()
            if not results:
                await bot.send_message(conversation.channel, "No currently running motions")
            else:
                msg = "\n".join(f"{motion.description} - Voting ends {motion.expires}" for motion in results)
                await bot.send_message(conversation.channel, msg)

    class CmdMotionNew(Command):
        def name(self) -> str:
            return "new"

        def short_help(self) -> str:
            return "**motion new** - File a new motion"

        async def execute_direct(self, input: List[str], bot: "PithosClient", conversation: discord.Message):
            await bot.send_message(conversation.channel,
                                   "Alright! I'll ask you some questions in PM to set up that motion.")
            await bot.send_message(conversation.author,
                                   "Please give me a short one- or two-line description of your motion "
                                   "(E.g. 'Paint all benches green.' or 'What will we do with all that "
                                   "cotton candy?'.")
            await bot.start_flow(CmdMotion.FlowNewMotion(bot, conversation.author))

    class FlowNewMotion(Flow):
        def __init__(self, bot: "PithosClient", user: discord.User):
            super(CmdMotion.FlowNewMotion, self).__init__(bot, user)
            self.phase = 0
            self.description: Optional[str] = None
            self.expiry: Optional[datetime.datetime] = None
            self.options: List[str] = []

        async def step(self, input: str):
            if self.phase == 0:
                self.description = input
                await self.bot.send_message(self.user, "Please write a description for option 1")
                self.phase = 1
            elif self.phase == 1:
                self.options.append(input)
                await self.bot.send_message(self.user, "Please write a description for option 2")
                self.phase = 2
            elif self.phase == 2:
                self.options.append(input)
                await self.bot.send_message(self.user,
                                            f"Please write a description for option 3, "
                                            f"or type 'done' to finish")
                self.phase = 3
            elif self.phase == 3:
                if input.lower() == "done":
                    await self.bot.send_message(self.user, f"How many days do you want your motion to last?")
                    self.phase = 4
                else:
                    self.options.append(input)
                    await self.bot.send_message(self.user,
                                                f"Please write a description for option {len(self.options) + 1}, "
                                                f"or type 'done' to finish")
            elif self.phase == 4:
                try:
                    duration = int(input)
                    self.expiry = datetime.datetime.now() + datetime.timedelta(days=duration)
                    self.phase = 5

                    motion = Motion(description=self.description, expires=self.expiry)
                    for option in self.options:
                        motion.options.append(MotionOptions(description=option))
                    liquid_democracy.get_session().add(motion)
                    liquid_democracy.get_session().commit()

                    announce_text = f":loudspeaker: New motion filed by {self.user.display_name}\n{self.description}"
                    for i, option in enumerate(self.options):
                        announce_text += f"\n[{i + 1}] {option}"
                    announce_text += f"\nVoting ends {self.expiry}"

                    await self.bot.send_message(self.bot.motion_channel, announce_text)

                except ValueError:
                    await self.bot.send_message(self.user, "Not a valid number")

        def is_finished(self) -> bool:
            return self.phase == 5

    def __init__(self):
        super().__init__()
        self.add_sub_command(CmdMotion.CmdMotionList())
        self.add_sub_command(CmdMotion.CmdMotionNew())

    def name(self) -> str:
        return "motion"

    def short_help(self) -> str:
        return "**motion** - Interact with motions"

    def execute_direct(self, input: List[str], bot: "PithosClient", conversation: discord.Message):
        pass  # Only contains subcommands


class PithosClient(discord.Client):
    def __init__(self, config: Config):
        super(PithosClient, self).__init__()
        self.config = config
        self.flows: Dict[str, Any] = {}  # Track flows of users through commands
        self.commands: Dict[str, Command] = {}
        self.server: Optional[discord.Server] = None
        self.motion_channel: Optional[discord.Channel] = None
        self.archive_channel: Optional[discord.Channel] = None

        self.register_command(CmdHelp())
        self.register_command(CmdCancel())
        self.register_command(CmdMotion())

    def register_command(self, command: Command):
        self.commands[command.name()] = command

    async def start_flow(self, flow: Flow):
        if flow.user.id in self.flows:
            await self.send_message(flow.user, f"You are already in a command. Try "
            f"{self.config.discord.command_prefix}cancel if you want to cancel the current command.")
            return

        self.flows[flow.user.id] = flow

    def cancel_flow(self, user: discord.User):
        del self.flows[user.id]

    async def on_ready(self):
        tgt_server_id = self.config.discord.server_id
        for server in self.servers:
            if server.id == tgt_server_id:
                self.server = server
                break

        if not self.server:
            print("Client not invited to target server! Follow this link:")
            print(discord.utils.oauth_url(
                self.config.discord.client_id,
                discord.Permissions(67648),
                discord.Server(id=str(tgt_server_id)))
            )
            return

        self.motion_channel = self.server.get_channel(self.config.discord.motion_channel_id)
        if not self.motion_channel:
            print(f"Motion channel not found on server. "
                  f"Looking for channel with id {self.config.discord.motion_channel_id}.")
            return

        self.archive_channel = self.server.get_channel(self.config.discord.archive_channel_id)
        if not self.archive_channel:
            print(f"Archive channel not found on server. "
                  f"Looking for channel with id {self.config.discord.archive_channel_id}.")
            return

        print("Running, connected")

    async def on_message(self, message: discord.Message):
        print(f"[{message.channel.name}] <{message.author.name}> {message.content}")
        if message.content.startswith(self.config.discord.command_prefix):
            parts = message.content[len(self.config.discord.command_prefix):].split()
            if not parts:
                await self.send_message(message.channel, "Missing command")
                return

            cmd = parts[0].lower()
            if cmd not in self.commands:
                await self.send_message(message.channel,
                                        f"{cmd} - No such command. Try {self.config.discord.command_prefix}help")
                return

            await self.commands[cmd].execute(parts[1:], self, message)
            return

        if message.author.id in self.flows:
            print("User has active flow")
            flow = self.flows[message.author.id]
            await flow.step(message.content)
            if flow.is_finished():
                self.cancel_flow(message.author)
