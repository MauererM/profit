"""Implements a class that stores foreign exchange rates and provides conversion functions

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import re
import dateoperations
import stringoperations
import files


class ForexData:
    """Represents data from a marketdata-csv.
    Forex files have this format:
    forex + Symbol A + Symbol B:
    "forex_[a-zA-Z0-9]{1,5}_[a-zA-Z0-9]{1,5}\.csv"
    """

    FORMAT_FNAME_GROUPS = r'forex_([a-zA-Z0-9]{1,5})_([a-zA-Z0-9]{1,5})\.csv'

    def __init__(self, pathname, interpol_days, data):
        self.pname = pathname
        self.interpol_days = interpol_days
        self.dates = data[0]
        self.values = data[1]

        # From the pathname, extract the name of the file and its constituents.
        self.fname = files.get_filename_from_path(self.pname)
        match = re.match(self.FORMAT_FNAME_GROUPS, self.fname)
        groups = match.groups()
        self.symbol_a = groups[0]
        self.symbol_b = groups[1]


class ForexRates:
    """Obtains online forex data (through the dataprovider) and/or obtains the required prices from the
    marketdata-folder
    """

    def __init__(self, currency_str, basecurrency_str, marketdata_folder_str, marketdata_dateformat_str,
                 marketdata_delimiter_str, startdate_str, stopdate_str, dateformat_str, dataprovider, analyzer):
        """ForexRates constructor: Obtains the required data from the dataprovider.
        The exchange rates are obtained such that the currency can be multiplied with the rates to get the value in the
        base currency.
        :param currency_str: String that encodes the currency, e.g., "EUR"
        :param basecurrency_str: String that encodes the basecurrency, e.g., "CHF"
        :param marketdata_folder_str: String that encodes the folder name, where the marketdata-files are located
        :param marketdata_dateformat_str: String that encodes the dateformat of the marketdata-files
        :param marketdata_delimiter_str: String that encodes the delimiter used in the marketdata-files
        :param startdate_str: String that encodes the start-date of the forex-data
        :param stopdate_str: String that encodes the stop-date of the forex-data
        :param dateformat_str: String that encodes the format of the dates, e.g., "%d.%m.%Y"
        :param dataprovider: Object of the data provider class, e.g., dataprovider_yahoofinance
        """
        self.currency = currency_str
        self.basecurrency = basecurrency_str
        self.startdate = startdate_str
        self.stopdate = stopdate_str
        self.dateformat = dateformat_str
        self.marketdata_folder = marketdata_folder_str
        self.marketdata_dateformat = marketdata_dateformat_str
        self.marketdata_delimiter = marketdata_delimiter_str
        self.pricedata_avail = False  # Indicates if it was possible to obtain prices of the currency
        self.provider = dataprovider
        self.analyzer = analyzer

        # Create the path of the file in the marketdata-folder that (should) hold information of this price-object,
        # or which will be generated.
        # Name of the corresponding marketdata-file:
        self.marketdata_fname = self.get_marketdata_filename()
        self.marketdata_filepath = files.create_path(self.marketdata_folder, self.marketdata_fname)

        # Sanity-Checks:
        startdate_dt = stringoperations.str2datetime(self.startdate, self.dateformat)
        stopdate_dt = stringoperations.str2datetime(self.stopdate, self.dateformat)
        if startdate_dt > stopdate_dt:
            raise RuntimeError("Startdate cannot be after stopdate. Currency: " + self.currency + ", basecurrency: " +
                               self.basecurrency)

        # Obtain the forex-data.
        # Two lists are expected, the first holds a lists of date-strings, and the second holds the exchange rate.
        success = False
        try:
            ret = self.provider.get_forex_data(self.currency, self.basecurrency, self.startdate, self.stopdate)
            if ret is not None:
                dates, rates = ret
                success = True
                print("Obtained exchange rate for " + self.basecurrency + " to " + self.currency)
        except:
            success = False

        # It was possible to obtain forex prices. Update the database, check if the returned values are consistent
        # with existing stored forex-data, and potentially extrapolate the data for the analysis-period
        if success is True:

            # Update the potentially available marketdata-file and cross-check the obtained values, if they match:
            dates_full, rates_full = marketdata.update_check_marketdata_in_file(self.marketdata_filepath,
                                                                                self.marketdata_dateformat,
                                                                                self.dateformat,
                                                                                self.marketdata_delimiter,
                                                                                dates, rates, self.analyzer)

            # The returned forex data might not be available until today (e.g., if this is run on a weekend).
            # Extend the data accordingly into the future. Note: In Forex, this is (probably) OK to do (in investments,
            # it is NOT OK to do this, as there, the manually entered transactions-data may not be overwritten. But in
            # Forex, there is no manually entered transactions-data that could take precedent.
            lastdate_dt = self.analyzer.str2datetime(dates_full[-1])
            if stopdate_dt > lastdate_dt:
                dates_full, rates_full = dateoperations.extend_data_future(dates_full, rates_full, self.stopdate,
                                                                           self.analyzer, zero_padding=False)

            # Interpolate the data to get a consecutive list:
            dates_full, rates_full = dateoperations.interpolate_data(dates_full, rates_full, self.analyzer)

            # The available market-data (from the dataprovider and the database) might not reach back to the
            # desired startdate! Check it:
            dates_full_start = self.analyzer.str2datetime(dates_full[0])
            dates_full_stop = self.analyzer.str2datetime(dates_full[-1])
            if dates_full_start > startdate_dt:
                print("Available rates (data provider and stored market-data) are only available from the " +
                      dates_full[0] + " onwards. Earliest available data will be extrapolated backwards.")
            if dates_full_stop < stopdate_dt:
                print("Available rates (data provider and stored market-data) are only available until the " +
                      dates_full[-1] + ". Latest available data will be extrapolated forwards.")

            # Crop the data to the desired period:
            self.rate_dates, self.rates = dateoperations.format_datelist(dates_full, rates_full,
                                                                         self.startdate, self.stopdate,
                                                                         self.analyzer,
                                                                         zero_padding_past=False,
                                                                         zero_padding_future=False)

            # Create a dictionary of available dates; this speeds up further searches within the available data:
            self.__create_date_dictionary(self.rate_dates)

            self.pricedata_avail = True

        # It was not possible to obtain rates-data: Use potentially recorded historic data in the marketdata-folder
        else:
            print("Could not obtain updated forex rates for " + self.currency + " and " + self.basecurrency)
            # Check, if there is a marketdata-file if yes: import the data:
            if files.file_exists(self.marketdata_filepath) is True:
                print("Using forex-data in the existing market-data-file: " + self.marketdata_filepath)
                dates, rates = marketdata.import_marketdata_from_file(self.marketdata_filepath,
                                                                      self.marketdata_dateformat,
                                                                      self.dateformat, self.marketdata_delimiter,
                                                                      self.analyzer)

                dates_start = self.analyzer.str2datetime(dates[0])
                dates_stop = self.analyzer.str2datetime(dates[-1])
                if dates_start > startdate_dt:
                    print("Available rates (stored market-data) are only available from the " +
                          dates[0] + " onwards. Earliest available data will be extrapolated backwards.")
                if dates_stop < stopdate_dt:
                    print("Available rates (stored market-data) are only available until the " +
                          dates[-1] + ". Latest available data will be extrapolated forwards.")

                # The returned forex data might not be available until today.
                # Extend the data accordingly into the future.
                # DO NOT DO THIS!
                # lastdate_dt = stringoperations.str2datetime(dates[-1], self.dateformat)
                # if stopdate_dt > lastdate_dt:
                #    dates, rates = dateoperations.extend_data_future(dates, rates, self.stopdate,
                #                                                     self.dateformat, zero_padding=False)

                # Interpolate the data to get a consecutive list:
                dates, rates = dateoperations.interpolate_data(dates, rates, self.analyzer)

                # Crop the data to the desired period:
                self.rate_dates, self.rates = dateoperations.format_datelist(dates, rates,
                                                                             self.startdate, self.stopdate,
                                                                             self.analyzer,
                                                                             zero_padding_past=False,
                                                                             zero_padding_future=False)

                # Create a dictionary of available dates; this speeds up further searches within the available data:
                self.__create_date_dictionary(self.rate_dates)

                self.pricedata_avail = True

            # Really no price-data available:
            else:
                self.pricedata_avail = False
                # We cannot continue, forex-data is a must, as otherwise the asset values are not known.
                raise RuntimeError("No forex data available for " +
                                   self.currency + " and " + self.basecurrency +
                                   ". Provide the data in a marketdata-file. Desired filename: " +
                                   self.marketdata_filepath)

    def __create_date_dictionary(self, dates):
        """
        Create a dictionary of the available dates for faster future lookup/matching of partial data to the available
        data. The key is the date, and the value is the index.
        :param dates: List of strings.
        """
        index_map = {}
        for idx, date in enumerate(dates):
            if date not in index_map:
                index_map[date] = idx  # For each date (which is the key), store the index
            else:
                raise RuntimeError("Received duplicated date to create date-dictionary")
        self.rate_dates_dict = index_map

    def get_marketdata_filename(self):
        """Returns the filename of the corresponding file in the marketdata-folder
        :return: String of the filename, with extension (".txt")
        """
        return "forex_" + self.currency + "_" + self.basecurrency + ".txt"

    def perform_conversion(self, datelist, vallist):
        """Perform a forex-conversion.
        :param datelist: List of strings of dates
        :param vallist: Corresponding list of values
        :return: List of converted values, corresponding to the datelist
        """
        if self.pricedata_avail is False:
            raise RuntimeError("Cannot perform currency conversion. Forex-data not available. "
                               "Should have been obtained in the constructor, though...")

        # Sanity-check:
        if len(datelist) != len(vallist):
            raise RuntimeError("The specified date- and value-lists must match in length.")

        # Convert the values:
        matches = [self.rate_dates_dict[key] for key in datelist if key in self.rate_dates_dict]
        if len(matches) != len(set(matches)) or len(matches) != len(vallist):  # This should really not happen here
            raise RuntimeError("The forex-dates are not consecutive, have duplicates, or miss data.")
        conv_val = [vallist[i] * self.rates[idx] for i, idx in enumerate(matches)]

        return conv_val

    def get_currency(self):
        """Return the currency (as string)"""
        return self.currency

    def get_basecurrency(self):
        """Return the basecurrency (as string)"""
        return self.basecurrency

    def get_dates_rates(self):
        """Returns a tuple of the stored forex dates and rates"""
        if self.pricedata_avail is True:
            return self.rate_dates, self.rates
        raise RuntimeError(
            "No forex rates available. Currency: " + self.currency + "Basecurrency: " + self.basecurrency)
