# TODO: Command not enabled message
from Common import Permissions, Utils


class Command:
    def __init__(self, parent_mod, name, aliases, enabled=False, minimum_permissions="Owner", command_help="No help",
                 useage="No useage"):
        # Check if parameters are valid
        assert name is not None or "", "Command not given a valid name"
        assert aliases is not None and len(aliases) > 0, "Command not given aliases"
        # Var Init
        self.parent_mod = parent_mod
        self.name = name
        self.aliases = aliases
        self.enabled = enabled
        self.minimum_permissions = minimum_permissions
        self.help = command_help
        self.useage = useage

    def __eq__(self, other):
        return self.name == other.name

    def __iter__(self):
        self.alias_index = 0
        return self

    def __next__(self):
        if self.alias_index > len(self.aliases) - 1:
            raise StopIteration
        else:
            alias = self.aliases[self.alias_index]
            self.alias_index += 1
            return alias

    # Returns if the given string is a known command alias
    def is_alias(self, string):
        return string in self.aliases

    # Returns true if the passed user ID has the permissions to call this command
    def has_permissions(self, user_id):
        return Permissions.has_permission(user_id, self.minimum_permissions)

    # Calls the command if it's enabled and if the user has perms
    async def call_command(self, message, user_id):
        if self.enabled:
            if self.has_permissions(user_id):
                # Send "is typing", for  a e s t h e t i c s
                await Utils.client.send_typing(message.channel)
                await self.parent_mod.command_called(message, self)
