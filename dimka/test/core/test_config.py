import unittest
import os.path
import tempfile
import argparse

import dimka.core.config as config


class TestConfig(unittest.TestCase):
    def test_correct_config(self):
        file = os.path.join(tempfile.gettempdir(), "conf.yaml")

        if os.path.isfile(file):
            os.remove(file)

        f = open(file, "a+")
        f.write("db_path: /var/www/data/test_app.sqlite3\n")
        f.write("key_path: /var/www/conf/keys.txt.dist\n")
        f.close()

        conf = config.Config()
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter
        )
        parser.add_argument("--config")

        result = conf.parse_config(parser.parse_args(["--config", file]))

        self.assertEqual(result.get('db_path'), '/var/www/data/test_app.sqlite3')
        self.assertEqual(result.get('key_path'), '/var/www/conf/keys.txt.dist')


if __name__ == '__main__':
    unittest.main()
