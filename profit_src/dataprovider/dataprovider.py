"""Implements top-level functions that provide financial data from web providers.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2020-2023 Mario Mauerer
"""

import logging
import pkgutil
import inspect
import importlib
from .. import dateoperations
from .provider_abc import DataProvider


class DataproviderMain:
    """The main data-provider class that wraps different data-providers.
    It imports dataproviders from the respective subpackages and initializes them.
    The first functioning data provider will be selected.
    """
    PACKAGE_NAME = "dataprovider"

    def __init__(self, analyzer):
        """
        """
        self.dateformat = analyzer.get_dateformat()
        self.analyzer = analyzer

        # Traverse the package hierarchy to find the "dataprovider" top-level package. Within this package, we then
        # find the data providers.
        providerpackage = self.__find_package(self.PACKAGE_NAME, path=None)

        # Find all subpackages:
        submodules = pkgutil.walk_packages(providerpackage.__path__, providerpackage.__name__ + '.')
        loaded_modules = []
        for _, name, is_pkg in submodules:
            if is_pkg:
                try:
                    submodule = importlib.import_module(name)
                    loaded_modules.append(submodule)
                except ImportError:
                    print(f"Could not load module {name}.")
        if len(loaded_modules) == 0:
            logging.error("Could not discover any dataprovider subpackage. Is the package-discovery working correctly?")

        # Find all classes that inherit from the provider's ABC. These are our entry points.
        classes = []  # Find the classes in the discovered modules that inherit the ABC for the dataprovider.
        for module in loaded_modules:
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    if issubclass(obj, DataProvider):
                        if obj is not DataProvider:
                            classes.append(obj)

        if len(loaded_modules) != len(classes):
            raise RuntimeError("There seem to be multiple or not enough classes in the loaded modules that "
                               "inherit from the dataprovider ABC")

        print(f"Discovered {len(classes):d} data provider packages.")

        # The list of available/feasible data providers. The last provider here should be DataproviderEmpty
        self.providers = classes

        self.active_provider = None

        # Initialize the data providers; select the first provider that successfully initializes
        for provider in self.providers:
            p = provider(self.dateformat)
            if p.initialize() is True:
                self.active_provider = p
                print(f"Data provider {p.get_name()} successfully initialized")
                break
            logging.warning(f"Failed to initialize provider {p.get_name()}")
        # Now, we either have a functioning provider initialized, or the Empty-provider (which will trigger
        # the falling functions to fall back to alternative means, making the data-source selection somewhat automatic)
        if self.active_provider is None:
            logging.warning(
                "Failed to initialize any data provider. Will rely on transactions-data or stored market data.")

    def __find_package(self, package_name, path=None, parent_name=''):
        """
        Find a package or subpackage by name.
        :param package_name: Name of the package to find.
        :param path: List of paths where to start the search or None for all paths.
        :return: The module object if found, None otherwise.
        """
        for _, name, ispkg in pkgutil.iter_modules(path):
            full_name = f"{parent_name}.{name}" if parent_name else name
            if name == package_name:
                mod = importlib.import_module(full_name)
                return mod
            if ispkg:
                # Recursively search in subpackages
                package = importlib.import_module(full_name)
                found_package = self.__find_package(package_name, package.__path__, full_name)
                if found_package is not None:
                    return found_package
        return None

    def get_stock_data(self, sym_stock, sym_exchange, startdate, stopdate):
        """Provides stock-prices (values at closing-time of given days; historic data).
        Note: The returned data might not be of sufficient length into the past (e.g., might not reach back to
        startdate!)
        This is done on purpose, the caller has to deal with this, he can then take appropriate action. This keeps this
        function as simple as possible.
        But: missing data in the returned interval is interpolated, so the returned dates and rates are consecutive and
        corresponding.
        :param sym_stock: String encoding the name of the stock, e.g., "TSLA"
        :param sym_exchange: String encoding the name of the exchange, e.g., "SWX"
        :param startdate: String encoding the day for the first price
        :param stopdate: String encoding the day of the last price
        :return: Tuple of two lists: the first is a list of strings of _consecutive_ dates, and the second is a list
        of the corresponding strock prices. Some data might be interpolated/extrapolated, as the API does not
        always return data for consecutive days (public holidays, weekends etc.)
        """
        if self.active_provider is None:
            return None

        self.__perform_date_sanity_check(startdate, stopdate)

        res = self.active_provider.retrieve_stock_data(sym_stock, startdate, stopdate, sym_exchange)
        if res is not None:
            pricedates, stockprices = res  # List of strings and floats
        else:
            logging.warning(f"Failed to obtain provider data for stock symbol: {sym_stock}")
            return None

        res = self.__post_process_dataprovider_data(pricedates, stockprices, startdate, stopdate)
        if res is not None:
            pricedates_full, stockprices_full = res
            return pricedates_full, stockprices_full
        return None

    def get_forex_data(self, sym_a, sym_b, startdate, stopdate):
        """Provides foreign-exchange rates for two currencies
        :param sym_a: String encoding the first currency, e.g., "CHF"
        :param sym_b: String encoding the second currency, e.g., "EUR"
        :param startdate: String encoding the day for the first rate
        :param stopdate: String encoding the day of the last rate
        :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        :return: Tuple of two lists: the first is a list of strings of consecutive dates, and the second is a list
        of the corresponding foreign exchange rates. Some data might be interpolated/extrapolated, as the API does not
        always return data for consecutive days (public holidays etc...)
        """
        if self.active_provider is None:
            return None

        self.__perform_date_sanity_check(startdate, stopdate)

        res = self.active_provider.retrieve_forex_data(sym_a, sym_b, startdate, stopdate)
        if res is not None:
            forexdates, forexrates = res  # List of strings and floats
        else:
            logging.warning(f"Failed to obtain exchange rates for: {sym_a} and {sym_b}")
            return None

        res = self.__post_process_dataprovider_data(forexdates, forexrates, startdate, stopdate)
        if res is not None:
            forexdates_full, forexrates_full = res
            return forexdates_full, forexrates_full
        return None

    def __perform_date_sanity_check(self, startdate, stopdate):
        """
        Sanity-checks the dates. Raises errors if something is wrong.
        :param startdate: String encoding the day for the first rate
        :param stopdate: String encoding the day of the last rate
        :return: The epoch values p1, p2 that correspond to start- and stopdate,
        and the datetime-objects of start- and stopdate.
        """
        # Use datetime, and sanity check:
        startdate_dt = self.analyzer.str2datetime(startdate)
        stopdate_dt = self.analyzer.str2datetime(stopdate)
        today = dateoperations.get_date_today(self.dateformat, datetime_obj=True)
        if startdate_dt > stopdate_dt:
            raise RuntimeError("Startdate has to be before stopdate")
        if stopdate_dt > today:
            raise RuntimeError("Cannot (unfortunately) obtain data from the future.")

    def __post_process_dataprovider_data(self, dates, values, startdate, stopdate):
        """
        Post-processes the data provided by the dataprovider.
        This is identical for both stocks and forex-data (as they are the same: Time-series values).
        :param dates: List of strings of dates as provided by the data provider. List of strings.
        :param values: (Corresponding) list of values provided by the data provider. Likely floats.
        :param startdate: String of (desired) startdate
        :param stopdate: String of (desired) stopdate
        :param stopdate_dt: Datetime-obj relating to stopdate
        :return: Tuple of two lists: the first is a list of strings of _consecutive_ dates, and the
        second is a list of the corresponding values. Some data might be interpolated/extrapolated, as
        the data provider does not always return data for consecutive days (public holidays etc...)
        """

        # Sanity check:
        if len(dates) != len(values):
            logging.warning("Returned time- and value-data is of unequal length. Will not use provided data.")
            return None

        stopdate_dt = self.analyzer.str2datetime(stopdate)

        # Don't accept entries with (near-) zero value: Two new lists that still correspond.
        dates_red = [date for i, date in enumerate(dates) if values[i] > 1e-6]
        values_red = [value for value in values if value > 1e-6]

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

        # Crop the data to the desired range. It may still contain non-consecutive days (i.e., holes).
        # The crop-function will not throw errors if the start/stop-dates are outside the date-list from
        # the data provider.
        dates, values = dateoperations.crop_datelist(dates_red, values_red, startdate, stopdate, self.analyzer)

        # Check if there is still data left:
        if len(values) < 1:
            logging.warning("Data unavailable for desired interval. "
                            "Maybe change analysis period. Will not use provided data.")
            return None

        # Fill in missing data in the vector
        dates_full, values_full = dateoperations.interpolate_data(dates, values, self.analyzer)

        MAX_PROVIDER_INTERPOLATION_DAYS = 10
        if abs(len(dates_full) - len(dates)) > MAX_PROVIDER_INTERPOLATION_DAYS:
            logging.warning(f"Interpolated more than {MAX_PROVIDER_INTERPOLATION_DAYS} days when retrieved "
                            f"provider data.")

        return dates_full, values_full
