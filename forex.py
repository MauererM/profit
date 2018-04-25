"""Implements a class that stores foreign exchange rates and provides conversion functions

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import dataprovider_google as dataprovider
import dateoperations
import stringoperations
import files
import marketdata


class ForexRates:
    """Obtains online forex data (through the dataprovider) and/or obtains the required prices from the
    marketdata-folder
    """

    def __init__(self, currency_str, basecurrency_str, marketdata_folder_str, marketdata_dateformat_str,
                 marketdata_delimiter_str, startdate_str, stopdate_str, dateformat_str):
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
        try:
            dates, rates = dataprovider.get_forex_data(self.currency, self.basecurrency, self.startdate, self.stopdate,
                                                       self.dateformat)
            success = True
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
                                                                                dates, rates)

            # The available market-data (from the dataprovider and the database) might not reach back to the
            # desired startdate! Check it:
            dates_full_start = stringoperations.str2datetime(dates_full[0], self.dateformat)
            dates_full_stop = stringoperations.str2datetime(dates_full[-1], self.dateformat)
            if dates_full_start > startdate_dt:
                print("Available rates (data provider and stored market-data) are only available from the " +
                      dates_full[0] + " onwards. Earliest available data will be extrapolated backwards.")
            if dates_full_stop < stopdate_dt:
                print("Available rates (data provider and stored market-data) are only available until the " +
                      dates_full[-1] + ". Latest available data will be extrapolated forwards.")

            # Crop the data to the desired period:
            dates_crop, rates_crop = dateoperations.format_datelist(dates_full, rates_full,
                                                                    self.startdate, self.stopdate,
                                                                    self.dateformat,
                                                                    zero_padding_past=False,
                                                                    zero_padding_future=False)
            # Interpolate the data to get a consecutive list:
            self.rate_dates, self.rates = dateoperations.interpolate_data(dates_crop, rates_crop,
                                                                          self.dateformat)
            self.pricedata_avail = True

        # It was not possible to obtain rates-data: Use potentially recorded historic data in the marketdata-folder
        else:
            print("\nCould not obtain updated forex rates for " + self.currency + " and " + self.basecurrency)
            # Check, if there is a marketdata-file if yes: import the data:
            if files.file_exists(self.marketdata_filepath) is True:
                print("Using forex-data in the existing market-data-file: " + self.marketdata_filepath)
                dates, rates = marketdata.import_marketdata_from_file(self.marketdata_filepath,
                                                                      self.marketdata_dateformat,
                                                                      self.dateformat, self.marketdata_delimiter)

                # Format the data such that it matches the analysis-range:
                dates_start = stringoperations.str2datetime(dates[0], self.dateformat)
                dates_stop = stringoperations.str2datetime(dates[-1], self.dateformat)
                if dates_start > startdate_dt:
                    print("Available rates (stored market-data) are only available from the " +
                          dates[0] + " onwards. Earliest available data will be extrapolated backwards.")
                if dates_stop < stopdate_dt:
                    print("Available rates (stored market-data) are only available until the " +
                          dates[-1] + ". Latest available data will be extrapolated forwards.")

                # Crop the data to the desired period:
                dates_crop, rates_crop = dateoperations.format_datelist(dates, rates,
                                                                        self.startdate, self.stopdate,
                                                                        self.dateformat,
                                                                        zero_padding_past=False,
                                                                        zero_padding_future=False)
                # Interpolate the data to get a consecutive list:
                self.rate_dates, self.rates = dateoperations.interpolate_data(dates_crop, rates_crop,
                                                                              self.dateformat)
                self.pricedata_avail = True

            # Really no price-data available:
            else:
                self.pricedata_avail = False
                # We cannot continue, forex-data is a must, as otherwise the asset values are not known.
                raise RuntimeError("No forex data available for " +
                                   self.currency + " and " + self.basecurrency +
                                   ". Provide the data in a marketdata-file. Desired filename: " +
                                   self.marketdata_filepath)

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
        conv_val = []
        for idx, date in enumerate(datelist):
            # Check, if the current date is in the forexdates-range.
            indexes = [i for i, x in enumerate(self.rate_dates) if x == date]
            if not indexes:
                raise RuntimeError("Did not find required forex-date. Currency: " + self.currency +
                                   ". Desired date: " + date)
            else:
                if len(indexes) > 1:
                    raise RuntimeError("The forex-dates are not consecutive. Detected more than one identical entry.")
                conv_val.append(vallist[idx] * self.rates[indexes[0]])

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
        else:
            raise RuntimeError("No forex rates available. Currency: " + self.currency + "Basecurrency: " +
                               self.basecurrency)
