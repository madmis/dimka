from argparse import Namespace
import datetime
from decimal import Decimal, ROUND_UP
from typing import Tuple, List

from dimka.core.config import Config
import dimka.core.utils as utils
import dimka.core.models as bot_models
from wexapi.keyhandler import KeyHandler
from wexapi.common import WexConnection
from wexapi.trade import TradeApi
from wexapi.public import InfoApi, PublicApi

import wexapi.models as models


class BaseBot(object):
    def __init__(self, key: str, key_handler: KeyHandler, config: Config, args: Namespace):
        self.key = key
        self.key_handler = key_handler
        self.params = config.params
        self.pair = config.params.get("pair")
        self.logger = config.log
        self.args = args
        self.pair_info = InfoApi(WexConnection()).get_pair_info(
            config.params.get("pair")
        )

    def run(self):
        raise NotImplementedError(
            "{} bot: should implement run() method.".format(
                self.params.get("bot_name")
            )
        )

    def split_pair(self) -> Tuple[str, str]:
        """
        :return: base, quote assets
        """
        base, quote = self.pair.split("_")

        return base, quote

    def funds(self) -> Tuple[Decimal, Decimal]:
        """
        Get account funds according to trading pair:
            base coin, quote (secondary) coin (from current pair)

        Returns:
            Tuple[Decimal, Decimal]: first - is base coin funds, second - quote coin funds
        """
        with WexConnection() as conn:
            t = TradeApi(self.key, self.key_handler, conn)
            r = t.get_info()

            base, quote = self.split_pair()

            return r.funds[base], r.funds[quote]

    def active_orders(self, orders_type: str = None) -> List[models.Order]:
        """
        Get active orders list.
        If defined type (buy, sell) return orders with this type
        """
        with WexConnection() as conn:
            t = TradeApi(self.key, self.key_handler, conn)

            orders = t.active_orders(self.pair)

            if orders_type is not None:
                result = []
                for order in orders:
                    if order.type == orders_type:
                        result.append(order)

                return result

            return orders

    def units(self) -> int:
        """ Pair currencies decimal units """
        return int(self.params.get("pair_units", 8))

    def cancel_buy_orders(self):
        """ Cancel all opened BUY orders """
        buy_orders = self.active_orders('buy')

        if len(buy_orders) > 0:

            self.logger.warning("Cancel all opened BUY orders: {}".format(len(buy_orders)))

            with WexConnection() as conn:
                t = TradeApi(self.key, self.key_handler, conn)

                for order in buy_orders:
                    result = t.cancel_order(order.order_id)
                    self.logger.debug("  Canceled order #{}".format(result.order_id))

    def top_sell_price(self) -> Decimal:
        """ Top sell price - top price from sell queue """
        with WexConnection() as conn:
            asks, _ = PublicApi(conn).get_depth(self.pair, limit=1)

            return asks[0][0]

    def top_buy_price(self) -> Decimal:
        """ Top buy price - top price from buy queue """
        with WexConnection() as conn:
            _, bids = PublicApi(conn).get_depth(self.pair, limit=1)

            return bids[0][0]

    def get_price_unit(self) -> Decimal:
        """ Get minimum price unit for current pair  """
        return utils.td(utils.quanta[-1], self.pair_info.decimal_places, ROUND_UP)

    def create_buy_order(self, buy_price: Decimal, buy_amount: Decimal) -> models.TradeResult:
        """ Create buy order """
        with WexConnection() as conn:
            t = TradeApi(self.key, self.key_handler, conn)

            return t.trade(self.pair, 'buy', buy_price, buy_amount)

    def create_sell_order(self, sell_price: Decimal, sell_amount: Decimal) -> models.TradeResult:
        """ Create buy order """
        with WexConnection() as conn:
            t = TradeApi(self.key, self.key_handler, conn)

            return t.trade(self.pair, 'sell', sell_price, sell_amount)

    def cancel_order(self, order_id: int) -> models.CancelOrderResult:
        """ Cancel order """
        with WexConnection() as conn:
            t = TradeApi(self.key, self.key_handler, conn)

            return t.cancel_order(order_id)

    def save_order(
            self,
            order: models.Order,
            parent_order: bot_models.OrderInfo = None,
    ) -> bot_models.OrderInfo:
        """ Save executed order to database """
        self.logger.debug("Save order #{} to database".format(order.order_id))
        # if we here - order executed and we can save it to the DB
        order_info = bot_models.OrderInfo()
        order_info.pair = order.pair
        order_info.order_type = order.type
        order_info.amount = order.amount
        order_info.rate = order.rate
        order_info.created = datetime.datetime.now()
        order_info.created_timestamp = datetime.datetime.now()

        if parent_order:
            order_info.parent_order = parent_order

        order_info.save()

        return order_info

    def low_high_daily_prices(self) -> Tuple[Decimal, Decimal]:
        """
        Get low and high daily prices

        :return: tuple low, high
        """
        ticker = PublicApi(WexConnection()).get_ticker(self.pair)

        return ticker.low, ticker.high
