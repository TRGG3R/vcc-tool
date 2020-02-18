import os
import hmac
import hashlib
import requests
import random
import sys
from datetime import datetime, timezone


class Error(Exception):
    """Base class for other exceptions"""
    pass


class Pairing(Error):
    """Raised when the coin -currency pairing does not exist"""
    sys.exit(f"No pairing exists for the coin-currency input")


def transact():
    """Sends an API request to the VCC exchange"""
    # Sets a quantity range to sell. Example: (10,15) randomly selects a number between 10 and 15
    quantity = round(random.uniform(10, 15), 2)

    # Coin to trade (FCT, ADA, BTC etc...)
    coin = 'fct'

    # Base currency coin is denominated in (BTC, USDT, etc...)
    currency = "usdt"

    # API key and secret key. Must set through env variable
    # Can change to your own reference via config file or other means
    api_key = os.environ["VCC_API"]
    secret = bytes(os.environ["VCC_SECRET"], "utf-8")

    # Validates the pairing input above and requests the last price of coin_currency pairing
    pairing = f"{coin.upper()}_{currency.upper()}"
    ticker = requests.get('https://vcc.exchange/api/v2/ticker')
    try:
        price = ticker.json()['data'][pairing]['last_price']
    except Pairing as e:
        raise e

    # Change the figure here to adjust the price addition/reduction factor
    # (.0000001, for example reduces current currency price by .0000001)
    tx_price = round((float(price) - .0000001), 7)

    # API endpoints for use. If anything other than  sell_order or buy_order, must change method to GET
    endpoints = {
        "user": "api/v2/user",
        "ticker": "api/v2/ticker",
        "orders": "api/v2/orders/",
        "trades": "api/v2/orders/trades",
        "sell_order": f"api/v2/orders?trade_type=sell&type=limit&quantity={quantity}&price={tx_price}"
                      f"&currency={currency.lower()}&coin={coin.lower()}",
        "buy_order": f"api/v2/orders?trade_type=buy&type=limit&quantity={quantity}&price={tx_price}"
                     f"&currency={currency.lower()}&coin={coin.lower()}"
    }

    # Base URL for API
    base_url = "https://vcc.exchange/"

    # Change this figure to determine type of API request
    endpoint = endpoints["sell_order"]

    # Creates the message payload
    if endpoints["sell_order"] or endpoints["buy_order"]:
        message = bytes(f"POST {endpoint}", "utf-8")
    else:
        message = bytes(f"GET {endpoint}", "utf-8")

    signature = hmac.new(secret, message, digestmod=hashlib.sha256).hexdigest().encode()

    # Millisecond UTC timestamp
    timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))

    # Headers for including in API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "timestamp": timestamp,
        "signature": signature
    }

    if endpoints["sell_order"] or endpoints["buy_order"]:
        response = requests.post(f"{base_url}{endpoint}", headers=headers)
        print(f'Placing a limit order to sell {quantity} {coin.upper()} at {tx_price}{currency.upper()}'
              f' price. Standby for response...')
    else:
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
    print(response.json())
