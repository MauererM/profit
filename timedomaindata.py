"""Implements a class that stores and manages time-domain data (e.g., from a data provider or storage-system)

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import dateoperations


class StockData:

    def __init__(self, symbol, exchange, currency, analysis_interval, analyzer, storage):
        self.symbol = symbol
        self.exchange = exchange
        self.currency = currency
        self.analysis_startdate, self.analysis_stopdate = analysis_interval
        self.analyzer = analyzer
        self.storage = storage

        # Gather and process the data:
        self.storageobj = self.__get_storage_object()
        if self.storageobj is None:
            self.__create_new_storage_file()  # Create a new file, if it does not yet exist.
        startdate_dataprovider, stopdate_dataprovider, startdate_from_storage, stopdate_from_storage = self.__get_provider_storage_ranges()
        self.__obtain_data_from_storage_and_provider(startdate_dataprovider, stopdate_dataprovider,
                                                     startdate_from_storage, stopdate_from_storage)
        self.__post_process_provider_storage_data()

    def __create_new_storage_file(self):
        self.storage.create_new_storage_file("stock", (self.symbol, self.exchange, self.currency))

    def __get_storage_object(self):
        return self.storage.is_storage_data_existing("stock", (self.symbol, self.exchange, self.currency))

    def __get_provider_storage_ranges(self):
        if self.storageobj is not None:
            startdate_storage, stopdate_storage = self.storage.get_start_stopdate(self.storageobj)
            startdate_analysis_dt = self.analyzer.str2datetime(self.analysis_startdate)
            stopdate_analysis_dt = self.analyzer.str2datetime(self.analysis_stopdate)
        # We only have valid data if the storage object exists, and if it actually already contains data:
        if (self.storageobj is not None) and (startdate_storage is not None) and (stopdate_storage is not None):
            startdate_storage_dt = self.analyzer.str2datetime(startdate_storage)
            stopdate_storage_dt = self.analyzer.str2datetime(stopdate_storage)

            # The storage-interval can not, partially, or over-overlap the analysis interval (and vice versa).
            # Depending on this, different data should be obtained by the data provider.

            # The analysis-interval is fully contained in the market-data: No online retrieval necessary.
            if startdate_storage_dt <= startdate_analysis_dt and stopdate_analysis_dt <= stopdate_storage_dt:
                startdate_dataprovider = None
                stopdate_dataprovider = None
                startdate_from_storage = self.analyzer.datetime2str(startdate_analysis_dt)
                stopdate_from_storage = self.analyzer.datetime2str(stopdate_analysis_dt)
            # The analysis-interval is larger on both ends than the stored data:
            elif startdate_analysis_dt < startdate_storage_dt and stopdate_analysis_dt > stopdate_storage_dt:
                startdate_dataprovider = self.analyzer.datetime2str(startdate_analysis_dt)  # Pull the full data
                stopdate_dataprovider = self.analyzer.datetime2str(stopdate_analysis_dt)
                startdate_from_storage = self.analyzer.datetime2str(startdate_storage_dt)
                stopdate_from_storage = self.analyzer.datetime2str(stopdate_storage_dt)
            # The analysis interval is fully before the storage interval:
            elif startdate_analysis_dt < startdate_storage_dt and stopdate_analysis_dt < startdate_storage_dt:
                startdate_dataprovider = self.analyzer.datetime2str(startdate_analysis_dt)
                # We pull the full data up until the storage interval, to fill missing data in storage
                stopdate_dataprovider = self.analyzer.datetime2str(startdate_storage_dt)
                startdate_from_storage = None
                stopdate_from_storage = None
            # The analysis interval is fully after the storage interval:
            elif startdate_analysis_dt > stopdate_storage_dt and stopdate_analysis_dt > stopdate_storage_dt:
                # We pull the full data up until the analysis interval, to fill missing data in storage
                startdate_dataprovider = self.analyzer.datetime2str(stopdate_storage_dt)
                stopdate_dataprovider = self.analyzer.datetime2str(stopdate_analysis_dt)
                startdate_from_storage = None
                stopdate_from_storage = None
            # The analysis interval is partially overlapping at the beginning of the storage interval:
            elif startdate_analysis_dt < startdate_storage_dt and stopdate_analysis_dt <= stopdate_storage_dt:
                startdate_dataprovider = self.analyzer.datetime2str(startdate_analysis_dt)
                stopdate_dataprovider = self.analyzer.datetime2str(startdate_storage_dt)  # Only obtain remaining data
                startdate_from_storage = self.analyzer.datetime2str(startdate_storage_dt)
                stopdate_from_storage = self.analyzer.datetime2str(stopdate_analysis_dt)
            # The analysis interval is partially overlapping at the end of the storage interval:
            elif startdate_analysis_dt <= stopdate_storage_dt and stopdate_analysis_dt > stopdate_storage_dt:
                startdate_dataprovider = self.analyzer.datetime2str(stopdate_storage_dt)  # Only obtain remaining data
                stopdate_dataprovider = self.analyzer.datetime2str(stopdate_analysis_dt)
                startdate_from_storage = self.analyzer.datetime2str(startdate_analysis_dt)
                stopdate_from_storage = self.analyzer.datetime2str(stopdate_storage_dt)
            else:
                raise RuntimeError("This should not have happened - not all cases covered?")

        else:  # Data storage file is not existing: (a new one was created above already)
            startdate_dataprovider = self.analyzer.datetime2str(startdate_analysis_dt)
            stopdate_dataprovider = self.analyzer.datetime2str(stopdate_analysis_dt)
            startdate_from_storage = None
            stopdate_from_storage = None

        return startdate_dataprovider, stopdate_dataprovider, startdate_from_storage, stopdate_from_storage

    def __obtain_data_from_storage_and_provider(self, startdate_dataprovider, stopdate_dataprovider,
                                                startdate_from_storage, stopdate_from_storage):
        self.storagedates = None
        self.storageprices = None
        self.providerdates = None
        self.providerprices = None
        if startdate_from_storage is not None and stopdate_from_storage is not None:
            # Storage-data retrieval necessary
            try:
                ret = self.storage.get_stored_data(self.storageobj, (startdate_from_storage, stopdate_from_storage))
                if ret is not None:
                    self.storagedates, self.storageprices = ret
                    if len(self.storagedates) != len(self.storageprices):
                        raise RuntimeError("Lists should be of identical length")
            except:
                raise RuntimeError("Failed to retrieve stored data. This should work at this point.")

        if startdate_dataprovider is not None and stopdate_dataprovider is not None:
            # Online data retrieval necessary
            try:
                ret = self.provider.get_stock_data(self.symbol, self.exchange, startdate_dataprovider,
                                                   stopdate_dataprovider)
                if ret is not None:
                    self.providerdates, self.providerprices = ret
                    if len(self.providerdates) != len(self.providerprices):
                        raise RuntimeError("Lists should be of identical length")
                    print(f"Obtained some provider data for {self.symbol}")
            except:
                print(f"Failed to obtain provider data for {self.symbol}")

    def __post_process_provider_storage_data(self):
        # Merge the dataprovider and storage data if necessary:
        self.full_dates = None
        self.full_prices = None
        self.write_to_file = False
        if self.storagedates is None and self.providerdates is None:
            # Neither online nor storage data is available. Transactions must be used. # Todo test this case, too
            self.full_dates = None
            self.full_prices = None
            self.write_to_file = False
        elif self.storagedates is None and self.providerdates is not None:
            # Only online data available. We still merge with the storage-data (whicht might cover a different
            # range, but that is OK; we do this to be able to write back to file below).
            self.full_dates, self.full_prices = self.storage.fuse_storage_and_provider_data(self.storageobj,
                                                                                            (self.providerdates,
                                                                                             self.providerprices),
                                                                                            tolerance_percent=3.0,
                                                                                            storage_is_groundtruth=True)
            self.write_to_file = True
        elif self.storagedates is not None and self.providerdates is None:
            # Only storage data available
            self.full_dates = self.storagedates
            self.full_prices = self.storageprices
            self.write_to_file = False
        elif self.storagedates is not None and self.providerdates is not None:
            # Both provider and storage data available: Merging needed.
            self.full_dates, self.full_prices = self.storage.fuse_storage_and_provider_data(self.storageobj,
                                                                                            (self.providerdates,
                                                                                             self.providerprices),
                                                                                            tolerance_percent=3.0,
                                                                                            storage_is_groundtruth=True)
            self.write_to_file = True
        else:
            raise RuntimeError("All cases should have been covered. Missing elif-statement?")

        if self.full_dates is not None:
            if dateoperations.check_dates_consecutive(self.full_dates, self.analyzer) is False:
                raise RuntimeError(f"The obtained market-price-dates are not consecutive. File: {self.symbol}")

    def get_price_data(self):
        return self.full_dates, self.full_prices

    def storage_to_update(self):
        return self.write_to_file

    def get_storageobj(self):
        return self.storageobj
