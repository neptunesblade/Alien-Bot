from Common.Mod import Mod
from Common import Utils
import discord
import logging
import json


# TODO: Change from in-memory DB to on-disk SQL DB
# TODO: on_member_join and on_server_join
class ColoredRoles(Mod):
    def __init__(self, mod_name, embed_color):
        # General var init
        self.users = {}
        self.roles = {}
        self.name = mod_name
        self.embed_color = embed_color
        # Config var init
        self.config = json.loads(
            "".join(open("Mods/ColoredRoles/ColoredRolesConfig.json", encoding="utf-8").readlines()))
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config['Commands'])
        # Generate a fresh DB
        self.generate_db()
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config['Mod Description'], self.commands, embed_color)

    # Called when a command from this mod is called
    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        channel, author, server = message.channel, message.author, message.guild
        try:
            # Adding a role
            if command is self.commands['Add Color Command']:
                # Check command format
                if len(split_message) > 1:
                    # If the first parameter is hex
                    if Utils.is_hex(split_message[1]):
                        hex_color = split_message[1].upper()
                        # If role hasn't been created and max color count hasn't been reached -> Create Role
                        if len(self.roles[server.id]) < self.config['Max Colors']:
                            if self.get_role_by_hex(server, hex_color) is None:
                                new_color_role = await self.create_role(server, hex_color)
                            # Role already exists -> Get it
                            else:
                                new_color_role = self.get_role_by_hex(server, hex_color)
                            # Give the user their color
                            await self.give_role(server, author, new_color_role)
                            await Utils.simple_embed_reply(channel, "[Add Role]",
                                                           "Added " + hex_color + " to your roles.", hex_color)
                        else:
                            await Utils.simple_embed_reply(channel, "[Added Color]", "Max role count reached.",
                                                           hex_color=hex_color)
                    # First parameter is not a valid hex value -> Error
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Invalid hex value.",
                                                       split_message[1])
                # Hex parameter not supplied -> Error
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Missing color parameter.")
            # Removing a role
            elif command is self.commands["Remove Color Command"]:
                # Get current role info
                current_color_role_id = self.users[server.id][author.id]
                current_color_role = Utils.get_role_by_id(server, current_color_role_id)
                hex_color = current_color_role.name
                # Remove the role
                await self.remove_role(server, author, current_color_role)
                # Reply
                await Utils.simple_embed_reply(channel, "[Removed Color]", "Removed " + hex_color + " from your roles.",
                                               hex_color=hex_color)
            # Deleting a role
            elif command is self.commands["Delete Color Command"]:
                # If the hex color was supplied
                if len(split_message) > 1:
                    if Utils.is_hex(split_message[1]):
                        hex_color = split_message[1].upper()
                        color_role = self.get_role_by_hex(server, hex_color)
                        # If the role doesn't exist -> Error
                        if color_role is None:
                            await Utils.simple_embed_reply(channel, "[Error]", "Color not found.", hex_color)
                        # Role found -> Delete it and let the user know
                        else:
                            await self.delete_role(server, color_role)
                            # Reply
                            await Utils.simple_embed_reply(channel, "[Deleted Color]", "Deleted " + hex_color + ".",
                                                           hex_color=hex_color)
                    # First parameter is not a valid hex value -> Error
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Invalid hex value.", split_message[1])
                # Hex parameter not supplied -> Error
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Missing color parameter.")
            # Listing roles
            elif command is self.commands["List Colors Command"]:
                roles_text = ""
                # If roles exist
                if len(self.roles[server.id]) > 0:
                    # Build text from every role name
                    for role in self.roles[server.id]:
                        roles_text += Utils.get_role_by_id(server, role).name + "\n"
                # No roles exist -> state so
                else:
                    roles_text = "No roles exist."
                # Reply with the list
                await Utils.simple_embed_reply(channel, "[Color List]", roles_text)
            # Listing users equipped with role
            elif command is self.commands["Equipped Users Command"]:
                # If the hex color was supplied
                if len(split_message) > 1:
                    if Utils.is_hex(split_message[1]):
                        hex_color = split_message[1].upper()
                        role = self.get_role_by_hex(server, hex_color)
                        # If the role exists
                        if role is not None:
                            users_text = ""
                            # Check if users are equipped with this role
                            if len(self.roles[server.id][role.id]) > 0:
                                for user_id in self.roles[server.id][role.id]:
                                    user = Utils.get_user_by_id(server, user_id)
                                    users_text += user.name + "\n"
                            # No users are equipped -> State so
                            else:
                                users_text = "No users are equipped with this role."
                            # Reply with the equipped roles
                            await Utils.simple_embed_reply(channel, "[" + role.name + " Equipped List]", users_text,
                                                           hex_color)
                        # Hex parameter doesn't have an associated role -> Error
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Color not found.", hex_color)
                    # First parameter is not a valid hex value -> Error
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Invalid hex value.", split_message[1])
                # Hex parameter not supplied -> Error
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Missing color parameter.")
            # List all info known by this mod for current server
            elif command is self.commands["Color Info Command"]:
                # If roles exist
                if len(self.roles[server.id]) > 0:
                    # Begin reply crafting
                    embed = discord.Embed(title="[Info]", Utils.default_hex_color)
                    # Cycle all the roles, creating user list per role
                    for role_id in self.roles[server.id]:
                        role = Utils.get_role_by_id(server, role_id)
                        users_text = ""
                        for user_id in self.roles[server.id][role_id]:
                            user = Utils.get_user_by_id(server, user_id)
                            users_text += user.name + "\n"
                        # Create embed field per role
                        embed.add_field(name=role.name, value=users_text)
                    # Reply
                    await channel.send(embed=embed)
                # No used roles -> state so
                else:
                    await Utils.simple_embed_reply(channel, "[Info]", "No color exist.")
            # Purge a given role
            elif command is self.commands["Clear Colors Command"]:
                for role_id in [role for role in self.roles[server.id]]:
                    role = Utils.get_role_by_id(server, role_id)
                    # Delete the role
                    await self.delete_role(server, role)
                # Let the user know all
                await Utils.simple_embed_reply(channel, "[Purged Color]", "Purged all colors.")
        # Bot isn't supplied with sufficient perms -> Error
        except discord.errors.Forbidden as e:
            await Utils.simple_embed_reply(channel, "[Error]", "Bot does not have enough perms.")
            logging.exception("An error occurred.")
        # Some error I don't know of occurred, PING ALIEN!
        except Exception as e:  # Leave as a general exception!
            await Utils.simple_embed_reply(channel, "[Error]", "Unknown error occurred (Ping Alien).")
            logging.exception("An error occurred.")

    # Used to give a role to a user and record it in the mod DB
    async def give_role(self, server, user, role):
        old_role_id = self.users[server.id][user.id]
        # If the user has an old role -> Delete old role
        if old_role_id is not None:
            old_role = Utils.get_role_by_id(server, old_role_id)
            # If the role isn't what's needed -> Delete old role
            if old_role.name is not role.name:
                await self.remove_role(server, user, old_role)
        # Give role to user
        await Utils.client.add_roles(user, role)
        # Save new user role to user's data
        self.users[server.id][user.id] = role.id
        # Save user to the color's data
        # Color data exists        -> Append user id
        # Color data doesn't exist -> Create and append it
        if role.id in self.roles[server.id].keys():
            self.roles[server.id][role.id].append(user.id)
        else:
            self.roles[server.id][role.id] = [user.id]

    # Used to delete a role from the user and mod DB
    async def remove_role(self, server, user, role):
        # Remove role from user
        await Utils.client.remove_roles(user, role)
        # Remove the old role from the role list
        self.roles[server.id][role.id].remove(user.id)
        # Remove color from user's data
        self.users[server.id][user.id] = None
        # Delete the old role if it is not used
        if len(self.roles[server.id][role.id]) == 0:
            await self.delete_role(server, role)

    # Used to delete a role from the server and mod DB
    async def delete_role(self, server, role):
        # Delete role from the server
        await Utils.client.delete_role(server, role)
        for user_id in self.roles[server.id][role.id]:
            self.users[server.id][user_id] = None
        # Delete the role database
        del self.roles[server.id][role.id]

    # Used for creating a role (Specific for this mod)
    async def create_role(self, server, color):
        role = await Utils.client.create_role(server, name=color, color=Utils.get_color(color),
                                              permissions=discord.Permissions(permissions=0))
        self.roles[server.id][role.id] = []
        # Move it to top priority (so other roles's colors get over-written)
        await self.role_max_shift(server, role)
        return role

    # Used for bringing a color forward in viewing priority
    async def role_max_shift(self, server, role):
        try:
            pos = 1
            while True:
                await Utils.client.move_role(server, role, pos)
                pos += 1
        except (discord.Forbidden, discord.HTTPException):
            return

    # Used for getting a role by hex value in given server
    def get_role_by_hex(self, server, role_hex):
        return discord.utils.get(server.roles, name=role_hex)

    # Called when a member joins a server the bot is in
    async def on_member_join(self, member):
        pass

    # Called when a member joins a server the bot is in
    async def on_server_join(self, member):
        pass

    # Generates a fresh database on users and their color roles for every server the bot is in
    def generate_db(self):
        # Created a local DB based on live info (fresh DB)
        for server in Utils.client.guilds:
            # Create a user database for each server
            self.users[server.id], self.roles[server.id] = {}, {}
            for user in server.members:
                # Create a role database for each user
                self.users[server.id][user.id] = None
                for role in user.roles:
                    # If a user's role is a color -> Save it
                    if Utils.is_hex(role.name):
                        self.users[server.id][user.id] = role.id
                        if role.id in self.roles[server.id].keys():
                            self.roles[server.id][role.id].append(user.id)
                        else:
                            self.roles[server.id][role.id] = [user.id]
