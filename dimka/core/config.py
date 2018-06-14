import os
import yaml
import errno
import argparse
import logging, verboselogs, coloredlogs


class Config(object):
    params = {}
    log = None

    def parse_config(self, args: argparse.Namespace) -> dict:
        """ Parse application config """
        if not os.path.isfile(args.config):
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                args.config,
            )

        with open(args.config, 'r') as stream:
            self.params = (yaml.load(stream))

        return self.params

    def init_logger(self, level: str, name: str) -> logging.Logger:
        """ Init application logger """
        handler = logging.StreamHandler()

        handler.setFormatter(logging.Formatter("%(asctime)s (%(name)s): %(message)s"))

        self.log = verboselogs.VerboseLogger(name, level)
        self.log.addHandler(handler)

        coloredlogs.install(level=level, logger=self.log)

        return self.log
