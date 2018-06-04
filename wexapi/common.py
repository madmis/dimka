import decimal
import json
import os
import re
import http.client as httplib


class InvalidTradePairException(Exception):
    """ Raised when an invalid pair is passed. """
    pass


class InvalidTradeTypeException(Exception):
    """ Raised when invalid trade type is passed. """
    pass


class InvalidTradeAmountException(Exception):
    """ Raised if trade amount is too much or too little. """
    pass


class APIResponseError(Exception):
    """ Raised if the API replies with an HTTP code not in the 2xx range. """
    pass


decimal.getcontext().rounding = decimal.ROUND_DOWN
quanta = [decimal.Decimal("1e-%d" % i) for i in range(16)]

wex_domain = "wex.nz"


def parse_json_response(response):
    def parse_decimal(var):
        return decimal.Decimal(var)

    try:
        if type(response) is not str:
            response = response.decode('utf-8')
        r = json.loads(response, parse_float=parse_decimal, parse_int=parse_decimal)
    except Exception as e:
        msg = "Error while attempting to parse JSON response: %s\nResponse:\n%r" % (e, response)
        raise Exception(msg)

    return r


HEADER_COOKIE_RE = re.compile(r'__cfduid=([a-f0-9]{46})')
BODY_COOKIE_RE = re.compile(r'document\.cookie="a=([a-f0-9]{32});path=/;";')


class WexConnection(object):
    def __init__(self, timeout=30):
        self.conn = None
        self.cookie = None
        self._timeout = timeout
        self.setup_connection()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def setup_connection(self):
        if "HTTPS_PROXY" in os.environ:
            match = re.search(r'http://([\w.]+):(\d+)', os.environ['HTTPS_PROXY'])
            if match:
                self.conn = httplib.HTTPSConnection(
                    match.group(1),
                    port=match.group(2),
                    timeout=self._timeout,
                )
            self.conn.set_tunnel(wex_domain)
        else:
            self.conn = httplib.HTTPSConnection(wex_domain, timeout=self._timeout)
        self.cookie = None

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def get_cookie(self):
        if self.conn is None:
            raise Exception("Attempted to use a closed connection.")

        self.cookie = ""

        try:
            self.conn.request("GET", '/')
            response = self.conn.getresponse()
        except Exception:
            # reset connection so it doesn't stay in a weird state if we catch
            # the error in some other place
            self.conn.close()
            self.setup_connection()
            raise

        set_cookie_header = response.getheader("Set-Cookie")
        match = HEADER_COOKIE_RE.search(set_cookie_header)
        if match:
            self.cookie = "__cfduid=" + match.group(1)

        cookie_body = response.read()
        if type(cookie_body) is not str:
            cookie_body = cookie_body.decode('utf-8')

        match = BODY_COOKIE_RE.search(cookie_body)
        if match:
            if self.cookie != "":
                self.cookie += '; '
            self.cookie += "a=" + match.group(1)

    def make_request(self, url, extra_headers=None, params="", with_cookie=False):
        if self.conn is None:
            raise Exception("Attempted to use a closed connection.")

        headers = {"Content-type": "application/x-www-form-urlencoded"}
        if extra_headers is not None:
            headers.update(extra_headers)

        if with_cookie:
            if self.cookie is None:
                self.get_cookie()

            headers.update({"Cookie": self.cookie})

        try:
            self.conn.request("POST", url, params, headers)
            response = self.conn.getresponse()
        except Exception:
            # reset connection so it doesn't stay in a weird state if we catch
            # the error in some other place
            self.conn.close()
            self.setup_connection()
            raise

        if response.status != 200:
            raise httplib.HTTPException
        else:
            return response.read()

    def make_json_request(self, url, extra_headers=None, params=""):
        response = self.make_request(url, extra_headers, params)
        return parse_json_response(response)


def truncate_amount_digits(value, digits: int) -> decimal.Decimal:
    """
    :param value: int|float|str|decimal.Decimal
    :param digits:
    :return: Decimal
    """
    if type(value) is int:
        value = str(value)

    if type(value) is float:
        value = str(value)

    if type(value) is str:
        value = decimal.Decimal(value)

    quantum = quanta[int(digits)]

    return value.quantize(quantum)


def format_currency_digits(value, digits: int) -> str:
    """
    :param value: int|float|str|decimal.Decimal
    :param digits:
    :return: str
WexConnection    """
    return str(truncate_amount_digits(value, digits))
