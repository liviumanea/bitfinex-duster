import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from requests import Response, RequestException

from bf_duster.errors import RepoException
from bf_duster.model_decoders import decode_wallet, decode_pair, decode_ticker
from bf_duster.models import Wallet, TradingPair, Ticker
from bf_duster.rest_client import RestClient

_logger = logging.getLogger(__name__)


class IRepo(ABC):
    """
    Interface for a repository that provides data from an exchange.
    """

    @abstractmethod
    def get_wallets(self) -> list[Wallet]:
        """
        Get all wallets for the current user.
        """
        raise NotImplementedError

    @abstractmethod
    def get_trading_pairs(self) -> list[TradingPair]:
        """
        Get all available trading pairs.
        """
        raise NotImplementedError

    @abstractmethod
    def get_tickers(self, symbols: list[str] = None) -> list[Ticker]:
        """
        Get ticker data for the specified symbols. If no symbols are specified, all tickers are returned.
        """
        raise NotImplementedError

    @abstractmethod
    def transfer(
            self,
            wallet_from: str,
            wallet_to: str,
            currency_from: str,
            currency_to: str,
            amount: Decimal
    ):
        """
        Transfer funds from one wallet to another.
        """
        raise NotImplementedError

    @abstractmethod
    def create_order(
            self,
            order_type: str,
            trading_symbol: str,
            amount: Decimal,
    ):
        """
        Create an order to buy or sell a certain amount of a trading symbol.
        """
        raise NotImplementedError


def _handle_response(resp: Response):
    """
    Handle a JSON HTTP response.
    """
    if resp.status_code != 200:
        raise RepoException(f"Error while requesting from Bitfinex: {resp.status_code}, {resp.text}")
    return resp.json()


class BitfinexRepo(IRepo):
    """
    Repository implementation that provides data from Bitfinex.
    """

    def __init__(self, client: RestClient):
        self._client = client

    def _request_securely(self, path: str, params: dict = None, headers: dict = None) -> Any:
        """
        Make a secure request to the specified path and return the response as a JSON object.
        """
        try:
            return _handle_response(self._client.request_securely(path, params, headers))
        except RequestException as e:
            raise RepoException("Error while requesting from Bitfinex") from e

    def _request_public_data(self, path: str, params: dict = None, headers: dict = None) -> Any:
        """
        Make a request to the specified public path and return the response as a JSON object.
        """
        try:
            return _handle_response(self._client.request_public_data(path, params, headers))
        except RequestException as e:
            raise RepoException("Error while requesting from Bitfinex") from e

    def get_wallets(self) -> list[Wallet]:
        wallets = self._request_securely("v2/auth/r/wallets")
        return [decode_wallet(w) for w in wallets]

    def get_trading_pairs(self) -> list[TradingPair]:
        pairs = self._request_public_data("v2/conf/pub:info:pair")
        pairs = pairs[0]
        return [decode_pair(p) for p in pairs]

    def get_tickers(self, symbols: list[str] = None) -> list[Ticker]:
        if symbols is None:
            symbols = "ALL"
        else:
            symbols = ",".join(symbols)
        tickers = self._request_public_data("v2/tickers", params={"symbols": symbols})
        return [decode_ticker(t) for t in tickers if t[0].startswith("t")]

    def transfer(
            self,
            wallet_from: str,
            wallet_to: str,
            currency_from: str,
            currency_to: str,
            amount: Decimal
    ):
        self._request_securely("v2/auth/w/transfer", params={
            "from": wallet_from,
            "to": wallet_to,
            "currency": currency_from,
            "currency_to": currency_to,
            "amount": str(amount)
        })

    def create_order(
            self,
            order_type: str,
            trading_symbol: str,
            amount: Decimal,
    ):
        self._request_securely("v2/auth/w/order/submit", params={
            "type": order_type,
            "symbol": trading_symbol,
            "amount": str(amount)
        })
