import logging

from bf_duster.repo import BitfinexRepo
from bf_duster.rest_client import RestClient
from bf_duster.settings import Settings
from bf_duster.steps import process_all

logging.basicConfig(level=logging.WARNING)
logging.getLogger('bf_duster').setLevel(logging.INFO)


def main():
    s = Settings()
    c = RestClient('https://api.bitfinex.com/', s.api_key, s.api_secret)
    r = BitfinexRepo(c)
    process_all(r)


if __name__ == '__main__':
    main()
