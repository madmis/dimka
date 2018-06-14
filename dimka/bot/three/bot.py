from decimal import Decimal
import time
from typing import Union, Tuple
import wexapi

from dimka.bot.base_bot import BaseBot
from dimka.core.app import RestartBotException
import dimka.core.models as models
from dimka.core.utils import td

import wexapi.models as wex_models

MAX_ORDERS = 3


class Bot(BaseBot):
    """
    This bot trade in three steps.
    """

    def run(self):
        self.logger.success('************* "{}" bot started: {} *************'.format(
            self.params.get('bot_name'),
            self.pair,
        ))

        # Bot parameters
        base, quote = self.split_pair()
        base_funds, quote_funds = self.funds()
        self.logger.verbose("Available funds")
        self.logger.verbose("  Base: ({}): {:f}".format(base, td(base_funds, self.units())))
        self.logger.verbose("  Quote ({}): {:f}".format(quote, td(quote_funds, self.units())))

        sell_orders = self.active_orders('sell')
        self.logger.success("Active SELL orders: {}".format(len(sell_orders)))
        self.show_orders_info(sell_orders)

        self.cancel_buy_orders()

        sell_len = len(sell_orders)

        last_buy_order = None
        # Check quote funds - is it possible to open BUY order?
        if quote_funds > self.pair_info.min_amount:
            self.logger.success("Check possibility to open BUY order")
            buy_amount = quote_funds / Decimal(str(MAX_ORDERS - sell_len))

            if buy_amount > self.pair_info.min_amount:
                # Calculate allowed buy price and create buy order
                # Waiting for it execution or restart bot
                top_price = self.top_sell_price()
                self.logger.success("  Top SELL price: {:f}".format(
                    td(top_price, self.pair_info.decimal_places)
                ))
                self.logger.success("  Increase unit: {:f}".format(self.get_price_unit()))
                price = top_price + self.get_price_unit()
                self.logger.success("  BUY price: {:f}".format(price))
                amount = td(Decimal("0.001") / price, self.units())
                self.logger.success("  BUY amount: {:f}".format(amount))

                buy_allowed, message = self.is_buy_allowed(price)
                if not self.is_buy_allowed(price):
                    raise RestartBotException(message, timeout=30)

                order = self.create_buy_order(price, amount)

                buy_state, order_info = self.waiting_order_execution(
                    order.order_id,
                    'buy',
                    self.args.iters,
                    self.args.iters_time,
                )
                if buy_state:
                    last_buy_order = self.save_order(order_info)
                else:
                    self.logger.success("  Cancel order #{}".format(order_info.order_id))
                    self.cancel_order(order_info.order_id)

        # SELL
        self.logger.success("Starting SELL")
        base_funds, quote_funds = self.funds()
        self.logger.verbose("Available funds")
        self.logger.verbose("  Base: ({}): {:f}".format(base, td(base_funds, self.units())))
        self.logger.verbose("  Quote ({}): {:f}".format(quote, td(quote_funds, self.units())))
        if base_funds > self.pair_info.min_amount:
            # sell_amount = base_funds / Decimal(str(MAX_ORDERS - sell_len))
            sell_amount = base_funds
            self.logger.success("  Sell amount: {:f}".format(td(sell_amount, self.units())))

            if not last_buy_order:
                last_buy_order = self.get_last_local_buy_order()

            # Calculate orders quantity
            self.logger.success("  Calculate orders quantity")
            orders_count = 1
            order_amount = sell_amount
            for i in range(MAX_ORDERS, 0, -1):
                order_amount = sell_amount / Decimal(str(i))
                if order_amount > self.pair_info.min_amount:
                    orders_count = i
                    break

            self.logger.success("    quantity: {}, order amount: {:f}".format(
                orders_count,
                td(order_amount, self.units())
            ))

            sell_factor = Decimal(str(self.args.step / 100))
            self.logger.debug("  Calculate SELL price")
            prev_price = self.find_sell_price(last_buy_order)
            for i in range(0, orders_count, 1):
                self.logger.debug("  Order #{}".format(i + 1))
                step_amount = sell_factor * prev_price
                self.logger.debug("    Step amount: {:f}".format(td(step_amount, self.pair_info.decimal_places)))
                sell_price = prev_price + step_amount
                prev_price = sell_price
                self.logger.debug("    SELL price: {:f}".format(td(sell_price, self.pair_info.decimal_places)))

                sell_res = self.create_sell_order(sell_price, order_amount)
                if sell_res.order_id:
                    order = self.get_last_order_from_history('sell')
                else:
                    with wexapi.common.WexConnection() as conn:
                        t = wexapi.trade.TradeApi(self.key, self.key_handler, conn)
                        order = t.order_info(sell_res.order_id)

                self.save_order(order, last_buy_order)
        else:
            msg = "{} funds is not enough to open SELL order. Min. amount is: {}".format(
                td(base_funds, self.units()),
                td(self.pair_info.min_amount, self.units()),
            )
            raise RestartBotException(msg, timeout=10)

    def is_buy_allowed(self, price: Decimal) -> Tuple[bool, str]:
        """
        Check is buy allowed

        :param: order buy price
        :return: state, message
        """
        low, high = self.low_high_daily_prices()
        high_diff = Decimal(str(abs(self.args.high_diff) / 100))
        allowed_price = (high - low) * high_diff

        if price > allowed_price:
            return False, 'Buy is not allowed, because high price is close'

        return True, ''

    def show_orders_info(self, orders: list):
        """
        Show orders details

        Args:
            orders (list): orders list wexapi.models.Order

        Returns:
            None: Only output info by logger
        """
        for order in orders:
            self.logger.verbose("  Order #{}".format(order.order_id))
            self.logger.verbose("    pair:{} | type:{} | amount:{:f} | rate:{:f} | status:{}".format(
                order.pair,
                order.type,
                td(order.amount, self.units()),
                td(order.rate, self.pair_info.decimal_places),
                order.status,
            ))

    def waiting_order_execution(
            self,
            order_id: int,
            order_type: str,
            iter_count: int,
            iter_time: int
    ) -> Tuple[bool, Union[bool, wex_models.Order]]:
        """
        Waiting for order execution.

        0 - order was completely satisfied with the counter orders

        :param order_id:
        :param order_type: buy OR sell
        :param iter_count: iterations count to check is order executed.
        :param iter_time: time in seconds for each iteration (time to sleep after iteration).
        :return: tuple where:

                    - first value: order execution state: True - executed, False - not executed
                    - second value: wex_models.Order or False (if order_id == 0)
        """
        with wexapi.common.WexConnection() as conn:
            t = wexapi.trade.TradeApi(self.key, self.key_handler, conn)

            # 0 - order was completely satisfied with the counter orders
            # this mean that we can get order id from last deal (trade history)
            if not order_id:
                order_id = self.get_last_order_from_history(order_type).order_id

            self.logger.debug("Waiting for order #{} execution ...".format(order_id))
            order_info = t.order_info(order_id)

            while order_info.status != 1 or iter_count > 0:
                time.sleep(iter_time)
                iter_count -= 1
                self.logger.debug("  Left iterations: {}".format(iter_count))

                self.show_orders_info([order_info])

                order_info = t.order_info(order_id)
            else:
                return order_info.status == 1, order_info

    def get_last_order_from_history(self, order_type: str) -> wex_models.Order:
        """
        :param order_type: buy OR sell
        """
        with wexapi.common.WexConnection() as conn:
            t = wexapi.trade.TradeApi(self.key, self.key_handler, conn)
            history = t.trade_history(pair=self.pair, count_number=100)
            for item in history:
                if item.is_your_order and item.type == order_type:
                    return t.order_info(item.order_id)

            raise Exception(
                "Wex history doesn't contains {} order for pair {}. Are you doing something wrong?".format(
                    type,
                    self.pair,
                )
            )

    def find_sell_price(self, last_buy_order: models.OrderInfo = None):
        if not last_buy_order:
            return self.top_buy_price()

        return last_buy_order.rate

    def get_last_local_buy_order(self) -> Union[None, models.OrderInfo]:
        last_hist_order = self.get_last_order_from_history('buy')

        result = None
        if last_hist_order:
            try:
                result = (models.OrderInfo
                          .select()
                          .where(models.OrderInfo.order_type == 'buy', models.OrderInfo.pair == self.pair)
                          .order_by(models.OrderInfo.created.desc())
                          .get())
            except models.DoesNotExist:
                pass

        return result
