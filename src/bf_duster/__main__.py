import logging

from bf_duster.repo import BitfinexRepo
from bf_duster.rest_client import RestClient
from bf_duster.settings import Settings
from bf_duster.steps import process_all
from argparse import ArgumentParser
from decimal import Decimal

logging.basicConfig(level=logging.WARNING)


def main():

    parser = ArgumentParser()
    parser.add_argument(
        '--max-value-usd',
        type=Decimal, default=Decimal('10'),
        help='Do not convert a wallet into BTC if value in USD is greater than this value.'
    )
    args = parser.parse_args()

    s = Settings()
    c = RestClient('https://api.bitfinex.com/', s.api_key, s.api_secret)
    r = BitfinexRepo(c)
    process_all(r, args.max_value_usd)


if __name__ == '__main__':
    main()
