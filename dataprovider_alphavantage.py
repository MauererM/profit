"""Implements functions that provide data from alpha vantage

It is possible that at some point, alpha vantage does not exist anymore, or the API changes...
Then, this file has to be adapted for the new source of exchange rates and stock prices.
A potential option is pandas-datareader...

Note that the API key for alpha vantage is provided in "setup.py".

The interface to/from these functions is string-based. The functions return a list of strings for the dates,
to which the returned prices/rates correspond.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import stringoperations
import dateoperations
import setup
from alpha_vantage.timeseries import TimeSeries
import pandas
import requests
import time


def get_forex_data(sym_a, sym_b, startdate, stopdate, dateformat):
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
    startdate_dt = stringoperations.str2datetime(startdate, dateformat)
    stopdate_dt = stringoperations.str2datetime(stopdate, dateformat)
    today = dateoperations.get_date_today(dateformat, datetime_obj=True)
    if startdate_dt > stopdate_dt:
        raise RuntimeError("Startdate has to be before stopdate")
    if stopdate_dt > today:
        raise RuntimeError("Cannot (unfortunately) obtain forex-data from the future.")

    # Wait for the API to cool down (frequent requests are not allowed)
    print(f"Waiting {setup.API_COOLDOWN_TIME_SECOND:.1f}s for API cooldown")
    time.sleep(setup.API_COOLDOWN_TIME_SECOND)

    # The github-provided API from Alpha Vantage cannot be used, as it does not provide historic forex data.
    # Hence, we request data from the API directly:
    payload = {'function': 'FX_DAILY', 'from_symbol': sym_a, 'to_symbol': sym_b, 'outputsize': 'full',
               'datatype': 'json', 'apikey': setup.API_KEY_ALPHA_VANTAGE}
    r = requests.get('https://www.alphavantage.co/query', params=payload)
    data = r.json()
    # Extract the desired data:
    keys = list(data.keys())
    data = data[keys[1]]
    dates = list(data.keys())
    valstrings = list(data.values())
    forexrates = [float(x['4. close']) for x in valstrings]

    # Convert to strings and python-internal structures:
    forexdates = [pandas.to_datetime(str(x)) for x in dates]
    forexdates = [x.strftime(dateformat) for x in forexdates]  # List of strings

    # Sanity check:
    if len(forexdates) != len(forexrates):
        raise RuntimeError("Returned forex data is of unequal length. Symbol a: " + sym_a + ". Symbol b: " + sym_b)

    # The lists from alpha vantage have to be reverted such that the dates are in the correct order:
    forexdates.reverse()
    forexrates.reverse()

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

    # Crop the data to the desired range. It may still contain non-consecutive days.
    # The crop-function will not throw errors if the start/stop-dates are outside the date-list from the data provider.
    forexdates, forexrates = dateoperations.crop_datelist(forexdates_red, forexrates_red, startdate, stopdate,
                                                          dateformat)
    # Check if there is still data left:
    if len(forexrates) < 1:
        raise RuntimeError("Forex data is not available for desired interval. Maybe change analysis period. " +
                           "Symbol a: " + sym_a + ".Symbol b: " + sym_b)

    # Fill in missing data in the vector
    forexdates_full, forexrates_full = dateoperations.interpolate_data(forexdates, forexrates, dateformat)

    return forexdates_full, forexrates_full


def get_stock_data(sym_stock, sym_exchange, startdate, stopdate, dateformat):
    """Provides stock-prices (values at closing-time of given days).
    Note: The returned data might not be of sufficient length into the past (e.g., might not reach back to startdate!)
    This is done on purpose, the caller has to deal with this, he can then take appropriate action. This keeps this
    function as simple as possible.
    But: missing data in the returned interval is interpolated, so the returned dates and rates are consecutive and
    corresponding.
    NOTE: sym_exchange is not actually needed by alphavantage.
    :param sym_stock: String encoding the name of the stock, e.g., "TSLA"
    :param sym_exchange: String encoding the name of the exchange, e.g., "SWX"
    :param startdate: String encoding the day for the first price
    :param stopdate: String encoding the day of the last price
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Tuple of two lists: the first is a list of strings of consecutive dates, and the second is a list of the
    corresponding strock prices. Some data might be interpolated/extrapolated, as the API does not
    always return data for consecutive days (public holidays, weekends etc.)
    """
    # Use datetime, and sanity check:
    startdate_dt = stringoperations.str2datetime(startdate, dateformat)
    stopdate_dt = stringoperations.str2datetime(stopdate, dateformat)
    today = dateoperations.get_date_today(dateformat, datetime_obj=True)
    if startdate_dt > stopdate_dt:
        raise RuntimeError("Startdate has to be before stopdate")
    if stopdate_dt > today:
        raise RuntimeError("Cannot (unfortunately) obtain stock-data from the future.")

    # Wait for the API to cool down (frequent requests are not allowed)
    print(f"Waiting {setup.API_COOLDOWN_TIME_SECOND:.1f}s for API cooldown")
    time.sleep(setup.API_COOLDOWN_TIME_SECOND)

    ts_alphavantage = TimeSeries(key=setup.API_KEY_ALPHA_VANTAGE, output_format='pandas')
    try:
        dataframe, test = ts_alphavantage.get_daily(symbol=sym_stock, outputsize='full')
    except:
        print("Full API-call did not work. Attempting compact call")
        print(f"Waiting {setup.API_COOLDOWN_TIME_SECOND:.1f}s for API cooldown")
        time.sleep(setup.API_COOLDOWN_TIME_SECOND)
        dataframe, test = ts_alphavantage.get_daily(symbol=sym_stock, outputsize='compact')

    # Check, if we get an empty response. Throw an error, if so. Higher-level code can catch it an potentially adapt
    # the symbols, in case they are outdated.
    if dataframe.empty is True:
        raise RuntimeError("Received an empty stock-price-dataframe from alpha vantage. Symbol: " + sym_stock)

    # Re-formate the data
    pricedates = dataframe.index.values  # This is a numpy datetime64 array
    stockprices = dataframe['4. close']  # This is a float64 numpy array

    # Convert to strings and python-internal structures:
    pricedates = [pandas.to_datetime(str(x)) for x in pricedates]
    pricedates = [x.strftime(dateformat) for x in pricedates]  # List of strings
    stockprices = [float(x) for x in stockprices]  # List of floats

    # Sanity check:
    if len(pricedates) != len(stockprices):
        raise RuntimeError("Returned stock data is of unequal length. Symbol: " +
                           sym_stock + ". Exchange: " + sym_exchange)

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

    # Crop the data to the desired range. It may still contain non-consecutive days.
    # The crop-function will not throw errors if the start/stop-dates are outside the date-list from the data provider.
    pricedates, stockprices = dateoperations.crop_datelist(pricedates_red, stockprices_red, startdate, stopdate,
                                                           dateformat)
    # Check if there is still data left:
    if len(stockprices) < 1:
        raise RuntimeError("Stock data is not available for desired interval. Maybe change analysis period. " +
                           sym_stock + ". Exchange: " + sym_exchange)

    # Fill in missing data in the vector
    pricedates_full, stockprices_full = dateoperations.interpolate_data(pricedates, stockprices, dateformat)

    return pricedates_full, stockprices_full


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    dateformat = "%d.%m.%Y"

    # dates, rates = get_forex_data("EUR", "CHF", "11.04.2018", "12.04.2018", dateformat)
    # print(dateoperations.check_dates_consecutive(dates, dateformat))

    # dates, rates = get_forex_data("CHF", "EUR", "05.08.2018", "05.08.2018", dateformat)
    # print(dates)
    # print(rates)

    # dates, prices = get_stock_data("TSLA", "NASDAQ", "08.11.2017", "10.11.2019", dateformat)
    dates, prices = get_stock_data("CSSMI.SW", "SWX", "01.11.2019", "10.11.2019", dateformat)

    print(len(dates))
    print(len(prices))
    print(dates)
    print(prices)
