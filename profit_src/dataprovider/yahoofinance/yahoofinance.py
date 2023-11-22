"""Implements functions that provide data from the yahoo finance website.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2020-2023 Mario Mauerer
"""

import urllib.request
import urllib.parse
import urllib.error
import time
from io import StringIO
import pandas as pd
from ... import stringoperations
from ...dataprovider.provider_abc import DataProvider


class DataproviderYahoo(DataProvider):
    """Gets data from the yahoo finance website, their "historical data" option."""

    def __init__(self, dateformat):
        """:param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        """
        self.cookie = None
        self.crumb = None
        self.dateformat = dateformat
        self.cooldown = 1.5  # Cooldown time in seconds between subsequent API calls.
        self.useragent = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/83.0'}
        self.cooker = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener(self.cooker)
        self.name = "Yahoo Finance"

    def initialize(self):
        """Initializes this provider: Can we obtain a cookie, and can we successfully pull some data?
        """
        urllib.request.install_opener(self.opener)
        try:
            self.__obtain_cookie_crumb()  # Obtain a cookie and crumb for the ongoing session.
        except:
            return False

        # Get some stock data to see if it works.
        startdate = stringoperations.datetime2str(stringoperations.str2datetime("01.02.2020", self.dateformat),
                                                  self.dateformat)
        stopdate = stringoperations.datetime2str(stringoperations.str2datetime("01.09.2020", self.dateformat),
                                                 self.dateformat)

        return self.__check_functionality(startdate, stopdate)

    def get_name(self):
        """:return: The name of this data provider"""
        return self.name

    def retrieve_forex_data(self, sym_a, sym_b, startdate, stopdate):
        """Pulls historic forex data from the Yahoo website.
        :param sym_a, sym_b: String of the currency symbol, as used by the data provider.
        :param startdate: stopdate: Strings for the date-interval of the desired historic data.
        :return: Two lists, one a list of strings (dates) and the corresponding forex values (list of floats)
         """
        # Wait for the API/homepage to cool down (frequent requests are not allowed)
        print(f"Waiting {self.cooldown:.1f}s for API cooldown")
        time.sleep(self.cooldown)

        startdate_dt = stringoperations.str2datetime(startdate, self.dateformat)
        stopdate_dt = stringoperations.str2datetime(stopdate, self.dateformat)

        p1 = int(time.mktime(startdate_dt.timetuple()))
        p2 = int(time.mktime(stopdate_dt.timetuple()))

        curr_str = sym_a + sym_b
        curr_str = curr_str + "=X"
        param = {}
        param['period1'] = str(p1)
        param['period2'] = str(p2)
        param['interval'] = '1d'
        param['events'] = 'history'
        param['includeAdjustedClose'] = 'true'
        param['crumb'] = self.crumb
        params = urllib.parse.urlencode(param)
        url = 'http://query1.finance.yahoo.com/v7/finance/download/{}?{}'.format(curr_str, params)
        req = urllib.request.Request(url, headers=self.useragent)
        try:
            # There is no need to enter the cookie here, as it is automatically handled by opener
            f = urllib.request.urlopen(req, timeout=6)
        except:
            return None

        strlines = f.read().decode('utf-8')
        if len(strlines) < 2:
            return None

        strlines = StringIO(strlines)
        df = pd.read_csv(strlines, sep=",")
        # Re-formate the data
        forexdates = df['Date']
        forexrates = df['Close']  # This is a float64 numpy array

        # Convert to strings and python-internal structures:
        forexdates = [pd.to_datetime(str(x)) for x in forexdates]
        forexdates = [x.strftime(self.dateformat) for x in forexdates]  # List of strings following our date format
        forexrates = [float(x) for x in forexrates]  # List of floats

        return forexdates, forexrates  # Returns strings and floats

    def retrieve_stock_data(self, symbol, startdate, stopdate, symbol_exchange=None):
        """Pulls historic stock data from the Yahoo website.
        :param symbol: String of the stock symbol, as used by the data provider.
        :param startdate: String of the start-date of the interval that should be retrieved
        :param stopdate: String of the stop-date of the interval that should be retrieved
        :param symbol_exchange: String of the exchange, e.g., "SWX". Unused in Yahoo finance, as the exchange
        is encoded in the symbol (e.g., CSGN.SW)
        :return: Two lists, one a list of strings (dates) and the corresponding stock values (list of floats)
        """
        # Wait for the API/Yahoo finance to cool down (frequent requests are likely not allowed)
        print(f"Waiting {self.cooldown:.1f}s for API cooldown")
        time.sleep(self.cooldown)

        startdate_dt = stringoperations.str2datetime(startdate, self.dateformat)
        stopdate_dt = stringoperations.str2datetime(stopdate, self.dateformat)

        p1 = int(time.mktime(startdate_dt.timetuple()))
        p2 = int(time.mktime(stopdate_dt.timetuple()))

        param = {}
        param['period1'] = str(p1)
        param['period2'] = str(p2)
        param['interval'] = '1d'
        param['events'] = 'history'
        param[
            'includeAdjustedClose'] = 'true'
        param['crumb'] = self.crumb
        params = urllib.parse.urlencode(param)
        url = 'http://query1.finance.yahoo.com/v7/finance/download/{}?{}'.format(symbol, params)
        req = urllib.request.Request(url, headers=self.useragent)

        try:
            # There is no need to enter the cookie here, as it is automatically handled by opener
            f = urllib.request.urlopen(req, timeout=6)
        except:
            return None

        strlines = f.read().decode('utf-8')
        if len(strlines) < 2:
            return None

        strlines = StringIO(strlines)
        df = pd.read_csv(strlines, sep=",")
        pricedates = df['Date']
        stockprices = df['Close']  # This is a float64 numpy array. # Yahoo includes splits in the non-adjusted
        # close-column already. Otherwise, "Adj Close" could be used here, too.

        # Convert to strings and python-internal structures:
        pricedates = [pd.to_datetime(str(x)) for x in pricedates]
        pricedates = [x.strftime(self.dateformat) for x in pricedates]  # List of strings following our date format
        stockprices = [float(x) for x in stockprices]  # List of floats

        return pricedates, stockprices  # These are strings (dates) and floats that are returned

    def __obtain_cookie_crumb(self):
        self.cooker.cookiejar.clear()
        req = urllib.request.Request('http://finance.yahoo.com/quote/TSLA', headers=self.useragent)
        f = urllib.request.urlopen(req, timeout=6)
        strlines = f.read().decode('utf-8')

        # Find the crumb in the response. Code from Stackoverflow.
        cs = strlines.find('CrumbStore')
        cr = strlines.find('crumb', cs + 10)
        cl = strlines.find(':', cr + 5)
        q1 = strlines.find('"', cl + 1)
        q2 = strlines.find('"', q1 + 1)
        crumb = strlines[q1 + 1:q2]
        self.crumb = crumb

        # Find the cookie-string:
        for c in self.cooker.cookiejar:
            if c.domain != '.yahoo.com':
                continue
            if c.name != 'B':
                continue
            self.cookie = c.value

        if self.crumb is None or self.cookie is None:
            # raise RuntimeError("Could not obtain cookie or crumb from yahoo")
            # print("Not sure if cookie from Yahoo finance was obtained correctly.")
            pass

    def __check_functionality(self, startdate, stopdate):
        """ Performs a functionality-check: (try to) obtain some stock-data.
        :param startdate, stopdate: String for the start/stop data of the intended period
        :return True if success, False otherwise
        """

        SYM_STOCK = "BAC"
        SYM_1_FOREX = "CHF"
        SYM_2_FOREX = "USD"

        startdate_dt = stringoperations.str2datetime(startdate, self.dateformat)
        stopdate_dt = stringoperations.str2datetime(stopdate, self.dateformat)
        duration = stopdate_dt - startdate_dt
        duration = duration.days
        MIN_DURATION = 5
        if duration < (MIN_DURATION + 10):
            raise RuntimeError(
                "It's probably better to check the functionality of yahoo finance with a longer interval > 15d")

        try:
            d, _ = self.retrieve_stock_data(SYM_STOCK, startdate, stopdate, symbol_exchange=None)
        except:
            return False

        if len(d) < MIN_DURATION:  # Something likely went wrong/way too little data provided
            return False

        try:
            d, _ = self.retrieve_forex_data(SYM_1_FOREX, SYM_2_FOREX, startdate, stopdate)
        except:
            return False

        if len(d) < MIN_DURATION:  # Something likely went wrong/way too little data provided
            return False

        return True
