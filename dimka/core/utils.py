from decimal import Decimal, ROUND_HALF_DOWN
from typing import Union

quanta = [Decimal("1e-%d" % i) for i in range(16)]


def truncate_digits(value: Union[int, float, str, Decimal], digits: int, rounding=ROUND_HALF_DOWN) -> Decimal:
    if digits > 15:
        digits = 15

    value = Decimal(str(value))

    result = value.quantize(quanta[digits], rounding=rounding)

    return Decimal(result)


def td(value: Union[int, float, str, Decimal], digits: int, rounding=ROUND_HALF_DOWN) -> Decimal:
    """
    Alias for truncate_digits
    """
    return truncate_digits(value, digits, rounding=rounding)
