import hashlib
import hmac
import json
import time
from urllib.parse import urljoin

import requests


def _nonce() -> str:
    """
    Generates a nonce
    """
    return str(int(round(time.time() * 10000)))


class RestClient:
    """
    Bitfinex REST API client
    """

    def __init__(self, base_url, api_key, api_secret):
        self._base_url = base_url
        self._api_key = api_key
        self._api_secret = api_secret.encode(encoding='UTF-8')

    def _secure_headers(self, path: str, nonce: str, body: str, headers: dict = None):
        """
        Generates the headers for a secure request
        """
        signature = "/api/" + path + nonce + body
        signature_bytes = signature.encode(encoding='UTF-8')
        h = hmac.new(self._api_secret, signature_bytes, hashlib.sha384)
        return {
            **(headers or {}),
            "bfx-nonce": nonce,
            "bfx-apikey": self._api_key,
            "bfx-signature": h.hexdigest(),
        }

    def request_securely(self, path, params: dict = None, headers: dict = None):
        """
        Sends a secure request to the Bitfinex API
        """
        nonce = _nonce()
        body = params or {}
        headers = headers or {}
        headers.setdefault("content-type", "application/json")
        body_json = json.dumps(body)
        headers = self._secure_headers(path, nonce, body_json, headers)
        url = urljoin(self._base_url, path)
        return requests.post(url, headers=headers, data=body_json, verify=True)

    def request_public_data(self, path, params: dict = None, headers: dict = None):
        """
        Sends a request for public data to the Bitfinex API
        """
        params = params or {}
        headers = headers or {}
        headers.setdefault("content-type", "application/json")
        url = urljoin(self._base_url, path)
        return requests.get(url, params=params, headers=headers)
