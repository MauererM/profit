"""Implements functions that provide data from google finance

It is possible that at some point, google finance does not exist anymore, or the API changes...
Then, this file has to be adapted for the new source of exchange rates and stock prices.
A potential option is pandas-datareader...

The interface to/from these functions is string-based. The functions return a list of strings for the dates,
to which the returned prices/rates correspond.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import stringoperations
import dateoperations
import googlefinance.client as googlefin
import pandas
import math


def get_forex_data(sym_a, sym_b, startdate, stopdate, dateformat):
    """Provides foreign-exchange rates for two currencies
    :param sym_a: String encoding the first currency, e.g., "CHF"
    :param sym_b: String encoding the second currency, e.g., "EUR"
    :param startdate: String encoding the day for the first rate
    :param stopdate: String encoding the day of the last rate
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Tuple of two lists: the first is a list of strings of consecutive dates, and the second is a list of the
    corresponding foreign exchange rates. Some data might be interpolated/extrapolated, as the google API does not
    always return data for consecutive days (public holidays probably...)
    """
    # Google takes values like "CHFEUR" or "USDCHF"
    symbols = sym_a + sym_b

    # Use datetime, and sanity check:
    startdate_dt = stringoperations.str2datetime(startdate, dateformat)
    stopdate_dt = stringoperations.str2datetime(stopdate, dateformat)
    today = dateoperations.get_date_today(dateformat, datetime_obj=True)
    if startdate_dt > stopdate_dt:
        raise RuntimeError("Startdate has to be before stopdate")
    if stopdate_dt > today:
        raise RuntimeError("Cannot (unfortunately) obtain forex-data from the future.")

    # The python googlefinance.client-package requires a number of days in the past, FROM TODAY:
    daydiff = today - startdate_dt
    num_past_days = int(daydiff.days)

    # Data is obtained from google in yearly blocks, as this seems to work fine.
    # If num_past_days is more than 1Y, figure out how many years at least:
    if num_past_days >= 364:
        years = math.ceil((num_past_days + 1) / 365.0)
        years_str = str(years) + "Y"
    else:
        years_str = "1Y"  # Otherwise, always read 1Y data, as this seems reliable

    # Get the data from google:
    dataframe = get_forex_rates_google(symbols, years_str)

    # Check, if we get an empty response. Throw an error, if so. Higher-level code can catch it an potentially adapt
    # the symbols, in case they are outdated.
    if dataframe.empty is True:
        raise RuntimeError("Received an empty forex-dataframe from google. Symbol a: " + sym_a + ". Symbol b: " + sym_b)

    # Re-formate the data
    forexdates = dataframe.index.values  # This is a numpy datetime64 array
    forexrates = dataframe.Close.values  # This is a float64 numpy array

    # Convert to strings and python-internal structures:
    forexdates = [pandas.to_datetime(str(x)) for x in forexdates]
    forexdates = [x.strftime(dateformat) for x in forexdates]  # List of strings
    forexdates_dt = [stringoperations.str2datetime(x, dateformat) for x in forexdates]
    forexrates = [float(x) for x in forexrates]  # List of floats

    # Sanity check:
    if len(forexdates) != len(forexrates):
        raise RuntimeError("Returned forex data is of unequal length. Symbol a: " + sym_a + ". Symbol b: " + sym_b)

    # The returned data might not span the fully available time-range (not enough historic information available).
    # But this is OK, we also don't raise a warning, the caller is left to deal with this, since he then can take
    # action. This reduces the complexity of this module.

    # It is possible that the price (closing...) of today is not yet known. Extrapolate forwards:
    # Do this before the cropping, otherwise cropping returns an empty list, if the only date is today...
    if stopdate_dt > forexdates_dt[-1]:
        forexdates, forexrates = dateoperations.extend_data_future(forexdates, forexrates, stopdate, dateformat,
                                                                   zero_padding=False)

    # Crop the data to the desired range. It may still contain non-consecutive days.
    # The crop-function will not throw errors if the start/stop-dates are outside the date-list from the data provider.
    forexdates, forexrates = dateoperations.crop_datelist(forexdates, forexrates, startdate, stopdate, dateformat)
    # Check if there is still data left:
    if len(forexrates) < 1:
        raise RuntimeError("Forex data is not available for desired interval. " +
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
    :param sym_stock: String encoding the name of the stock, e.g., "TSLA"
    :param sym_exchange: String encoding the name of the exchange, e.g., "SWX"
    :param startdate: String encoding the day for the first price
    :param stopdate: String encoding the day of the last price
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Tuple of two lists: the first is a list of strings of consecutive dates, and the second is a list of the
    corresponding strock prices. Some data might be interpolated/extrapolated, as the google API does not
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

    # The python googlefinance.client-package requires a number of days in the past, FROM TODAY:
    daydiff = today - startdate_dt
    num_past_days = int(daydiff.days)

    # Data is obtained from google in yearly blocks, as this seems to work fine.
    # If num_past_days is more than 1Y, figure out how many years at least:
    if num_past_days >= 364:
        years = math.ceil((num_past_days + 1) / 365.0)
        years_str = str(years) + "Y"
    else:
        years_str = "1Y"  # Otherwise, always read 1Y data, as this seems reliable

    # Get the data from google:
    dataframe = get_stock_prices_google(sym_stock, sym_exchange, years_str)

    # Check, if we get an empty response. Throw an error, if so. Higher-level code can catch it an potentially adapt
    # the symbols, in case they are outdated.
    if dataframe.empty is True:
        raise RuntimeError("Received an empty stock-price-dataframe from google. Symbol: " +
                           sym_stock + ". Exchange: " + sym_exchange)

    # Re-formate the data
    pricedates = dataframe.index.values  # This is a numpy datetime64 array
    stockprices = dataframe.Close.values  # This is a float64 numpy array

    # Convert to strings and python-internal structures:
    pricedates = [pandas.to_datetime(str(x)) for x in pricedates]
    pricedates = [x.strftime(dateformat) for x in pricedates]  # List of strings
    pricedates_dt = [stringoperations.str2datetime(x, dateformat) for x in pricedates]
    stockprices = [float(x) for x in stockprices]  # List of floats

    # Sanity check:
    if len(pricedates) != len(stockprices):
        raise RuntimeError("Returned stock data is of unequal length. Symbol: " +
                           sym_stock + ". Exchange: " + sym_exchange)

    # The returned data might not span the fully available time-range (not enough historic information available).
    # But this is OK, we also don't raise a warning, the caller is left to deal with this, since he then can take
    # action. This reduces the complexity of this module.

    # It is possible that the price (closing...) of today is not yet known. Extrapolate forwards:
    # Do this before the cropping, otherwise cropping returns an empty list, if the only date is today...
    if stopdate_dt > pricedates_dt[-1]:
        pricedates, stockprices = dateoperations.extend_data_future(pricedates, stockprices, stopdate, dateformat,
                                                                    zero_padding=False)

    # Crop the data to the desired range. It may still contain non-consecutive days.
    # The crop-function will not throw errors if the start/stop-dates are outside the date-list from the data provider.
    pricedates, stockprices = dateoperations.crop_datelist(pricedates, stockprices, startdate, stopdate, dateformat)
    # Check if there is still data left:
    if len(stockprices) < 1:
        raise RuntimeError("Stock data is not available for desired interval. " +
                           sym_stock + ". Exchange: " + sym_exchange)

    # Fill in missing data in the vector
    pricedates_full, stockprices_full = dateoperations.interpolate_data(pricedates, stockprices, dateformat)

    return pricedates_full, stockprices_full


def get_forex_rates_google(symbol, years):
    """Obtains forex-rates from google
    No (stock) exchange is needed for currencies.
    :param symbol: String of the currencies to be converted, e.g., "CHFEUR"
    :param years: String with the desired number of years to obtain data back into the past.
    This seems to work best. E.g., "2Y"
    :return: Panda dataframe, from googlefinance.client
    """
    # Create the dictionary for googlefinance:
    param = {
        'q': symbol,
        'i': "86400",  # Interval size in seconds ("86400" = 1 day intervals)
        'p': years  # Period (Ex: "1Y" = 1 year)
    }
    # The googlefinance.client-package returns a Pandas dataframe:
    return googlefin.get_price_data(param)


def get_stock_prices_google(symbol, exchange, years):
    """Obtains stock-prices from google
    :param symbol: String of the stock symbol
    :param exchange: String of the exchange
    :param years: String with the desired number of years to obtain data back into the past.
    This seems to work best. E.g., "2Y"
    :return: Panda dataframe, from googlefinance.client
    """
    # Create the dictionary for googlefinance:
    param = {
        'q': symbol,
        'i': "86400",  # Interval size in seconds ("86400" = 1 day intervals)
        'x': exchange,
        'p': years  # Period (Ex: "1Y" = 1 year)
    }
    # The googlefinance.client-package returns a Pandas dataframe:
    return googlefin.get_price_data(param)


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    dateformat = "%d.%m.%Y"

    # dates, rates = get_forex_data("EUR", "CHF", "11.04.2018", "12.04.2018", dateformat)
    # print(dateoperations.check_dates_consecutive(dates, dateformat))

    dates, prices = get_stock_data("IBM", "SWX", "14.04.2018", "14.04.2018", dateformat)

    print(len(dates))
    print(len(prices))
    print(dates)
    print(prices)
