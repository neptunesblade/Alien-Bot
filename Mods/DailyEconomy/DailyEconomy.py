from Common import DataManager, Utils
from Common.Mod import Mod
import discord
import random
import re

try:
    from Mods.Economy import EconomyUtils
except ImportError:
    raise Exception("Economy mod not installed")


class DailyEconomy(Mod):
    def __init__(self, mod_name, embed_color):
        # Config var init
        self.config = DataManager.JSON("Mods/DailyEconomy/DailyEconomyConfig.json")
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        server, channel, author = message.guild, message.channel, message.author
        if command is self.commands["Set Default Success Rate Command"]:
            if len(split_message) > 2:
                income_command = split_message[1]
                new_rate = split_message[2]
                if income_command in ("slut", "work", "crime"):
                    income_command = get_income_command(income_command)
                    if new_rate.isdigit():
                        new_rate = int(new_rate)
                        if 0 <= new_rate <= 100:
                            economy_config = self.config.get_data()
                            economy_config["Commands"][income_command]["Default Success Rate"] = new_rate
                            self.config.write_data(economy_config)
                            await Utils.simple_embed_reply(channel, "[Success]", "`" + income_command +
                                                           "` default success rate set to " + str(new_rate) + "%.")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]",
                                                           "Success rate parameter not between 0 and 100.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]",
                                                       "Success rate parameter is incorrect.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Income command parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
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
        elif command is self.commands["Delete Failure Reply Command"]:
            await self.delete_command_reply(message, False)
        elif command is self.commands["Set Payout Command"]:
            await self.set_income_min_max(message, is_payout=True)
        elif command is self.commands["Set Deduction Command"]:
            await self.set_income_min_max(message, is_payout=False)
        elif command is self.commands["Work Command"]:
            await self.roll_income(message, "Work Command")
        elif command is self.commands["Slut Command"]:
            await self.roll_income(message, "Slut Command")
        elif command is self.commands["Crime Command"]:
            await self.roll_income(message, "Crime Command")
        # TODO: Determine how to calculate success chance for the Rob Command
        elif command is self.commands["Rob Command"]:
            await Utils.simple_embed_reply(channel, "[Error]", "Awaiting method of calculating success rate")

    async def set_income_reply(self, message, is_success):
        server, channel, author = message.guild, message.channel, message.author
        split_message = message.content.split(" ")
        if len(split_message) > 2:
            income_command = split_message[1].lower()
            reply = message.content[len(split_message[0]) + len(split_message[1]) + 2:]
            if len(reply) < 1500:
                if income_command in ("slut", "work", "crime"):
                    income_command = get_income_command(income_command)
                    economy_config = self.config.get_data()
                    reply_type = "Success" if is_success else "Failure"
                    # Check to make sure that and {user_id}s supplied are valid
                    for section in reply.split(" "):
                        if re.fullmatch(r"{[0-9]{18}}", section) is not None:
                            if Utils.get_user_by_id(server, section[1:-1]) is None:
                                return await Utils.simple_embed_reply(channel, "[Error]",
                                                                      "User ID `" + section[1:-1] + "` not found.")
                    economy_config["Commands"][income_command][reply_type]["Messages"].append(reply)
                    self.config.write_data(economy_config)
                    await Utils.simple_embed_reply(message.channel, "[Success]", "Added `" + reply + "` to `" +
                                                   income_command + "`'s replies.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]",
                                               "Reply message is too long - it must be < 1500 characters")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # TODO: Add pages
    # Lists all the success or failure reply messages for an income command
    async def list_reply_commands(self, message, is_success):
        server, channel, author = message.guild, message.channel, message.author
        split_message = message.content.split(" ")
        if len(split_message) > 1:
            reply_type = "Success" if is_success else "Failure"
            income_command = split_message[1].lower()
            if income_command in ("slut", "work", "crime"):
                income_command = get_income_command(income_command)
                current_index = 0
                messages = self.config.get_data(key="Commands")[income_command][reply_type]["Messages"]
                if len(messages) > 0:
                    # Get the length of the largest number (EX: "100" = 3, "10" = 2)
                    max_number_length = len(str(len(messages)))
                    embed_text = ""
                    for reply_message in messages:
                        current_index += 1
                        if len(reply_message) > 50 - max_number_length:
                            embed_text += reply_message[0: 50 - max_number_length - 3] + "...\n"
                        else:
                            embed_text += reply_message + "\n"
                    embed = discord.Embed(title="[Reply Messages]",
                                          color=Utils.default_hex_color)
                    embed.add_field(name="ID", value=''.join([str(i) + "\n" for i in range(current_index)]),
                                    inline=True)
                    embed.add_field(name="Message", value=embed_text, inline=True)
                    await channel.send(embed=embed)
                else:
                    await Utils.simple_embed_reply(message.channel, "[Reply Messages]", "There are no replies.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter is incorrect.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # Deletes a success/failure reply message given an ID
    async def delete_command_reply(self, message, is_success):
        split_message = message.content.split(" ")
        if len(split_message) > 2:
            reply_type = "Success" if is_success else "Failure"
            income_command, index = split_message[1].lower(), split_message[2]
            if income_command in ("slut", "work", "crime"):
                if index.isdigit():
                    index = int(index)
                    income_command = get_income_command(income_command)
                    economy_config = self.config.get_data()
                    messages = economy_config["Commands"][income_command][reply_type]["Messages"]
                    if index < len(messages):
                        message_to_remove = messages[index]
                        messages.remove(message_to_remove)
                        self.config.write_data(economy_config)
                        await Utils.simple_embed_reply(message.channel, "[Success]",
                                                       "Deleted `" + message_to_remove + "` from `" + income_command +
                                                       "`.")
                    else:
                        await Utils.simple_embed_reply(message.channel, "[Error]", "Given ID not found.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]", "ID parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter is incorrect.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # Sets the range for a given income command
    async def set_income_min_max(self, message, is_payout):
        split_message = message.content.split(" ")
        success_type, change_type = ("Success", "Payout") if is_payout else ("Failure", "Deduction")
        if len(split_message) > 3:
            income_command, minimum, maximum = split_message[1].lower(), split_message[2], split_message[3]
            if income_command in ("slut", "work", "crime"):
                income_command = get_income_command(income_command)
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
                                                       "Maximum parameter is incorrect.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]",
                                                   "Minimum parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter is incorrect.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # Pics a random win/loss based on the command and prints a win/loss message respectively
    async def roll_income(self, message, command_name):
        server, channel, author = message.guild, message.channel, message.author
        command_config = self.config.get_data(key="Commands")[command_name]
        user_cash = EconomyUtils.get_cash(server.id, author.id)
        # Pick success or failure
        win_mode, change_mode, balance_change = ("Success", "Payout", 1) if roll(
            int(self.config.get_data(key="Commands")[command_name]["Default Success Rate"])) else (
            "Failure", "Deduction", -1)
        balance_change_range = command_config[win_mode][change_mode]
        cash_change = random.randint(balance_change_range["Min"], balance_change_range["Max"]) * balance_change
        messages = command_config[win_mode]["Messages"]
        if len(messages) > 0:
            reply = messages[rng(len(messages) - 1)]
            EconomyUtils.set_cash(server.id, author.id, user_cash + cash_change)
            for section in reply.split(" "):
                if re.fullmatch(r"{[0-9]{18}}", section) is not None:
                    reply = reply.replace(section, Utils.get_user_by_id(server, section[1:-1]).mention)
            await Utils.simple_embed_reply(channel, "[" + str(author) + "]", reply.replace("{amount}",
                                                                                           str(abs(cash_change)) +
                                                                                           EconomyUtils.currency))
        else:
            await Utils.simple_embed_reply(channel, "[" + str(author) + "]", str(cash_change) + EconomyUtils.currency)


def get_income_command(text):
    if text == "slut":
        return "Slut Command"
    if text == "work":
        return "Work Command"
    if text == "crime":
        return "Crime Command"
    return None


# Roll a True/Fall with a given success chance
def roll(success_percent_chance):
    if success_percent_chance > random.randint(0, 100):
        return True
    return False


# Returns a random number between 0 and max_value
def rng(max_value):
    # Some more RNG
    random.seed(random.randint(0, 1000))
    return random.randint(0, max_value)
