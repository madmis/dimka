import textwrap
import dimka

if __name__ == '__main__':
    app = dimka.core.app.Application('three')
    app.add_argument(
        '--step',
        default=3,
        type=int,
        help='Percent. Sell order price increase step.'
    )
    app.add_argument(
        '--iters',
        default=5,
        type=int,
        help=textwrap.dedent('''\
            Iterations quantity to waiting order execution. After all iterations order will be canceled.
                This is bot working flow with BUY orders.
                Bot waiting while order will be executed to place SELL order right after that.
                If BUY order is not executed after all iteration, we can suppose that this order is not on top now.
                So it can be canceled and new order can be placed. 
        '''),
    )
    app.add_argument(
        '--iters-time',
        default=5,
        type=int,
        help='Time in seconds to hold iteration before start new one.',
    )
    app.add_argument(
        '--high-diff',
        default=50,
        type=int,
        help=textwrap.dedent('''\
            Percent. Difference from highest price when BUY allowed.
            Example:
                - high: 10, low: 9, high-diff: 50 (pct) - buy allowed if price less then 9.5
                - high: 10, low: 9, high-diff: 10 (pct) - buy allowed if price less then 9.9
                - high: 10, low: 9, high-diff: 0 (pct) - buy allowed if price less then 10
        '''),
    )
    app.init()
    app.run()
