"""Implements functions that provide data from the yahoo finance website.

The constructor obtains a cookie/crumb from yahoo finance, with which the subsequent inquiries are done. 
Make sure the constructor is only called once per session, as otherwise, many cookies are obtained, which is simply
not needed. 

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2020 Mario Mauerer
"""

import urllib.request, urllib.parse, urllib.error
import time
import stringoperations
import dateoperations
from io import StringIO
import pandas as pd


class Dataprovider:

    def __init__(self, dateformat, cooldown):
        """
        Constructor: Also obtains a cookie/crumb from yahoo finance to enable subsequent downloads. 
        :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        :param cooldown: Time in seconds between API calls
        """

        self.cookie = None
        self.crumb = None
        self.dateformat = dateformat
        self.cooldown = cooldown
        self.useragent = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/83.0'}

        self.cooker = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener(self.cooker)
        urllib.request.install_opener(self.opener)
        try:
            self.__obtain_cookie_crumb()  # Obtain a cookie and crumb for the ongoing session.
            #print("Cookie for yahoo finance obtained")
        except:
            raise RuntimeError("Initialization of yahoo/cookie somehow failed")

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

        if self.crumb == None or self.cookie == None:
            #raise RuntimeError("Could not obtain cookie or crumb from yahoo")
            print("Not sure if cookie from Yahoo finance was obtained correctly...")

    def get_forex_data(self, sym_a, sym_b, startdate, stopdate):
        """Provides foreign-exchange rates for two currencies
        :param sym_a: String encoding the first currency, e.g., "CHF"
        :param sym_b: String encoding the second currency, e.g., "EUR"
        :param startdate: String encoding the day for the first rate
        :param stopdate: String encoding the day of the last rate
        :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        :return: Tuple of two lists: the first is a list of strings of consecutive dates, and the second is a list of the
        corresponding foreign exchange rates. Some data might be interpolated/extrapolated, as the API does not
        always return data for consecutive days (public holidays probably...)
        """
        # Use datetime, and sanity check:
        startdate_dt = stringoperations.str2datetime(startdate, self.dateformat)
        stopdate_dt = stringoperations.str2datetime(stopdate, self.dateformat)
        today = dateoperations.get_date_today(self.dateformat, datetime_obj=True)
        if startdate_dt > stopdate_dt:
            raise RuntimeError("Startdate has to be before stopdate")
        if stopdate_dt > today:
            raise RuntimeError("Cannot (unfortunately) obtain forex-data from the future.")

        # Wait for the API to cool down (frequent requests are not allowed)
        print(f"Waiting {self.cooldown:.1f}s for API cooldown")
        time.sleep(self.cooldown)

        # Convert the start, stop dates to epoch:
        p1 = int(time.mktime(startdate_dt.timetuple()))
        p2 = int(time.mktime(stopdate_dt.timetuple()))

        curr_str = sym_a + sym_b
        curr_str = curr_str + "=X"

        param = dict()
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
            print("Failed to obtain data for url:" + url)
            print("Currencies: " + sym_a + " and " + sym_b)
            raise RuntimeError("Data not available.")  # This trips the outer loop and it will be dealt with otherwise

        strlines = f.read().decode('utf-8')
        if len(strlines) < 2:
            print("Error: Obtained string is very short. Probably a failure.")
            raise RuntimeError("See above...")
        strlines = StringIO(strlines)
        df = pd.read_csv(strlines, sep=",")
        # Re-formate the data
        forexdates = df['Date']
        forexrates = df['Close']  # This is a float64 numpy array

        # Convert to strings and python-internal structures:
        forexdates = [pd.to_datetime(str(x)) for x in forexdates]
        forexdates = [x.strftime(self.dateformat) for x in forexdates]  # List of strings
        forexrates = [float(x) for x in forexrates]  # List of floats

        # Sanity check:
        if len(forexdates) != len(forexrates):
            print("Returned forex data is of unequal length. Symbol a: " + sym_a + ". Symbol b: " + sym_b)
            raise RuntimeError("See above...")

        # Don't accept entries with (near-) zero value:
        forexdates_red = []
        forexrates_red = []
        for idx in range(0, len(forexdates)):
            if forexrates[idx] > 1e-6:
                forexdates_red.append(forexdates[idx])
                forexrates_red.append(forexrates[idx])

        # The returned data might not span the fully available time-range (not enough historic information available).
        # But this is OK, we also don't raise a warning, the caller is left to deal with this, since he then can take
        # action. This reduces the complexity of this module.

        # Check, if the start/stopdates are identical. Then, only the most recent value is desired. Then, it should
        # be checked if it's on a weekend or not. If yes, it falls back to the friday before.
        if startdate == stopdate:
            if stopdate_dt.weekday() == 5:
                startdate = dateoperations.add_days(startdate, -1, self.dateformat)
                stopdate = dateoperations.add_days(stopdate, -1, self.dateformat)
            elif stopdate_dt.weekday() == 6:
                startdate = dateoperations.add_days(startdate, -2, self.dateformat)
                stopdate = dateoperations.add_days(stopdate, -2, self.dateformat)

        # Crop the data to the desired range. It may still contain non-consecutive days.
        # The crop-function will not throw errors if the start/stop-dates are outside the date-list from the data provider.
        forexdates, forexrates = dateoperations.crop_datelist(forexdates_red, forexrates_red, startdate, stopdate,
                                                              self.dateformat)
        # Check if there is still data left:
        if len(forexrates) < 1:
            print("Forex data is not available for desired interval. Maybe change analysis period. " +
                  "Symbol a: " + sym_a + ".Symbol b: " + sym_b)
            raise RuntimeError("See above...")

        # Fill in missing data in the vector
        forexdates_full, forexrates_full = dateoperations.interpolate_data(forexdates, forexrates, self.dateformat)

        return forexdates_full, forexrates_full

    def get_stock_data(self, sym_stock, sym_exchange, startdate, stopdate):
        """Provides stock-prices (values at closing-time of given days).
        Note: The returned data might not be of sufficient length into the past (e.g., might not reach back to startdate!)
        This is done on purpose, the caller has to deal with this, he can then take appropriate action. This keeps this
        function as simple as possible.
        But: missing data in the returned interval is interpolated, so the returned dates and rates are consecutive and
        corresponding.
        NOTE: sym_exchange is not actually needed by yahoo finance
        :param sym_stock: String encoding the name of the stock, e.g., "TSLA"
        :param sym_exchange: String encoding the name of the exchange, e.g., "SWX". Not really needed.
        :param startdate: String encoding the day for the first price
        :param stopdate: String encoding the day of the last price
        :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        :return: Tuple of two lists: the first is a list of strings of consecutive dates, and the second is a list of the
        corresponding strock prices. Some data might be interpolated/extrapolated, as the API does not
        always return data for consecutive days (public holidays, weekends etc.)
        """
        # Use datetime, and sanity check:
        startdate_dt = stringoperations.str2datetime(startdate, self.dateformat)
        stopdate_dt = stringoperations.str2datetime(stopdate, self.dateformat)
        today = dateoperations.get_date_today(self.dateformat, datetime_obj=True)
        if startdate_dt > stopdate_dt:
            raise RuntimeError("Startdate has to be before stopdate")
        if stopdate_dt > today:
            raise RuntimeError("Cannot (unfortunately) obtain forex-data from the future.")

        # Wait for the API to cool down (frequent requests are not allowed)
        print(f"Waiting {self.cooldown:.1f}s for API cooldown")
        time.sleep(self.cooldown)

        # Convert the start, stop dates to epoch:
        p1 = int(time.mktime(startdate_dt.timetuple()))
        p2 = int(time.mktime(stopdate_dt.timetuple()))

        param = dict()
        param['period1'] = str(p1)
        param['period2'] = str(p2)
        param['interval'] = '1d'
        param['events'] = 'history'
        param['includeAdjustedClose'] = 'true'
        param['crumb'] = self.crumb
        params = urllib.parse.urlencode(param)
        url = 'http://query1.finance.yahoo.com/v7/finance/download/{}?{}'.format(sym_stock, params)
        req = urllib.request.Request(url, headers=self.useragent)
        try:
            # There is no need to enter the cookie here, as it is automatically handled by opener
            f = urllib.request.urlopen(req, timeout=6)
        except:
            print("Failed to obtain data for url:" + url)
            print("Stock symbol: " + sym_stock + ", with associated exchange: " + sym_exchange)
            raise RuntimeError("Data not available.")  # This trips the outer loop and it will be dealt with otherwise

        strlines = f.read().decode('utf-8')
        if len(strlines) < 2:
            print("Error: Obtained string is very short. Probably a failure.")
            raise RuntimeError("See above...")
        strlines = StringIO(strlines)
        df = pd.read_csv(strlines, sep=",")
        # Re-formate the data
        pricedates = df['Date']
        stockprices = df['Close']  # This is a float64 numpy array
        # Convert to strings and python-internal structures:
        pricedates = [pd.to_datetime(str(x)) for x in pricedates]
        pricedates = [x.strftime(self.dateformat) for x in pricedates]  # List of strings
        stockprices = [float(x) for x in stockprices]  # List of floats

        # Sanity check:
        if len(pricedates) != len(stockprices):
            print("Returned stock data is of unequal length. Symbol: " +
                  sym_stock + ". Exchange: " + sym_exchange)
            raise RuntimeError("See above...")

        # The returned data might not span the fully available time-range (not enough historic information available).
        # But this is OK, we also don't raise a warning, the caller is left to deal with this, since he then can take
        # action. This reduces the complexity of this module.

        # Don't accept entries with (near-) zero value:
        pricedates_red = []
        stockprices_red = []
        for idx in range(0, len(pricedates)):
            if stockprices[idx] > 1e-6:
                pricedates_red.append(pricedates[idx])
                stockprices_red.append(stockprices[idx])

        # Check, if the start/stopdates are identical. Then, only the most recent value is desired. Then, it should
        # be checked if it's on a weekend or not. If yes, it falls back to the friday before.
        if startdate == stopdate:
            if stopdate_dt.weekday() == 5:
                startdate = dateoperations.add_days(startdate, -1, self.dateformat)
                stopdate = dateoperations.add_days(stopdate, -1, self.dateformat)
            elif stopdate_dt.weekday() == 6:
                startdate = dateoperations.add_days(startdate, -2, self.dateformat)
                stopdate = dateoperations.add_days(stopdate, -2, self.dateformat)

        # Crop the data to the desired range. It may still contain non-consecutive days.
        # The crop-function will not throw errors if the start/stop-dates are outside the date-list from the data provider.
        pricedates, stockprices = dateoperations.crop_datelist(pricedates_red, stockprices_red, startdate, stopdate,
                                                               self.dateformat)
        # Check if there is still data left:
        if len(stockprices) < 1:
            # Provide information and trigger the outer try-catch loop.
            print(
                "Stock data is not available for desired interval. Maybe change analysis period, or check if there is "
                "data of today available by the provider. " +
                sym_stock + ". Exchange: " + sym_exchange)
            raise RuntimeError("See above")  # Make sure to trigger the outer try-catch loop properly

        # Fill in missing data in the vector
        pricedates_full, stockprices_full = dateoperations.interpolate_data(pricedates, stockprices, self.dateformat)

        return pricedates_full, stockprices_full


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    dateformat = "%d.%m.%Y"

    yahoo = Dataprovider(dateformat, 4.0)

    a, b = yahoo.get_forex_data("EUR", "CHF", "01.01.2019", "03.02.2019")
    print(b)
    a, b = yahoo.get_forex_data("CHF", "EUR", "01.01.2019", "03.02.2019")
    print(b)
    a, b = yahoo.get_forex_data("USD", "CHF", "01.01.2019", "03.02.2019")
    print(b)

    testlist = ["CSABI35", "VWRL.SW", "TSLA", "AAPL", "CSSMI.SW",
                "AUUSI.SW",
                "CSGN.SW",
                "CSBGC7.SW",
                "IEAC.SW",
                "UCHV50U",
                "ESREUA.SW",
                "ZGLD.SW",
                "CSCO",
                "DJI",
                "^IXIC",
                "^GDAXI",
                ".INX",
                "^SSMI"]
    for idx, dat in enumerate(testlist):
        try:
            a, b = yahoo.get_stock_data(dat, "", "01.01.2020", "05.02.2020")
            print(a)
        except:
            print("Failure: " + dat)
