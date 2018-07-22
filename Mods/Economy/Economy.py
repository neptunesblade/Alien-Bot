import re

import discord

import Common.DataManager as DataManager
from Common import Utils
from Common.Mod import Mod
import random


# TODO: Major commenting needed
class Economy(Mod):
    def __init__(self, mod_name, embed_color):
        # General var init
        self.users = {}
        self.roles = {}
        self.name = mod_name
        self.embed_color = embed_color
        # Config var init
        self.config = DataManager.JSON("Mods/Economy/EconomyConfig.json")
        # Database var init
        self.database = DataManager.add_manager("bank_database", "Mods/Economy/Bank.db",
                                                file_type=DataManager.FileType.SQL)
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Generate and Update DB
        self.generate_db()
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        server, channel, author = message.server, message.channel, message.author
        if command is self.commands["Set Currency Command"]:
            if len(split_message) > 1:
                self.config.write_data(split_message[1], key="Currency")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Currency parameter not supplied.")
        elif command is self.commands["Set Starting Balance Command"]:
            if len(split_message) > 1:
                starting_balance = split_message[1]
                if starting_balance.isdigit():
                    self.config.write_data(int(starting_balance), key="Starting Balance")
                    await Utils.simple_embed_reply(message.channel, "[Success]",
                                                   "Starting balance set to `" + starting_balance + "`.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]",
                                                   "Starting balance command parameter is not a digit.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]",
                                               "Starting balance command parameter not supplied.")
        elif command is self.commands["Set Payout Command"]:
            await self.set_income_min_max(message, is_payout=True)
        elif command is self.commands["Set Deduction Command"]:
            await self.set_income_min_max(message, is_payout=False)
        elif command is self.commands["Balance Command"]:
            user_balance = self.database.execute("SELECT balance FROM '" + server.id + "' WHERE user='" +
                                                 author.id + "'LIMIT 1")[0]
            await Utils.simple_embed_reply(channel, "[Balance]", str(user_balance) + self.config.get_data("Currency"))
        # TODO: Determine how to calculate success chance
        elif command is self.commands["Rob Command"]:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Awaiting method of calculating success rate")
        elif command is self.commands["Work Command"]:
            await self.roll_income(message, "Work Command")
        elif command is self.commands["Slut Command"]:
            await self.roll_income(message, "Slut Command")
        elif command is self.commands["Crime Command"]:
            await self.roll_income(message, "Crime Command")
        elif command is self.commands["Set Success Rate Command"]:
            if len(split_message) > 2:
                income_command = split_message[1]
                new_rate = split_message[2]
                if income_command == "slut" or "work" or "crime":
                    income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                    if new_rate.isdigit():
                        new_rate = int(new_rate)
                        if 0 <= new_rate <= 100:
                            economy_config = self.config.get_data()
                            economy_config["Commands"][income_command]["Success Rate"] = new_rate
                            self.config.write_data(economy_config)
                            await Utils.simple_embed_reply(message.channel, "[Success]", "`" + income_command +
                                                           "` success rate set to " + str(new_rate) + "%.")
                        else:
                            await Utils.simple_embed_reply(message.channel, "[Error]",
                                                           "Success rate parameter not between 0 and 100.")
                    else:
                        await Utils.simple_embed_reply(message.channel, "[Error]",
                                                       "Success rate parameter is not a digit.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Add Success Reply Command"]:
            await self.set_income_reply(message, is_success=True)
        elif command is self.commands["Add Failure Reply Command"]:
            await self.set_income_reply(message, is_success=False)
        elif command is self.commands["List Success Reply Command"]:
            await self.list_reply_commands(message, is_success=True)
        elif command is self.commands["List Failure Reply Command"]:
            await self.list_reply_commands(message, is_success=False)
        elif command is self.commands["Delete Success Reply Command"]:
            await self.delete_command_reply(message, True)
        elif command in self.commands["Delete Failure Reply Command"]:
            await self.delete_command_reply(message, False)

    # TODO: Add max reply message count and length limits
    async def set_income_reply(self, message, is_success):
        server, channel, author = message.server, message.channel, message.author
        split_message = message.content.split(" ")
        if len(split_message) > 2:
            income_command = split_message[1]
            reply = message.content[len(split_message[0]) + len(split_message[1]) + 2:]
            if income_command == "slut" or "work" or "crime":
                income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                economy_config = self.config.get_data()
                reply_type = "Success" if is_success else "Failure"
                # Check to make sure that and {user_id}s supplied are valid
                for section in reply.split(" "):
                    if re.fullmatch(r"{[0-9]{18}}", section) is not None:
                        if Utils.get_user_by_id(server, section[1:-1]) is None:
                            return await Utils.simple_embed_reply(channel, "[Error]",
                                                                  "User ID`" + section[1:-1] + "` not found.")
                economy_config["Commands"][income_command][reply_type]["Messages"].append(reply)
                self.config.write_data(economy_config)
                await Utils.simple_embed_reply(message.channel, "[Success]", "Added `" + reply + "` to `" +
                                               income_command + "`'s replies.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # TODO: Compress by putting the re-used code into a func
    # Called when a member joins a server the bot is in
    async def on_member_join(self, member):
        user_id = member.id
        server_id = member.server.id
        if len(self.database.execute("SELECT balance FROM '" + server_id + "' WHERE user=" + str(
                user_id) + " LIMIT 1")) == 0:
            self.database.execute("INSERT INTO '" + server_id + "' VALUES('" + user_id + "', " +
                                  str(self.config.get_data("Starting Balance")) + ", 0)")

    # Pics a random win/loss based on the command and prints a win/loss message respectively
    async def roll_income(self, message, command_name):
        server, channel, author = message.server, message.channel, message.author
        command_config = self.config.get_data(key="Commands")[command_name]
        user_balance = int(self.database.execute("SELECT balance FROM '" + server.id + "' WHERE user='" + author.id
                                                 + "' LIMIT 1")[0])
        # Success, pick message and payout
        if roll(int(self.config.get_data(key="Commands")[command_name]["Success Rate"])):
            payout_range = command_config["Success"]["Payout"]
            balance_change = random.randint(payout_range["Min"], payout_range["Max"])
            success_messages = command_config["Success"]["Messages"]
            reply = success_messages[rng(len(success_messages) - 1)]
        # Failure, pick message and deduction
        else:
            deduction_range = command_config["Failure"]["Deduction"]
            balance_change = random.randint(deduction_range["Min"], deduction_range["Max"]) * -1
            failure_messages = command_config["Failure"]["Messages"]
            reply = failure_messages[rng(len(failure_messages) - 1)]
        self.database.execute("UPDATE '" + server.id + "' SET balance=" + str(user_balance + balance_change) +
                              " WHERE user='" + author.id + "'")
        for section in reply.split(" "):
            if re.fullmatch(r"{[0-9]{18}}", section) is not None:
                reply = reply.replace(section, Utils.get_user_by_id(server, section[1:-1]).mention)
        await Utils.simple_embed_reply(channel, "[" + str(author) + "]", reply.replace("{amount}",
                                                                                       str(abs(balance_change)) +
                                                                                       self.config.get_data(
                                                                                           key="Currency")))

    # Generates the bank DB
    def generate_db(self):
        for server in Utils.client.servers:
            self.database.execute("CREATE TABLE IF NOT EXISTS '" + server.id + "'(user TEXT, balance REAL, bank REAL)")
            for user in server.members:
                if len(self.database.execute("SELECT balance FROM '" + server.id + "' WHERE user=" + str(
                        user.id) + " LIMIT 1")) == 0:
                    self.database.execute("INSERT INTO '" + server.id + "' VALUES('" + user.id + "', " +
                                          str(self.config.get_data("Starting Balance")) + ", 0)")

    # Sets the range for a given income command
    async def set_income_min_max(self, message, is_payout):
        split_message = message.content.split(" ")
        success_type, change_type = ("Success", "Payout") if is_payout else ("Failure", "Deduction")
        if len(split_message) > 3:
            income_command, minimum, maximum = split_message[1], split_message[2], split_message[3]
            if income_command == "slut" or "work" or "crime":
                income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                if minimum.isdigit():
                    if maximum.isdigit():
                        # Make sure the minimum is lower than the maximum
                        minimum, maximum = (minimum, maximum) if minimum < maximum else (maximum, minimum)
                        economy_config = self.config.get_data()
                        min_max_config = economy_config["Commands"][income_command][success_type][change_type]
                        min_max_config["Min"], min_max_config["Max"] = int(minimum), int(maximum)
                        self.config.write_data(economy_config)
                        await Utils.simple_embed_reply(message.channel, "[Success]",
                                                       "The `" + income_command + "` now has a " + change_type +
                                                       " between " + minimum + " and " + maximum)
                    else:
                        await Utils.simple_embed_reply(message.channel, "[Error]",
                                                       "Maximum parameter is not a digit.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]",
                                                   "Minimum parameter is not a digit.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # Deletes a success/failure reply message given an ID
    async def delete_command_reply(self, message, is_success):
        server, channel, author = message.server, message.channel, message.author
        split_message = message.content.split(" ")
        if len(split_message) > 2:
            reply_type = "Success" if is_success else "Failure"
            income_command, index = split_message[1], split_message[2]
            if income_command == "slut" or "work" or "crime":
                if index.isdigit():
                    income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                    economy_config = self.config.get_data()
                    messages = economy_config["Commands"][income_command][reply_type]["Messages"]
                    message_to_remove = messages[int(index)]
                    messages.remove(message_to_remove)
                    self.config.write_data(economy_config)
                    await Utils.simple_embed_reply(message.channel, "[Success]",
                                                   "Deleted `" + message_to_remove + "` from `" + income_command + "`.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]", "ID parameter is not a digit.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # Lists all the success or failure reply messages for an income command
    async def list_reply_commands(self, message, is_success):
        server, channel, author = message.server, message.channel, message.author
        split_message = message.content.split(" ")
        if len(split_message) > 1:
            reply_type = "Success" if is_success else "Failure"
            income_command = split_message[1]
            if income_command == "slut" or "work" or "crime":
                income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                current_index = 0
                embed = discord.Embed(title="[Reply Messages]", color=discord.Color(int("0x751DDF", 16)))
                messages = self.config.get_data(key="Commands")[income_command][reply_type]["Messages"]
                max_number_length = len(str(len(messages)))
                embed_text = ""
                for reply_message in messages:
                    current_index += 1
                    if len(reply_message) > 50 - max_number_length:
                        embed_text += reply_message[0: 50 - max_number_length - 3] + "...\n"
                    else:
                        embed_text += reply_message + "\n"
                embed.add_field(name="ID", value=''.join([str(i) + "\n" for i in range(current_index)]), inline=True)
                embed.add_field(name="Message", value=embed_text, inline=True)
                await Utils.client.send_message(channel, embed=embed)
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")


def roll(success_percent_chance):
    if success_percent_chance > random.randint(0, 100):
        return True
    return False


def rng(max_value):
    # Some more RNG
    random.seed(random.randint(0, 1000))
    return random.randint(0, max_value)
