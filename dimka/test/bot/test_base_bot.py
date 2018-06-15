from argparse import Namespace
from decimal import Decimal
from pathlib import Path
import unittest
from unittest.mock import patch, mock_open
import vcr
import os

from wexapi.keyhandler import KeyHandler
import dimka.bot.base_bot as base_bot
import dimka.core as core

FIXTURE_DIR = Path(__file__).parent.resolve() / "fixtures"

file = "/tmp/keys.tmp"


class TestBaseBot(unittest.TestCase):
    # @patch("builtins.open", new_callable=mock_open, read_data="data")
    # def test_patch(mock_file):
    #     assert open("path/to/open").read() == "data"
    #     mock_file.assert_called_with("path/to/open")

    @classmethod
    @vcr.use_cassette(str(FIXTURE_DIR / "init_bot.yaml"))
    def setUpClass(cls):
        with open(file, 'a') as f:
            f.write("key\nsecret\n1")

        cls.config = core.config.Config()
        cls.config.params = {
            "db_path": ":memory:",
            "pair": "ppc_usd",
            "pair_units": "4",
        }

        key = 'key'
        handler = KeyHandler(file)
        cls.bot = base_bot.BaseBot(
            key,
            handler,
            cls.config,
            Namespace(step=3)
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(file):
            os.remove(file)


    def test_split_pair(self):
        self.assertEqual(self.bot.split_pair(), ("ppc", "usd"))

    @vcr.use_cassette(str(FIXTURE_DIR / "test_funds.yaml"))
    def test_funds(self):
        self.assertEqual(self.bot.funds(), (Decimal("0"), Decimal("0.00083385")))

    def test_units(self):
        self.assertIsInstance(self.bot.units(), int)
        self.assertEqual(self.bot.units(), 4)

    def test_get_price_unit(self):
        self.assertEqual(self.bot.get_price_unit(), Decimal("0.001"))

    @vcr.use_cassette(str(FIXTURE_DIR / "test_low_high_daily_prices.yaml"))
    def test_low_high_daily_prices(self):
        self.assertEqual(self.bot.low_high_daily_prices(), (Decimal('1.64'), Decimal('1.76')))


if __name__ == '__main__':
    unittest.main()
