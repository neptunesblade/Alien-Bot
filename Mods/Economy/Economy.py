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
        if command is self.commands["Balance Command"]:
            user_balance = self.database.execute("SELECT balance FROM '" + server.id + "' WHERE user='" +
                                                 author.id + "'LIMIT 1")[0]
            await Utils.simple_embed_reply(channel, "[Balance]", str(user_balance) + self.config.get_data("Currency"))
        elif command is self.commands["Set Currency Command"]:
            if len(split_message) > 1:
                self.config.write_data(split_message[1], key="Currency")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Currency parameter not supplied.")
        elif command is self.commands["Rob Command"]:
            await self.roll_income(message, "Rob Command")
        elif command is self.commands["Work Command"]:
            await self.roll_income(message, "Work Command")
        elif command is self.commands["Slut Command"]:
            await self.roll_income(message, "Slut Command")
        elif command is self.commands["Crime Command"]:
            await self.roll_income(message, "Crime Command")
        elif command is self.commands["Set Rob Command"]:
            await self.set_chance(message, "Rob Command")
        elif command is self.commands["Set Work Command"]:
            await self.set_chance(message, "Work Command")
        elif command is self.commands["Set Slut Command"]:
            await self.set_chance(message, "Slut Command")
        elif command is self.commands["Set Crime Command"]:
            await self.set_chance(message, "Crime Command")

    # Called when a member joins a server the bot is in
    async def on_member_join(self, member):
        pass

    async def set_chance(self, message, command_name):
        split_message = message.content.split(" ")
        if len(split_message) > 1:
            new_rate = split_message[1]
            economy_config = self.config.get_data()
            economy_config["Commands"][command_name]["Success Rate"] = new_rate
            self.config.write_data(economy_config)
            await Utils.simple_embed_reply(message.channel, "[Success]", "\"" + command_name +
                                           "\" success rate set to " + str(new_rate) + "%.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Currency parameter not supplied.")

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
        await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                       reply.replace("{$}", str(abs(balance_change)) +
                                                     self.config.get_data(key="Currency")))

    # Generates the bank DB and removes old data
    def generate_db(self):
        for server in Utils.client.servers:
            self.database.execute("CREATE TABLE IF NOT EXISTS '" + server.id + "'(user TEXT, balance REAL, bank REAL)")
            for user in server.members:
                if len(self.database.execute("SELECT balance FROM '" + server.id + "' WHERE user=" + str(
                        user.id) + " LIMIT 1")) == 0:
                    self.database.execute("INSERT INTO '" + server.id + "' VALUES('" + user.id + "', " +
                                          str(self.config.get_data("Starting Balance")) + ", 0)")


def roll(success_percent_chance):
    if success_percent_chance > random.randint(0, 100):
        return True
    return False


def rng(max_value):
    return random.randint(0, max_value)
