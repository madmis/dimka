import unittest
import os.path
import tempfile
import sys

from dimka.core.app import Application


class TestConfig(unittest.TestCase):
    conf = os.path.join(tempfile.gettempdir(), "conf.yaml")
    db = os.path.join(tempfile.gettempdir(), "db.sqlite3")

    def tearDown(self):
        super().tearDown()
        if os.path.isfile(self.conf):
            os.remove(self.conf)

        if os.path.isfile(self.db):
            os.remove(self.db)

    def test_app_create_database(self):
        self._create_config(self.conf, self.db)

        self.assertFalse(os.path.isfile(self.db))

        sys.argv = ["--config", self.conf]
        app = Application('bot')
        app.init()

        self.assertTrue(os.path.isfile(self.db))

    def _create_config(self, conf, db_path):
        if os.path.isfile(conf):
            os.remove(conf)

        if os.path.isfile(db_path):
            os.remove(db_path)

        f = open(conf, "a+")
        f.write("db_path: {}\n".format(db_path))
        f.write("key_path: /tmp/keys.txt\n")
        f.close()


if __name__ == '__main__':
    unittest.main()
