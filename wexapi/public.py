# Public API v3 description: https://wex.nz/api/3/docs

from decimal import Decimal
from collections import namedtuple

from html import unescape
from . import common, scraping

PairInfoBase = namedtuple(
    "PairInfoBase",
    ["decimal_places", "min_price", "max_price", "min_amount", "hidden", "fee"],
)


class PairInfo(PairInfoBase):
    def format_currency(self, value) -> str:
        """
        :param value: int|float|str|decimal.Decimal
        :return: str
        """
        return common.format_currency_digits(value, self.decimal_places)

    def truncate_amount(self, value) -> Decimal:
        """
        :param value: int|float|str|Decimal
        :return: str
        """
        return common.truncate_amount_digits(value, self.decimal_places)

    def validate_order(self, trade_type: str, rate, amount):
        """

        :param trade_type:
        :param rate:
        :param amount:
        :return:
        """
        if trade_type not in ("buy", "sell"):
            raise common.InvalidTradeTypeException("Unrecognized trade type: %r" % trade_type)

        formatted_min_amount = self.format_currency(self.min_amount)
        if amount < self.min_amount:
            msg = "Trade amount %r too small; should be >= %s" % (amount, formatted_min_amount)
            raise common.InvalidTradeAmountException(msg)


class APIInfo(object):
    def __init__(self, connection):
        self.connection = connection
        self.currencies = None
        self.pair_names = None
        self.pairs = None
        self.server_time = None

        self._scrape_pair_index = 0

        self.update()

    def update(self):
        info = self.connection.make_json_request("/api/3/info")
        if type(info) is not dict:
            raise TypeError("The response is not a dict.")

        self.server_time = info.get(u"server_time")

        pairs = info.get(u"pairs")
        if type(pairs) is not dict:
            raise TypeError("The pairs item is not a dict.")

        self.pairs = {}
        currencies = set()
        for name, data in pairs.items():
            self.pairs[name] = PairInfo(**data)
            a, b = name.split(u"_")
            currencies.add(a)
            currencies.add(b)

        self.currencies = list(currencies)
        self.currencies.sort()

        self.pair_names = list(self.pairs.keys())
        self.pair_names.sort()

    def validate_pair(self, pair):
        if pair not in self.pair_names:
            if "_" in pair:
                a, b = pair.split("_", 1)
                swapped_pair = "%s_%s" % (b, a)
                if swapped_pair in self.pair_names:
                    msg = "Unrecognized pair: %r (did you mean %s?)"
                    msg = msg % (pair, swapped_pair)
                    raise common.InvalidTradePairException(msg)
            raise common.InvalidTradePairException("Unrecognized pair: %r" % pair)

    def get_pair_info(self, pair):
        self.validate_pair(pair)
        return self.pairs[pair]

    def validate_order(self, pair, trade_type, rate, amount):
        # import ipdb
        # ipdb.set_trace()

        self.validate_pair(pair)

        pair_info = self.pairs[pair]
        pair_info.validate_order(trade_type, rate, amount)

    def format_currency(self, pair, amount):
        self.validate_pair(pair)

        pair_info = self.pairs[pair]
        return pair_info.format_currency(amount)

    def scrape_main_page(self):
        parser = scraping.BTCEScraper()

        # Rotate through the currency pairs between chat requests so that the
        # chat pane contents will update more often than every few minutes.
        self._scrape_pair_index = (self._scrape_pair_index + 1) % len(self.pair_names)
        current_pair = self.pair_names[self._scrape_pair_index]

        response = self.connection.make_request('/exchange/%s' % current_pair, with_cookie=True)

        parser.feed(unescape(response.decode('utf-8')))
        parser.close()

        r = scraping.ScraperResults()
        r.messages = parser.messages
        r.dev_online = parser.dev_online
        r.support_online = parser.support_online
        r.admin_online = parser.admin_online

        return r


Ticker = namedtuple(
    "Ticker",
    ["high", "low", "avg", "vol", "vol_cur", "last", "buy", "sell", "updated"],
)


def get_ticker(pair, connection=None, info=None):
    """
    Retrieve the ticker for the given pair.  Returns a Ticker instance.
    """

    if info is not None:
        info.validate_pair(pair)

    if connection is None:
        connection = common.WexConnection()

    response = connection.make_json_request("/api/3/ticker/%s" % pair)

    if type(response) is not dict:
        raise TypeError("The response is a %r, not a dict." % type(response))
    elif u'error' in response:
        print("There is a error \"%s\" while obtaining ticker %s" % (response['error'], pair))
        ticker = None
    else:
        ticker = Ticker(**response[pair])

    return ticker


def get_depth(pair, connection=None, info=None):
    """Retrieve the depth for the given pair.  Returns a tuple (asks, bids);
    each of these is a list of (price, volume) tuples."""

    if info is not None:
        info.validate_pair(pair)

    if connection is None:
        connection = common.WexConnection()

    response = connection.make_json_request("/api/3/depth/%s" % pair)
    if type(response) is not dict:
        raise TypeError("The response is not a dict.")

    depth = response.get(pair)
    if type(depth) is not dict:
        raise TypeError("The pair depth is not a dict.")

    asks = depth.get(u'asks')
    if type(asks) is not list:
        raise TypeError("The response does not contain an asks list.")

    bids = depth.get(u'bids')
    if type(bids) is not list:
        raise TypeError("The response does not contain a bids list.")

    return asks, bids


Trade = namedtuple(
    "Trade",
    ['pair', 'type', 'price', 'tid', 'amount', 'timestamp', ],
)


def get_trade_history(pair, connection=None, info=None, count=None):
    """
    Retrieve the trade history for the given pair.  Returns a list of
    Trade instances.  If count is not None, it should be an integer, and
    specifies the number of items from the trade history that will be
    processed and returned.
    """

    if info is not None:
        info.validate_pair(pair)

    if connection is None:
        connection = common.WexConnection()

    response = connection.make_json_request("/api/3/trades/%s" % pair)
    if type(response) is not dict:
        raise TypeError("The response is not a dict.")

    history = response.get(pair)
    if type(history) is not list:
        raise TypeError("The response is a %r, not a list." % type(history))

    result = []

    # Limit the number of items returned if requested.
    if count is not None:
        history = history[:count]

    for h in history:
        h["pair"] = pair
        t = Trade(**h)
        result.append(t)
    return result
