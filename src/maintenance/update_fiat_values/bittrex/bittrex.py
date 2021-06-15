import base64
import hashlib
import hmac
import time
import json
import argparse
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import requests

API_V1_1 = 'v1.1'
API_V2_0 = 'v2.0'
API_V3_0 = 'v3'
BASE_URL = 'https://api.bittrex.com/{version}/{method}?{paramvalue}'


class Bittrex(object):

    def __init__ (self, api_ver):
        self._api_ver = api_ver
        self._ReqUrlDict = dict ()

    def get_json (self, url, sign = None):
        raw_dict = requests.get (url).json() if sign is None else requests.get(url, headers = {'apisign': sign}).json()
        if self._api_ver == API_V1_1:
            if raw_dict ['success'] is True:
                return True, raw_dict['result']
            else:
                return False, raw_dict['message']
        if self._api_ver == API_V3_0:
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


class PublicAPI(Bittrex):
    def __init__ (self, api_ver):
        Bittrex.__init__ (self, api_ver)
        if api_ver == API_V1_1:
            self._ReqUrlDict = {'GET_MARKETS'	: BASE_URL.format(version = self._api_ver, method = 'public/getmarkets', paramvalue = '') [:-1],
                                'GET_CURRENCIES'  : BASE_URL.format(version = self._api_ver, method = 'public/getcurrencies', paramvalue = '') [:-1],
                                'GET_TICKER'	: BASE_URL.format(version = self._api_ver, method = 'public/getticker', paramvalue = 'market={mar}'),
                                'GET_24HSUMALL'	: BASE_URL.format(version = self._api_ver, method = 'public/getmarketsummaries', paramvalue = '') [:-1],
                                'GET_24HSUM'		 : BASE_URL.format(version = self._api_ver, method = 'public/getmarketsummary', paramvalue = 'market={mar}'),
                                'GET_ORDERBOOK'  : BASE_URL.format(version = self._api_ver, method = 'public/getorderbook', paramvalue = 'market={mar}&type={typ}'),
                                'GET_HISTORY'		: BASE_URL.format(version = self._api_ver, method = 'public/getmarketsummary', paramvalue = 'market={mar}'),
                                }
        elif api_ver == API_V2_0:
            self._ReqUrlDict = {'GET_BTC_PRICE': BASE_URL.format(version = self._api_ver, method = 'pub/currencies/GetBTCPrice', paramvalue = '')[:-1],
                                'GET_TICKS': BASE_URL.format(version = self._api_ver, method = 'pub/market/GetTicks', paramvalue = 'marketName={mar}&tickInterval={itv}'),
                                'GET_LATESTTICK': BASE_URL.format(version = self._api_ver, method = 'pub/market/GetLatestTick', paramvalue = 'marketName={mar}&tickInterval={itv}'),
                                }
        elif api_ver == API_V3_0:
            self._ReqUrlDict = {'PING': BASE_URL.format(version = self._api_ver, method = 'ping', paramvalue = '')[:-1],
                                'GET_MARKETS': BASE_URL.format(version = self._api_ver, method = 'markets', paramvalue = '')[:-1],
                                'GET_MARKET': BASE_URL.format(version = self._api_ver, method = 'markets/{symbol}', paramvalue = '')[:-1],
                                'GET_MARKETS_SUMMARIES': BASE_URL.format(version = self._api_ver, method = 'markets/summaries', paramvalue = '')[:-1],
                                'GET_MARKET_SUMMARY': BASE_URL.format(version = self._api_ver, method = 'markets/{symbol}/summary', paramvalue = '')[:-1],
                                'GET_MARKET_TICKERS': BASE_URL.format(version = self._api_ver, method = 'markets/tickers', paramvalue = '')[:-1],
                                'GET_MARKET_TICKER': BASE_URL.format(version = self._api_ver, method = 'markets/{symbol}/ticker', paramvalue = '')[:-1],
                                'GET_MARKET_ORDERBOOK': BASE_URL.format(version = self._api_ver, method = 'markets/{symbol}/orderbook', paramvalue = 'depth={depth}'),
                                'GET_MARKET_TRADES': BASE_URL.format(version = self._api_ver, method = 'markets/{symbol}/trades', paramvalue = '')[:-1],
                                'GET_CURRENCIES': BASE_URL.format(version = self._api_ver, method = 'currencies{symbol}', paramvalue = '')[:-1],
                                'GET_MARKET_CANDLES': BASE_URL.format(version = self._api_ver, method = 'markets/{mar}/candles{type}{int}/historical{yr}{mth}{day}', paramvalue = '')[:-1],
                                'GET_MARKET_CANDLES_RECENT': BASE_URL.format(version = self._api_ver, method = 'markets/{mar}/candles{type}{int}/recent', paramvalue = '')[:-1],
                                'GET_RECENT': BASE_URL.format(version = self._api_ver, method = 'markets/{mar}/candles{type}{int}/recent', paramvalue = '')[:-1],
                                'GET_MARKET_HISTORY': BASE_URL.format(version = self._api_ver, method = 'markets/{mar}/candles{type}{int}/historical{yr}{mth}{day}', paramvalue = '')[:-1],
                                }

    def format_param (self, value):
        fmt = '/{}'
        return fmt.format(value)

    def ping(self):
        reqUrl = self._ReqUrlDict['PING'].format()
        return self.get_json(reqUrl)

    def get_markets(self):
        reqUrl = self._ReqUrlDict['GET_MARKETS'].format()
        return self.get_json(reqUrl)

    def get_market(self, symbol):
        reqUrl = self._ReqUrlDict['GET_MARKET'].format(symbol=symbol)
        return self.get_json(reqUrl)

    def get_market_summaries(self):
        reqUrl = self._ReqUrlDict['GET_MARKETS_SUMMARIES'].format()
        return self.get_json(reqUrl)

    def get_market_summary(self, symbol):
        reqUrl = self._ReqUrlDict['GET_MARKET_SUMMARY'].format(symbol=symbol)
        return self.get_json(reqUrl)

    def get_market_tickers(self):
        reqUrl = self._ReqUrlDict['GET_MARKET_TICKERS'].format()
        return self.get_json(reqUrl)

    def get_market_ticker(self, symbol):
        reqUrl = self._ReqUrlDict['GET_MARKET_TICKER'].format(symbol=symbol)
        return self.get_json(reqUrl)

    def get_market_orderbook(self, symbol, depth=25):
        reqUrl = self._ReqUrlDict['GET_MARKET_ORDERBOOK'].format(symbol=symbol, depth=depth)
        return self.get_json(reqUrl)

    def get_market_candles(self, market, candleType=None, candleInterval=None, year=None, month=None, day=None):
        """
        :param market:
        :param candleType: ['TRADE','MIDPOINT']
        :param candleInterval: ['MINUTE_1', 'MINUTE_5', 'HOUR_1', 'DAY_1']
        :param year:
        :param month:
        :param day:
        :return:
        """
        year_str = self.format_param(year) if year else ''
        mth_str = self.format_param(month) if month else ''
        day_str = self.format_param(day) if day else ''
        candleType_str = self.format_param(candleType) if candleType else ''
        candleInterval_str = self.format_param(candleInterval) if candleInterval else ''

        reqUrl = self._ReqUrlDict['GET_MARKET_HISTORY'].format(mar = market, type=candleType_str, int=candleInterval_str, yr=year_str, mth=mth_str, day=day_str)
        return self.get_json(reqUrl)

    def get_market_candles_recent(self, market, candleType=None, candleInterval=None):
        """
        :param market:
        :param candleType: ['TRADE','MIDPOINT']
        :param candleInterval: ['MINUTE_1', 'MINUTE_5', 'HOUR_1', 'DAY_1']
        :return:
        """
        candleType_str = self.format_param(candleType) if candleType else ''
        candleInterval_str = self.format_param(candleInterval) if candleInterval else ''

        reqUrl = self._ReqUrlDict['GET_RECENT'].format(mar = market, type=candleType_str, int=candleInterval_str)
        return self.get_json(reqUrl)

    def get_market_history(self, market, candleType=None, candleInterval=None, year=None, month=None, day=None):
        """
        :param market:
        :param candleType: ['TRADE','MIDPOINT']
        :param candleInterval: ['MINUTE_1', 'MINUTE_5', 'HOUR_1', 'DAY_1']
        :param year:
        :param month:
        :param day:
        :return:
        """
        fmtdate = '/{}'
        year_str = fmtdate.format(year) if year else ''
        mth_str = fmtdate.format(month) if month else ''
        day_str = fmtdate.format(day) if day else ''
        candleType_str = fmtdate.format(candleType) if candleType else ''
        candleInterval_str = fmtdate.format(candleInterval) if candleInterval else ''

        reqUrl = self._ReqUrlDict['GET_MARKET_HISTORY'].format(mar = market, type=candleType_str, int=candleInterval_str, yr=year_str, mth=mth_str, day=day_str)
        return self.get_json(reqUrl)

    def get_recent(self, market, candleType=None, candleInterval=None):
        """
        :param market:
        :param candleType: ['TRADE','MIDPOINT']
        :param candleInterval: ['MINUTE_1', 'MINUTE_5', 'HOUR_1', 'DAY_1']
        :return:
        """
        candleType_str = self.format_param(candleType) if candleType else ''
        candleInterval_str = self.format_param(candleInterval) if candleInterval else ''

        reqUrl = self._ReqUrlDict['GET_RECENT'].format(mar = market, type=candleType_str, int=candleInterval_str)
        return self.get_json(reqUrl)

