from decimal import Decimal, ROUND_HALF_DOWN
import unittest

import dimka.core.utils as utils


class TestUtils(unittest.TestCase):
    def test_truncate_digits(self):
        self.assertIsInstance(
            utils.truncate_digits(1, 0),
            Decimal,
        )
        self.assertEqual(
            str(utils.truncate_digits(1, 5)),
            str(Decimal('1.00000')),
        )
        self.assertEqual(
            str(utils.truncate_digits(0.5689, 3, rounding=ROUND_HALF_DOWN)),
            str(Decimal('0.569')),
        )

        self.assertEqual(
            str(utils.truncate_digits(1.0, 16)),
            str(Decimal('1.{}'.format('0' * 15))),
        )
        self.assertEqual(
            str(utils.truncate_digits('0.345', 2)),
            str(Decimal('0.34')),
        )

    def test_truncate_digits_alias(self):
        self.assertIsInstance(
            utils.td(1, 0),
            Decimal,
        )

        self.assertEqual(
            str(utils.truncate_digits('0.345', 2)),
            str(utils.td(0.345, 2)),
        )


if __name__ == '__main__':
    unittest.main()
