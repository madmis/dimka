import unittest

import wexapi


class TestPublic(unittest.TestCase):
    def test_get_ticker(self):
        connection = wexapi.WexConnection()
        info = wexapi.APIInfo(connection)
        for pair in info.pair_names:
            wexapi.get_ticker(pair, connection, info)
            wexapi.get_ticker(pair, connection)
            wexapi.get_ticker(pair, info=info)
            wexapi.get_ticker(pair)

    def test_get_history(self):
        connection = wexapi.WexConnection()
        info = wexapi.APIInfo(connection)
        for pair in info.pair_names:
            wexapi.get_trade_history(pair, connection, info)
            wexapi.get_trade_history(pair, connection)
            wexapi.get_trade_history(pair, info=info)
            wexapi.get_trade_history(pair)

    def test_get_depth(self):
        connection = wexapi.WexConnection()
        info = wexapi.APIInfo(connection)
        for pair in info.pair_names:
            wexapi.get_depth(pair, connection, info)
            wexapi.get_depth(pair, connection)
            wexapi.get_depth(pair, info=info)
            wexapi.get_depth(pair)


if __name__ == '__main__':
    unittest.main()
