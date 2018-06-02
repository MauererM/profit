"""Implements a class that stores market prices of traded assets

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import files
import dataprovider_google as dataprovider
import stringoperations
import dateoperations
import marketdata


class MarketPrices:
    """Obtains online market data (through the dataprovider) and/or obtains the required prices from the
    marketdata-folder
    """

    def __init__(self, symbol_str, exchange_str, currency_str, marketdata_folder_str, marketdata_dateformat_str,
                 marketdata_delimiter_str, startdate_str, stopdate_str, dateformat_str):
        """Constructor. Sets up internal storage.
        Tries to obtain updated prices from the dataprovider of the corresponding asset.
        Matches potentially updated data with the potentially stored data in the marketdata-folder
        Updates files in the marketdata-folder accordingly.
        Stores market-data, or not, if not possible
        :param symbol_str: String of the corresponding market-symbol
        :param exchange_str: String of the exchange, where the symbol is traded
        :param currency_str: String of the currency
        :param marketdata_folder_str: String of the folder, where marketdata is stored
        :param marketdata_dateformat_str: String of the dateformat used with the marketdata-files
        :param marketdata_delimiter_str: String of the delimiter used with the marketdata-files
        :param startdate_str: Data (market prices) is obtained/created from this date onwards
        :param stopdate_str: Data (market prices) is obtained/created until this date
        :param dateformat_str: String of the dateformat as used throughout the project
        """
        self.symbol = symbol_str
        self.exchange = exchange_str
        self.currency = currency_str
        self.startdate = startdate_str
        self.stopdate = stopdate_str
        self.dateformat = dateformat_str
        self.marketdata_folder = marketdata_folder_str
        self.marketdata_dateformat = marketdata_dateformat_str
        self.marketdata_delimiter = marketdata_delimiter_str
        self.pricedata_avail = False  # Indicates if it was possible to obtain prices of the asset.

        # Create the path of the file in the marketdata-folder that (should) hold information of this price-object,
        # or which will be generated.
        # Get the name of the corresponding marketdata-file
        self.marketdata_fname = self.get_marketdata_filename()
        self.marketdata_filepath = files.create_path(self.marketdata_folder, self.marketdata_fname)

        # Sanity-Checks:
        startdate_dt = stringoperations.str2datetime(self.startdate, self.dateformat)
        stopdate_dt = stringoperations.str2datetime(self.stopdate, self.dateformat)
        if startdate_dt > stopdate_dt:
            raise RuntimeError("Startdate cannot be after stopdate. Symbol: " + self.symbol + ", exchange: " +
                               self.exchange)

        # Obtain the market prices:
        try:
            # print("Trying to obtain prices for " + self.symbol + ", traded at " + self.exchange +
            #      " from the data provider.")

            dates, prices = dataprovider.get_stock_data(self.symbol, self.exchange, self.startdate, self.stopdate,
                                                        self.dateformat)
            success = True
        except:
            success = False

        # It was possible to obtain market prices. Update the database, check if the returned values are consistent
        # with existing stored market-data, and potentially extrapolate the data for the analysis-period
        if success is True:
            # print("Success. Updating marketdata-file and cross-checking the values. File: " +
            # self.marketdata_filepath)

            # Update the potentially available marketdata-file and cross-check the obtained values, if they match:
            dates_full, prices_full = marketdata.update_check_marketdata_in_file(self.marketdata_filepath,
                                                                                 self.marketdata_dateformat,
                                                                                 self.dateformat,
                                                                                 self.marketdata_delimiter,
                                                                                 dates, prices)

            # The returned market data might not be available until today (e.g., if this is run on a weekend).
            # Extend the data accordingly into the future.
            lastdate_dt = stringoperations.str2datetime(dates_full[-1], self.dateformat)
            if stopdate_dt > lastdate_dt:
                dates_full, prices_full = dateoperations.extend_data_future(dates_full, prices_full, self.stopdate,
                                                                            self.dateformat, zero_padding=False)

            # Store the latest available price and date, for the holding-period return analysis
            # (It needs to be un-extrapolated)
            self.latestrealprice = prices_full[-1]
            self.latestrealpricedate = dates_full[-1]

            # The available market-data (from the dataprovider and the database) might not reach back to the
            # desired startdate! Check it:
            dates_full_start = stringoperations.str2datetime(dates_full[0], self.dateformat)
            dates_full_stop = stringoperations.str2datetime(dates_full[-1], self.dateformat)
            if dates_full_start > startdate_dt:
                print("Available prices (data provider and stored market-data) are only available from the " +
                      dates_full[0] + " onwards. Earliest available data will be extrapolated backwards. Symbol: " +
                      self.symbol + ", exchange: " + self.exchange)
            if dates_full_stop < stopdate_dt:
                print("Available prices (data provider and stored market-data) are only available until the " +
                      dates_full[-1] + ". Latest available data will be extrapolated forwards. Symbol: " +
                      self.symbol + ", exchange: " + self.exchange)
                print("CAREFUL: Update the market-data file manually with the most recent value, or the holding period"
                      " returns cannot be calculated. Symbol: " +
                      self.symbol + ", exchange: " + self.exchange)

            # Crop the data to the desired period:
            dates_crop, prices_crop = dateoperations.format_datelist(dates_full, prices_full,
                                                                     self.startdate, self.stopdate,
                                                                     self.dateformat,
                                                                     zero_padding_past=False,
                                                                     zero_padding_future=False)
            # Interpolate the data to get a consecutive list:
            self.market_dates, self.market_prices = dateoperations.interpolate_data(dates_crop, prices_crop,
                                                                                    self.dateformat)
            self.pricedata_avail = True

        # It was not possible to obtain market-data: Use potentially recorded historic data in the marketdata-folder
        else:
            print("\nCould not obtain updated market prices for " + self.symbol)
            # Check, if there is a marketdata-file if yes: import the data:
            if files.file_exists(self.marketdata_filepath) is True:
                print("Using data in the existing market-data-file: " + self.marketdata_filepath)
                dates, prices = marketdata.import_marketdata_from_file(self.marketdata_filepath,
                                                                       self.marketdata_dateformat,
                                                                       self.dateformat, self.marketdata_delimiter)

                # The returned market data might not be available until today.
                # Extend the data accordingly into the future.
                lastdate_dt = stringoperations.str2datetime(dates[-1], self.dateformat)
                if stopdate_dt > lastdate_dt:
                    dates, prices = dateoperations.extend_data_future(dates, prices, self.stopdate,
                                                                      self.dateformat, zero_padding=False)

                # Store the latest available price and date, for the holding-period return analysis
                # (It needs to be un-extrapolated)
                self.latestrealprice = prices[-1]
                self.latestrealpricedate = dates[-1]

                # Format the data such that it matches the analysis-range:
                dates_start = stringoperations.str2datetime(dates[0], self.dateformat)
                dates_stop = stringoperations.str2datetime(dates[-1], self.dateformat)
                if dates_start > startdate_dt:
                    print("Available prices (stored market-data) are only available from the " +
                          dates[0] + " onwards. Earliest available data will be extrapolated backwards.")
                if dates_stop < stopdate_dt:
                    print("Available prices (stored market-data) are only available until the " +
                          dates[-1] + ". Latest available data will be extrapolated forwards.")
                    print("CAREFUL: Update the market-data file manually with the most recent value, "
                          "or the holding period returns cannot be calculated.")

                # Crop the data to the desired period:
                dates_crop, prices_crop = dateoperations.format_datelist(dates, prices,
                                                                         self.startdate, self.stopdate,
                                                                         self.dateformat,
                                                                         zero_padding_past=False,
                                                                         zero_padding_future=False)
                # Interpolate the data to get a consecutive list:
                self.market_dates, self.market_prices = dateoperations.interpolate_data(dates_crop, prices_crop,
                                                                                        self.dateformat)
                self.pricedata_avail = True

            # Really no price-data available:
            else:
                print("No financial data available for " + self.symbol)
                print("Provide an update-transaction to deliver the most recent price of the asset. "
                      "Otherwise, the holding period returns cannot be calculated.")
                self.pricedata_avail = False

    def get_marketdata_filename(self):
        """Returns the filename of the corresponding file in the marketdata-folder
        :return: String of the filename, with extension (".txt")
        """
        return "price_" + self.symbol + "_" + self.exchange + "_" + self.currency + ".txt"

    def get_latest_price_date(self):
        """Returns the latest available price and date, that has not been extrapolated.
        For the calculation of the holding period return.
        :return: Tuple of date and value
        """
        return self.latestrealpricedate, self.latestrealprice

    def is_price_avail(self):
        """Return a bool if market prices are available"""
        return self.pricedata_avail

    def get_price_dates(self):
        """Return the list of dates (strings) of the available market-prices"""
        return self.market_dates

    def get_price_values(self):
        """Return the list of values (floats) of the available market-prices"""
        return self.market_prices

    def get_currency(self):
        """Return the currency of the available prices"""
        return self.currency
