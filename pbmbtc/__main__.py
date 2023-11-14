import sys
from . import operation
from . import config
from . import bot
import logging

logging.basicConfig(level=logging.DEBUG)


help_str = """Pixiv bookmark backup on telegram channel
Usage:
    python -m pbmbtc run            run bot instance
    python -m pbmbtc init           init bot parameters
    python -m pbmbtc update         update bot parameter
In addition, most operations can be achieved by using tools such as sqlite3 to modify the data.db database file."""


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) == 0:
        print(help_str)

    elif args[0] == "init":
        operation.init()

    elif args[0] == "update":
        operation.update()

    elif args[0] == "add":
        operation.add_channel(args[1])

    elif args[0] == "delete":
        operation.delete_channel(args[1])

    elif args[0] == "run":
        config.load_config()
        bot.run()

    else:
        print(help_str)

