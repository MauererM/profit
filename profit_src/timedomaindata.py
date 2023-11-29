"""Implements classes that stores and manages time-domain data (e.g., from a data provider or storage-system)

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import logging
from . import dateoperations
from . import helper
from .storage.stock.stock import StockData
from .storage.forex.forex import ForexData
from .storage.index.index import IndexData


class StockMarketIndicesData:
    """Manages time-domain data for stock market indices from the data provider and/or storage-system."""

    def __init__(self, symbol, name, storage, startdate_str, stopdate_str, provider, analyzer):
        """Obtains the required data for stock market indices from the dataprovider or storage.
        :param symbol: Symbol of the index
        :param storage: Object of the storage-handler
        :param startdate_str: String that encodes the start-date of the forex-data
        :param stopdate_str: String that encodes the stop-date of the forex-data
        :param provider: Object of the data provider class, e.g., dataprovider_yahoofinance
        :param analyzer: The analyzer-object (used for caching)
        """
        self.symbol = symbol
        self.storage = storage
        self.analysis_startdate = startdate_str
        self.analysis_stopdate = stopdate_str
        self.analyzer = analyzer
        self.dateformat = self.analyzer.get_dateformat()
        self.provider = provider
        self.analysis_startdate_dt = self.analyzer.str2datetime(self.analysis_startdate)
        self.analysis_stopdate_dt = self.analyzer.str2datetime(self.analysis_stopdate)
        self.full_dates = None
        self.full_values = None
        self.price_avail = False
        self.name = name

        if self.analysis_startdate_dt > self.analysis_stopdate_dt:
            raise RuntimeError(f"Startdate cannot be after stopdate. Stock market symbol: {self.symbol}")

        # Gather and process the data:
        self.storageobj = self.__get_index_storage_object()
        if self.storageobj is None:
            self.__create_new_index_storage_file()  # Create a new file, if it does not yet exist.
        startdate_dataprovider, stopdate_dataprovider, startdate_from_storage, stopdate_from_storage = get_provider_storage_ranges(
            self.storageobj, self.storage, self.analyzer, self.analysis_startdate, self.analysis_stopdate)
        storagedates, storageprices, providerdates, providerprices = obtain_data_from_storage_and_provider(
            startdate_dataprovider, stopdate_dataprovider,
            startdate_from_storage, stopdate_from_storage, self.storage, self.storageobj, self.provider)
        self.full_dates, self.full_values, self.write_to_file = post_process_provider_storage_data(storagedates,
                                                                                                   storageprices,
                                                                                                   providerdates,
                                                                                                   providerprices,
                                                                                                   self.storage,
                                                                                                   self.storageobj,
                                                                                                   self.analyzer)
        if isinstance(self.full_dates, list) and len(self.full_dates) > 0:
            # The index-data must be fully extrapolated:
            self.full_dates, self.full_values = dateoperations.format_datelist(self.full_dates, self.full_values,
                                                                               self.analysis_startdate,
                                                                               self.analysis_stopdate, self.analyzer,
                                                                               zero_padding_past=False,
                                                                               zero_padding_future=False)

            self.price_avail = True
        else:
            self.price_avail = False  # Something failed, e.g., no provider-data, no market-data available.

    def __get_index_storage_object(self):
        return self.storage.is_storage_data_existing("index", (self.symbol))

    def __create_new_index_storage_file(self):
        self.storageobj = self.storage.create_new_storage_file("index", (self.symbol))

    def get_values(self):
        return self.full_values

    def is_price_avail(self):
        return self.price_avail

    def get_name(self):
        return self.name


class ForexTimeDomainData:
    """Obtains online forex data (through the dataprovider) and/or obtains the required prices from the
    storage-folder
    """

    def __init__(self, currency_str, basecurrency_str, storage, startdate_str, stopdate_str, provider, analyzer):
        """ForexRates constructor: Obtains the required data from the dataprovider or storage.
        The exchange rates are obtained such that the currency can be multiplied with the rates to get the value in the
        base currency.
        :param currency_str: String that encodes the currency, e.g., "EUR"
        :param basecurrency_str: String that encodes the basecurrency, e.g., "CHF"
        :param storage: Object of the storage-handler
        :param startdate_str: String that encodes the start-date of the forex-data
        :param stopdate_str: String that encodes the stop-date of the forex-data
        :param provider: Object of the data provider class, e.g., dataprovider_yahoofinance
        :param analyzer: The analyzer-object (used for caching)
        """
        self.currency = currency_str
        self.basecurrency = basecurrency_str
        self.storage = storage
        self.analysis_startdate = startdate_str
        self.analysis_stopdate = stopdate_str
        self.analyzer = analyzer
        self.dateformat = self.analyzer.get_dateformat()
        self.provider = provider
        self.analysis_startdate_dt = self.analyzer.str2datetime(self.analysis_startdate)
        self.analysis_stopdate_dt = self.analyzer.str2datetime(self.analysis_stopdate)
        self.full_dates = None
        self.full_prices = None

        if self.analysis_startdate_dt > self.analysis_stopdate_dt:
            raise RuntimeError(f"Startdate cannot be after stopdate. "
                               f"Currency: {self.currency}, basecurrency: {self.basecurrency}")

        # Gather and process the data:
        self.storageobj = self.__get_forex_storage_object()
        if self.storageobj is None:
            self.__create_new_forex_storage_file()  # Create a new file, if it does not yet exist.
        startdate_dataprovider, stopdate_dataprovider, startdate_from_storage, stopdate_from_storage = \
            get_provider_storage_ranges(self.storageobj, self.storage, self.analyzer, self.analysis_startdate,
                                        self.analysis_stopdate)
        storagedates, storageprices, providerdates, providerprices = obtain_data_from_storage_and_provider(
            startdate_dataprovider, stopdate_dataprovider,
            startdate_from_storage, stopdate_from_storage, self.storage, self.storageobj, self.provider)
        self.full_dates, self.full_prices, self.write_to_file = \
            post_process_provider_storage_data(storagedates, storageprices, providerdates, providerprices, self.storage,
                                               self.storageobj, self.analyzer)

        # No forex data available:
        if self.full_dates is None or len(self.full_dates) < 2:
            # We cannot continue, forex-data is a must, as otherwise the asset values are not known.
            raise RuntimeError(f"No forex data available for {self.currency} and {self.basecurrency}. "
                               f"Provide the data in a marketdata-file.")

        # Write the fused provider- and storge-data back to file:
        if self.write_to_file is True:
            self.storage.write_data_to_storage(self.storageobj, (self.full_dates, self.full_prices))

        # The returned forex data might not be available until today (e.g., if this is run on a weekend).
        # Extend the data accordingly into the future. Note: In Forex, this is OK to do (in investments,
        # it is NOT OK to do this, as there, the manually entered transactions-data may not be overwritten. But in
        # Forex, there is no manually entered transactions-data that could take precedent.
        lastdate_dt = self.analyzer.str2datetime(self.full_dates[-1])
        if self.analysis_stopdate_dt > lastdate_dt:
            self.full_dates, self.full_prices = dateoperations.extend_data_future(self.full_dates, self.full_prices,
                                                                                  self.analysis_stopdate,
                                                                                  self.analyzer,
                                                                                  zero_padding=False)

        # Interpolate the data to get a consecutive list:
        self.full_dates, self.full_prices = dateoperations.interpolate_data(self.full_dates, self.full_prices,
                                                                            self.analyzer)

        # The available market-data (from the dataprovider and the database) might not reach back to the
        # desired startdate! Check it:
        dates_full_start = self.analyzer.str2datetime(self.full_dates[0])
        dates_full_stop = self.analyzer.str2datetime(self.full_dates[-1])
        if dates_full_start > self.analysis_startdate_dt:
            print(f"Available rates (data provider and stored market-data) are only available from "
                  f"the {self.full_dates[0]} onwards. Earliest available data will be extrapolated backwards.")
        if dates_full_stop < self.analysis_stopdate_dt:
            print(f"Available rates (data provider and stored market-data) are only available until "
                  f"the {self.full_dates[-1]}. Latest available data will be extrapolated forwards.")

        # Crop the data to the desired period:
        self.full_dates, self.full_prices = dateoperations.format_datelist(self.full_dates, self.full_prices,
                                                                           self.analysis_startdate,
                                                                           self.analysis_stopdate,
                                                                           self.analyzer,
                                                                           zero_padding_past=False,
                                                                           zero_padding_future=False)

        self.rate_dates_dict = helper.create_dict_from_list(self.full_dates)

    def __get_forex_storage_object(self):
        return self.storage.is_storage_data_existing("forex", (self.currency, self.basecurrency))

    def __create_new_forex_storage_file(self):
        self.storageobj = self.storage.create_new_storage_file("forex", (self.currency, self.basecurrency))

    def get_price_data(self):
        if self.full_dates is not None:
            return self.full_dates, self.full_prices
        raise RuntimeError(f"No forex rates available. Currency: {self.currency}. Basecurrency: {self.basecurrency}")

    def perform_conversion(self, datelist, vallist):
        """Perform a forex-conversion.
        :param datelist: List of strings of dates
        :param vallist: Corresponding list of values
        :return: List of converted values, corresponding to the datelist
        """
        if self.full_dates is None:
            raise RuntimeError("Cannot perform currency conversion. Forex-data not available. "
                               "Should have been obtained in the constructor, though...")

        # Sanity-check:
        if len(datelist) != len(vallist):
            raise RuntimeError("The specified date- and value-lists must match in length.")

        # Convert the values:
        matches = [self.rate_dates_dict[key] for key in datelist if key in self.rate_dates_dict]
        if len(matches) != len(set(matches)) or len(matches) != len(vallist):  # This should really not happen here
            raise RuntimeError("The forex-dates are not consecutive, have duplicates, or miss data.")
        conv_val = [vallist[i] * self.full_prices[idx] for i, idx in enumerate(matches)]

        return conv_val

    def get_currency(self):
        """Return the currency (as string)"""
        return self.currency

    def get_basecurrency(self):
        """Return the basecurrency (as string)"""
        return self.basecurrency


class StockTimeDomainData:
    """Manages time-domain data for stocks from the data provider and/or storage-system."""

    def __init__(self, symbol, exchange, currency, analysis_interval, analyzer, storage, provider):
        self.symbol = symbol
        self.exchange = exchange
        self.currency = currency
        self.analysis_startdate, self.analysis_stopdate = analysis_interval
        self.analyzer = analyzer
        self.storage = storage
        self.provider = provider
        self.full_dates = None
        self.full_prices = None

        # Gather and process the data:
        self.storageobj = self.__get_stock_storage_object()
        if self.storageobj is None:
            self.__create_new_stock_storage_file()  # Create a new file, if it does not yet exist.
        startdate_dataprovider, stopdate_dataprovider, startdate_from_storage, stopdate_from_storage = \
            get_provider_storage_ranges(self.storageobj, self.storage, self.analyzer, self.analysis_startdate,
                                        self.analysis_stopdate)
        storagedates, storageprices, providerdates, providerprices = obtain_data_from_storage_and_provider(
            startdate_dataprovider, stopdate_dataprovider,
            startdate_from_storage, stopdate_from_storage, self.storage, self.storageobj, self.provider)
        self.full_dates, self.full_prices, self.write_to_file = \
            post_process_provider_storage_data(storagedates, storageprices, providerdates, providerprices, self.storage,
                                               self.storageobj, self.analyzer)

        # Write the fused provider- and storge-data back to file:
        if self.write_to_file is True:
            self.storage.write_data_to_storage(self.storageobj, (self.full_dates, self.full_prices))

        if self.full_dates is not None:
            # If only 3 days are missing until "today", then extrapolate forward
            # (avoid having to manually enter data in transactions when not really needed)
            lastdate_dt = self.analyzer.str2datetime(self.full_dates[-1])
            stopdate_analysis_dt = self.analyzer.str2datetime(self.analysis_stopdate)
            startdate_analysis_dt = self.analyzer.str2datetime(self.analysis_startdate)
            duration = stopdate_analysis_dt - lastdate_dt
            if duration.days <= 3:
                self.full_dates, self.full_prices = dateoperations.extend_data_future(self.full_dates, self.full_prices,
                                                                                      self.analysis_stopdate,
                                                                                      self.analyzer,
                                                                                      zero_padding=False)

            # Interpolate the data to get a consecutive list (this only fills holes, and does not
            # extrapolate over the given date-range):
            self.full_dates, self.full_prices = dateoperations.interpolate_data(self.full_dates, self.full_prices,
                                                                                self.analyzer)

            # The available market-data (from the dataprovider and the database) might not reach back to the
            # desired analysis range startdate! Check it:
            full_dates_start = self.analyzer.str2datetime(self.full_dates[0])
            full_dates_stop = self.analyzer.str2datetime(self.full_dates[-1])
            if full_dates_start > startdate_analysis_dt:
                print(f"Available prices (provider and stored data) are only available from the {self.full_dates[0]} "
                      f"onwards. Earliest available data will be extrapolated backwards and merged with the "
                      f"manually entered prices. \nSymbol: {self.symbol}, exchange: {self.exchange}")
            if full_dates_stop < stopdate_analysis_dt:
                print(f"Available prices (data provider and stored market-data) are only available until "
                      f"the {self.full_dates[-1]}. Latest available data will be extrapolated forwards and merged with "
                      f"the manually entered prices.\nSymbol: {self.symbol}, exchange: {self.exchange}."
                      f"\nUpdate the storage data file or transactions-list for correct returns calculation")

    def __create_new_stock_storage_file(self):
        self.storageobj = self.storage.create_new_storage_file("stock", (self.symbol, self.exchange, self.currency))

    def __get_stock_storage_object(self):
        return self.storage.is_storage_data_existing("stock", (self.symbol, self.exchange, self.currency))

    def get_price_data(self):
        return self.full_dates, self.full_prices

    def storage_to_update(self):
        return self.write_to_file

    def get_storageobj(self):
        return self.storageobj


def get_provider_storage_ranges(storageobj, storage, analyzer, analysis_startdate, analysis_stopdate):
    startdate_analysis_dt = analyzer.str2datetime(analysis_startdate)
    stopdate_analysis_dt = analyzer.str2datetime(analysis_stopdate)
    if storageobj is not None:
        startdate_storage, stopdate_storage = storage.get_start_stopdate(storageobj)
    # We only have valid data if the storage object exists, and if it actually already contains data:
    if (storageobj is not None) and (startdate_storage is not None) and (stopdate_storage is not None):
        startdate_storage_dt = analyzer.str2datetime(startdate_storage)
        stopdate_storage_dt = analyzer.str2datetime(stopdate_storage)

        # The storage-interval can not, partially, or over-overlap the analysis interval (and vice versa).
        # Depending on this, different data should be obtained by the data provider.

        # The storage object contains holes in its data ==> Pull the full range from the provider, as otherwise,
        # all assumptions/cases below will not work. For the time being, this system needs contiguous data in the
        # storage, as we only pull one set of data from the provider.
        # Todo: This could be made more granular (if pulling less data from the provider is a need)
        if len(storageobj.get_holes()) != 0:
            startdate_dataprovider = analyzer.datetime2str(startdate_analysis_dt)
            stopdate_dataprovider = analyzer.datetime2str(stopdate_analysis_dt)
            startdate_from_storage = None
            stopdate_from_storage = None
            print(f"Holes in the data of the storage object for {storageobj.get_filename()} detected. "
                  f"Will pull all data from provider.")
        # The analysis-interval is fully contained in the market-data: No online retrieval necessary.
        elif startdate_storage_dt <= startdate_analysis_dt and stopdate_analysis_dt <= stopdate_storage_dt:
            startdate_dataprovider = None
            stopdate_dataprovider = None
            startdate_from_storage = analyzer.datetime2str(startdate_analysis_dt)
            stopdate_from_storage = analyzer.datetime2str(stopdate_analysis_dt)
        # The analysis-interval is larger on both ends than the stored data:
        elif startdate_analysis_dt < startdate_storage_dt and stopdate_analysis_dt > stopdate_storage_dt:
            startdate_dataprovider = analyzer.datetime2str(startdate_analysis_dt)  # Pull the full data
            stopdate_dataprovider = analyzer.datetime2str(stopdate_analysis_dt)
            startdate_from_storage = analyzer.datetime2str(startdate_storage_dt)
            stopdate_from_storage = analyzer.datetime2str(stopdate_storage_dt)
        # The analysis interval is fully before the storage interval:
        elif startdate_analysis_dt < startdate_storage_dt and stopdate_analysis_dt < startdate_storage_dt:
            startdate_dataprovider = analyzer.datetime2str(startdate_analysis_dt)
            # We pull the full data up until the storage interval, to fill missing data in storage
            stopdate_dataprovider = analyzer.datetime2str(startdate_storage_dt)
            startdate_from_storage = None
            stopdate_from_storage = None
        # The analysis interval is fully after the storage interval:
        elif startdate_analysis_dt > stopdate_storage_dt and stopdate_analysis_dt > stopdate_storage_dt:
            # We pull the full data up until the analysis interval, to fill missing data in storage
            startdate_dataprovider = analyzer.datetime2str(stopdate_storage_dt)
            stopdate_dataprovider = analyzer.datetime2str(stopdate_analysis_dt)
            startdate_from_storage = None
            stopdate_from_storage = None
        # The analysis interval is partially overlapping at the beginning of the storage interval:
        elif startdate_analysis_dt < startdate_storage_dt and stopdate_analysis_dt <= stopdate_storage_dt:
            startdate_dataprovider = analyzer.datetime2str(startdate_analysis_dt)
            stopdate_dataprovider = analyzer.datetime2str(startdate_storage_dt)  # Only obtain remaining data
            startdate_from_storage = analyzer.datetime2str(startdate_storage_dt)
            stopdate_from_storage = analyzer.datetime2str(stopdate_analysis_dt)
        # The analysis interval is partially overlapping at the end of the storage interval:
        elif startdate_analysis_dt <= stopdate_storage_dt < stopdate_analysis_dt:
            startdate_dataprovider = analyzer.datetime2str(stopdate_storage_dt)  # Only obtain remaining data
            stopdate_dataprovider = analyzer.datetime2str(stopdate_analysis_dt)
            startdate_from_storage = analyzer.datetime2str(startdate_analysis_dt)
            stopdate_from_storage = analyzer.datetime2str(stopdate_storage_dt)
        else:
            raise RuntimeError("This should not have happened - not all cases covered?")

    else:  # Data storage file is not existing: (a new one was created above already)
        startdate_dataprovider = analyzer.datetime2str(startdate_analysis_dt)
        stopdate_dataprovider = analyzer.datetime2str(stopdate_analysis_dt)
        startdate_from_storage = None
        stopdate_from_storage = None

    logging.debug("Will (try to) obtain these dates from provider and marketdata-storage:")
    logging.debug(f"Provider:\tStartdate: {startdate_dataprovider}\tStopdate: {stopdate_dataprovider}")
    logging.debug(f"Storage:\t\tStartdate: {startdate_storage}\tStopdate: {stopdate_storage}")
    return startdate_dataprovider, stopdate_dataprovider, startdate_from_storage, stopdate_from_storage


def obtain_data_from_storage_and_provider(startdate_dataprovider, stopdate_dataprovider,
                                          startdate_from_storage, stopdate_from_storage, storage, storageobj, provider):
    if storageobj is None:
        raise RuntimeError("Storage object must be given!")
    storagedates = None
    storageprices = None
    providerdates = None
    providerprices = None
    if startdate_from_storage is not None and stopdate_from_storage is not None:
        # Storage-data retrieval necessary
        try:
            ret = storage.get_stored_data(storageobj, (startdate_from_storage, stopdate_from_storage))
            if ret is not None:
                storagedates, storageprices = ret
                if len(storagedates) != len(storageprices):
                    raise RuntimeError("Lists should be of identical length")
                print("Obtained some data from storage.")
                debuglen = min(len(storagedates), 5)
                logging.debug("Obtained data from storage. First few entries:")
                for i in range(debuglen):
                    logging.debug(f"Date: {storagedates[i]}\tValue: {storageprices[i]:.3f}")
            else:
                logging.debug("Did not obtain storage-data")
        except:
            raise RuntimeError("Failed to retrieve stored data. This should work at this point.")

    if startdate_dataprovider is not None and stopdate_dataprovider is not None:
        # Online data retrieval necessary
        try:
            if isinstance(storageobj, StockData):
                symbol = storageobj.get_id()  # We use the id as symbol, as this can contain non-alphanumeric chars.
                exchange = storageobj.get_exchange()
                ret = provider.get_stock_data(symbol, exchange, startdate_dataprovider, stopdate_dataprovider)
                if ret is not None:
                    print(f"Obtained some provider data for {symbol}")
            elif isinstance(storageobj, ForexData):
                symbol_a = storageobj.get_symbol_a()
                symbol_b = storageobj.get_symbol_b()
                ret = provider.get_forex_data(symbol_a, symbol_b, startdate_dataprovider, stopdate_dataprovider)
                if ret is not None:
                    print(f"Obtained some provider data for the currencies {symbol_a} and {symbol_b}")
            elif isinstance(storageobj, IndexData):
                symbol = storageobj.get_id()  # We use the id as symbol, as this can contain non-alphanumeric chars.
                ret = provider.get_stock_data(symbol, "", startdate_dataprovider, stopdate_dataprovider)
                if ret is not None:
                    print(f"Obtained some provider data for the stock market index {symbol}")
            else:
                print("Not implemented yet!")
            if ret is not None:
                providerdates, providerprices = ret
                if len(providerdates) != len(providerprices):
                    print("Lists should be of identical length. Will throw an error.")
                    raise Exception()  # Raise without statement to trigger the try-catch loop, print the message above.
                logging.debug("Obtained data from an online provider. First few data-points:")
                debuglen = min(len(providerdates), 5)
                for i in range(debuglen):
                    logging.debug(f"Date: {providerdates[i]}\t Value: {providerprices[i]:.3f}")
                splits = storageobj.get_splits()  # This is currently only used for stocks/could also be done above,
                # but all storageobj implement this.
                if len(splits) > 0:
                    providerdates, providerprices = storage.apply_splits(splits, (providerdates, providerprices))
                    print("Split(s) are detected in the storage-csv. Will modify provider data.")

            else:
                logging.debug("Did not obtain provider-data.")
        except:
            print("Failed to obtain provider data. An (unknown?) error has occurred.")
    return storagedates, storageprices, providerdates, providerprices


def post_process_provider_storage_data(storagedates, storageprices, providerdates, providerprices, storage, storageobj,
                                       analyzer):
    # Merge the dataprovider and storage data if necessary:
    full_dates = None
    full_prices = None
    write_to_file = False
    if storagedates is None and providerdates is None:
        # Neither online nor storage data is available. Transactions must be used.
        full_dates = None
        full_prices = None
        write_to_file = False
    elif storagedates is None and providerdates is not None:
        # Only online data available. We still merge with the storage-data (whicht might cover a different
        # range, but that is OK; we do this to be able to write back to file below).
        full_dates, full_prices = storage.fuse_storage_and_provider_data(storageobj,
                                                                         (providerdates,
                                                                          providerprices),
                                                                         tolerance_percent=3.0,
                                                                         storage_is_groundtruth=True)
        write_to_file = True
    elif storagedates is not None and providerdates is None:
        # Only storage data available
        full_dates = storagedates
        full_prices = storageprices
        write_to_file = False
    elif storagedates is not None and providerdates is not None:
        # Both provider and storage data available: Merging needed.
        full_dates, full_prices = storage.fuse_storage_and_provider_data(storageobj,
                                                                         (providerdates,
                                                                          providerprices),
                                                                         tolerance_percent=3.0,
                                                                         storage_is_groundtruth=True)
        write_to_file = True
    else:
        raise RuntimeError("All cases should have been covered. Missing elif-statement?")

    if full_dates is not None:
        if dateoperations.check_dates_consecutive(full_dates, analyzer) is False:
            raise RuntimeError("The obtained market-price-dates are not consecutive.")

    return full_dates, full_prices, write_to_file
