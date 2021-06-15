import base64
import hashlib
import hmac
import time
import json
import argparse
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import requests

API_V1_1 = '1'
API_V2_0 = '2'
API_V3_0 = '3'
BASE_URL = 'https://api.exchange.bitcoin.com/api/{version}/{method}?{paramvalue}'


class BitcoinExchange(object):

    def __init__ (self, api_ver):
        self._api_ver = api_ver
        self._ReqUrlDict = dict ()

    def get_json (self, url, sign = None):
        raw_dict = requests.get (url).json() if sign is None else requests.get(url, headers = {'apisign': sign}).json()
        if self._api_ver == API_V2_0:
            if raw_dict:
                return True, raw_dict
            else:
                return False, raw_dict

    @staticmethod
    def get_nonce ():
        return str(int(time() * 1000))

    @staticmethod
    def hmac_sign (msg_str, secret_bytes):
        return hmac.new (secret_bytes, msg_str.encode('utf-8'), hashlib.sha512).hexdigest()


class PublicAPI(BitcoinExchange):
    def __init__ (self, api_ver):
        BitcoinExchange.__init__ (self, api_ver)
        if api_ver == API_V2_0:
            self._ReqUrlDict = {'GET_CANDLES': BASE_URL.format(version = self._api_ver, method = 'public/candles/{market}', paramvalue = 'period={period}&from={start}&till={till}&limit={limit}'),
                                }

    def get_candles(self, market, period, start='', till='', limit=''):
        """

        :param market: (String) Comma separated list of symbols. If empty, request returns candles for all symbols
        :param period: (String) Accepted values: M1 (one minute), M3, M5, M15, M30, H1 (one hour), H4, D1 (one day), D7, 1M (one month). Default value: M30 (30 minutes)
        :param start: (Datetime) Interval initial value (optional parameter)
        :param till: (Datetime) Interval end value (optional parameter)
        :param limit: (Number) Limit of candles. Default value: 100. Max value: 1000
        :return:
        """
        reqUrl = self._ReqUrlDict['GET_CANDLES'].format(market = market, period = period, start = start, till = till, limit = limit)
        return self.get_json(reqUrl)

