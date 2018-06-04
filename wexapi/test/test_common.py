import decimal
import random
import unittest

import wexapi
from wexapi.common import parse_json_response


# TODO: Add test for using WexConnection with a proxy.

class TestCommon(unittest.TestCase):
    def setUp(self):
        self.connection = wexapi.WexConnection()

    def tearDown(self):
        self.connection.close()
        self.connection = None

    def test_format_currency(self):
        self.assertEqual(wexapi.format_currency_digits(1.123456789, 1), "1.1")
        self.assertEqual(wexapi.format_currency_digits(1.123456789, 2), "1.12")
        self.assertEqual(wexapi.format_currency_digits(1.123456789, 3), "1.123")
        self.assertEqual(wexapi.format_currency_digits(1.123456789, 4), "1.1234")
        self.assertEqual(wexapi.format_currency_digits(1.123456789, 5), "1.12345")
        self.assertEqual(wexapi.format_currency_digits(1.123456789, 6), "1.123456")
        self.assertEqual(wexapi.format_currency_digits(1.123456789, 7), "1.1234567")

        self.assertEqual(wexapi.format_currency_digits(1.12, 3), "1.120")
        self.assertEqual(wexapi.format_currency_digits(44.0, 2), "44.00")

    def test_format_currency_by_pair(self):
        info = wexapi.APIInfo(self.connection)
        for i in info.pairs.values():
            d = i.decimal_places
            self.assertEqual(i.format_currency(1.12), wexapi.format_currency_digits(1.12, d))
            self.assertEqual(i.format_currency(44.0), wexapi.format_currency_digits(44.0, d))

            self.assertEqual(i.truncate_amount(44.0), wexapi.truncate_amount_digits(44.0, d))

            self.assertEqual(str(i.truncate_amount(1.12)), wexapi.format_currency_digits(1.12, d))

    def test_truncate_amount(self):
        info = wexapi.APIInfo(self.connection)
        for i in info.pairs.values():
            d = i.decimal_places
            self.assertEqual(i.truncate_amount(1.12), wexapi.truncate_amount_digits(1.12, d))
            self.assertEqual(i.truncate_amount(44.0), wexapi.truncate_amount_digits(44.0, d))

    def test_validate_pair(self):
        info = wexapi.APIInfo(self.connection)
        for pair in info.pair_names:
            info.validate_pair(pair)
        self.assertRaises(wexapi.InvalidTradePairException, info.validate_pair, "not_a_real_pair")

    def test_validate_pair_suggest(self):
        info = wexapi.APIInfo(self.connection)
        self.assertRaises(wexapi.InvalidTradePairException, info.validate_pair, "usd_btc")

    def test_validate_order(self):
        info = wexapi.APIInfo(self.connection)
        for pair in info.pair_names:
            t = random.choice(("buy", "sell"))
            a = random.random()
            if pair[4] == "btc":
                info.validate_order(pair, t, a, decimal.Decimal("0.001"))
            else:
                info.validate_order(pair, t, a, decimal.Decimal("0.1"))

            t = random.choice(("buy", "sell"))
            a = decimal.Decimal(str(random.random()))
            if pair[:4] == "btc_":
                self.assertRaises(
                    wexapi.InvalidTradeAmountException,
                    info.validate_order,
                    pair,
                    t,
                    a,
                    decimal.Decimal("0.0009999"),
                )
            else:
                self.assertRaises(
                    wexapi.InvalidTradeAmountException,
                    info.validate_order,
                    pair,
                    t,
                    a,
                    decimal.Decimal("0.000999"),
                )

        self.assertRaises(
            wexapi.InvalidTradePairException,
            info.validate_order,
            "foo_bar",
            "buy",
            decimal.Decimal("1.0"),
            decimal.Decimal("1.0"),
        )
        self.assertRaises(
            wexapi.InvalidTradeTypeException,
            info.validate_order,
            "btc_usd",
            "foo",
            decimal.Decimal("1.0"),
            decimal.Decimal("1.0"),
        )

    def test_parse_json_response(self):
        json1 = """
                {"asks":[[3.29551,0.5],[3.29584,5]],
                "bids":[[3.29518,15.51461],[3,27.5]]}
                """
        parsed = parse_json_response(json1)
        asks = parsed.get("asks")
        self.assertEqual(
            asks[0],
            [decimal.Decimal("3.29551"), decimal.Decimal("0.5")],
        )
        self.assertEqual(
            asks[1],
            [decimal.Decimal("3.29584"), decimal.Decimal("5")],
        )
        bids = parsed.get("bids")
        self.assertEqual(
            bids[0],
            [decimal.Decimal("3.29518"), decimal.Decimal("15.51461")],
        )
        self.assertEqual(
            bids[1],
            [decimal.Decimal("3"), decimal.Decimal("27.5")],
        )

    def test_parse_json_response_fail(self):
        json1 = """ \most /definitely *not ^json"""
        self.assertRaises(Exception, parse_json_response, json1)

    def test_pair_identity(self):
        info = wexapi.APIInfo(self.connection)
        self.assertEqual(len(info.pair_names), len(set(info.pair_names)))
        self.assertEqual(set(info.pairs.keys()), set(info.pair_names))

    def test_currency_sets(self):
        currencies_from_pairs = set()
        info = wexapi.APIInfo(self.connection)
        for pair in info.pair_names:
            c1, c2 = pair.split("_")
            currencies_from_pairs.add(c1)
            currencies_from_pairs.add(c2)

        self.assertEqual(len(info.currencies), len(set(info.currencies)))
        self.assertEqual(currencies_from_pairs, set(info.currencies))


if __name__ == '__main__':
    unittest.main()
