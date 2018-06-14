import argparse
import time
import logging
import wexapi
import os
from dimka.core import config, models


class Application:
    """ BitBot Application instance """

    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.__init_default_arguments()

        self.config = config.Config()
        self.log = logging.getLogger()

        self.args = None
        self.pair_info = None

    def init(self):
        self.args = self.__arg_parser.parse_args()
        self.__init_logger()
        self.__parse_config()
        self.__init_db_conn()

        self.config.params['bot_name'] = self.bot_name

    def run(self):
        key_path = self.config.params.get("key_path")
        with wexapi.keyhandler.KeyHandler(key_path) as handler:
            for key in handler.keys:
                name = "dimka.bot.{}.bot".format(self.bot_name.lower())
                mod = __import__(name, fromlist=[''])
                class_ = getattr(mod, "Bot")
                bot = class_(key, handler, self.config, self.args)

                while True:
                    try:
                        bot.run()

                        time.sleep(15)
                    except RestartBotException as e:
                        self.log.warning(str(e))
                        self.log.warning("Restart Bot")
                        time.sleep(e.timeout)
                        continue
                    except NotImplementedError as e:
                        self.log.error("{}".format(e))
                        break
                    except Exception as e:
                        self.log.exception("An error occurred: {}".format(e))
                        time.sleep(5)

    def add_argument(self, *args, **kwargs):
        """
        Add application console argument.
        Can be used to add specific bot arguments.
        """
        self.__arg_parser.add_argument(*args, **kwargs)

    def __parse_config(self):
        """ Parse application config """
        self.config.parse_config(self.args)

    def __init_logger(self):
        """ Initialize application logger """
        level = logging.WARNING
        if self.args.debug is True:
            level = logging.DEBUG

        self.log = self.config.init_logger(level, self.bot_name)

    def __init_db_conn(self):
        """ Initialize database """
        db_path = self.config.params.get("db_path")
        create = not os.path.isfile(db_path)

        self.log.notice("Initialize database:")
        self.log.notice("  DB Path: {}".format(db_path))

        db = models.database
        db.init(db_path)
        if create:
            self.log.notice("  Create tables")
            db.create_tables([
                models.OrderInfo,
                models.Ticker,
            ])

    def __init_default_arguments(self):
        """ Initialize ArgumentParser and set default arguments """
        self.__arg_parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter
        )
        self.__arg_parser.add_argument(
            "config",
            type=str,
            help="Application config yaml file (full path): /var/www/config/config.yaml",
        )
        self.__arg_parser.add_argument(
            "--debug",
            action="store_true",
            help="Show debug info",
        )
        # self.__arg_parser.add_argument(
        #     "--pair",
        #     default="ltc_usd",
        #     type=str,
        #     help="Trade pair. Format: btc_usd.",
        # )

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


class RestartBotException(RuntimeError):
    """ Exception to restart loop with bot.run """
    def __init__(self, *args, timeout: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = timeout

