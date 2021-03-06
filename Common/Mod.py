from Common.Command import Command
from Common import Utils
import time


# Extendable class for mods
class Mod:
    def __init__(self, mod_name, description="No description", commands=None, embed_color=Utils.default_hex_color):
        # Check if parameters are valid
        assert ' ' not in mod_name, "Mod name \"" + mod_name + "\" contains a space"
        assert Utils.is_hex(hex(embed_color)), "Embed Color \"" + hex(embed_color) + "\" is not a valid hex color"
        assert type(commands) is dict, "Mod command list is not of type dict"
        for command_name in commands:
            assert type(commands[command_name]) is Command, "Mod commands are not of type \"Command\""
        # Var init
        self.commands = {} if commands is None else commands
        self.name = mod_name
        self.embed_color = embed_color
        self.description = description
        self.command_aliases = [alias for command_name in self.commands for alias in self.commands[command_name]]

    # Called when the bot receives a message
    async def command_called(self, message, command):
        await Utils.simple_embed_reply(Utils.client, message.channel, "[Error]",
                                       "No command parsing implemented for this mod")

    # Called when the bot receives ANY message
    async def message_received(self, message):
        pass

    # Called when the bot joins a server
    async def on_server_join(self, server):
        pass

    # Called when a member joins a server
    async def on_member_join(self, member):
        pass

    # Called when a message is deleted
    async def on_message_delete(self, message):
        pass

    # Called when a user's VoiceState changes
    async def on_voice_state_update(self, before, after):
        pass

    # Called when a user doesn't have permissions to call a command
    async def error_no_permissions(self, message, command):
        pass

    # Called when a command is called in a channel it is disabled in
    async def error_disabled_channel(self, message, command):
        pass

    # Called when a command is called in a server it is disabled in
    async def error_disabled_server(self, message, command):
        pass

    # Called when a command is called during its cool down
    # Default message - can be over-written
    async def error_cool_down(self, message, command):
        seconds_left = command.cool_down_seconds - (time.time() - command.last_called(message.author.id))
        time_left_text = Utils.seconds_format(seconds_left)
        await Utils.simple_embed_reply(message.channel, str(message.author),
                                       "You can call " + command.name + " again in " + time_left_text + ".",
                                       self.embed_color)

    # Called once a second
    async def second_tick(self):
        pass

    # Called once a minute
    async def minute_tick(self):
        pass

    # Returns true if the passed command alias is known by the mod
    def is_command_alias(self, command_alias):
        return command_alias in self.command_aliases

    # Replies with help (specific or broad)
    async def get_help(self, message):
        await Utils.get_help(message, self.name, self.commands,
                             message.content.split(" ")[1].lower() == self.name.lower())

    # Returns the important info about this mod
    def get_info(self):
        return {'Name': self.name, 'Description': self.description, 'Commands': self.mod_commands()}

    # Returns a list of known commands from this mod
    def mod_commands(self):
        return self.commands
