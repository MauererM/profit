"""Implements a class that represents an account

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import PROFIT_main as cfg
import setup
import stringoperations
import dateoperations


class Account:
    """Implements an account. Parses transactions, provides analysis-data, performs currency conversions"""

    def __init__(self, ident_str, type_str, purpose_str, currency_str, basecurrency_str, filename_str,
                 transactions_dict, dateformat_str, analyzer):
        """Account constructor
        Use the function parse_account_file to obtain the necessary information from an account file.
        It sets up all internal data structures and analyzes the transactions.
        It also creates some basic data, e.g., it creates complete balance lists
        :param ident_str: String containing the account ID
        :param type_str: String containing the type of asset
        :param purpose_str: String containing the purpose of the account
        :param currency_str: String of the account currency
        :param filename_str: String of the filename associated with this account
        :param transactions_dict: Dictionary with the transactions-data.
        :param dateformat_str: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        """
        self.id = ident_str
        self.type = type_str
        self.purpose = purpose_str
        self.currency = currency_str
        self.basecurrency = basecurrency_str
        self.filename = filename_str
        self.transactions = transactions_dict
        self.dateformat = dateformat_str
        self.analyzer = analyzer
        # Analysis data is not yet prepared:
        self.analysis_data_done = False
        # Forex data has not yet been obtained:
        self.forex_data_given = False
        # Data not yet given:
        self.forex_obj = None
        self.analysis_dates = None
        self.analysis_balances = None
        self.analysis_costs = None
        self.analysis_interests = None

        # Check if the transaction-dates are in order. Allow identical successive days (e.g., multiple payouts on one
        # day are possible)
        if dateoperations.check_date_order(self.transactions[setup.DICT_KEY_DATES], self.analyzer,
                                           allow_ident_days=True) is False:
            raise RuntimeError("Transaction-dates are not in temporal order. But: identical successive dates are "
                               "allowed. Filename: " + self.filename)

        # Check, if the transactions-actions-column only contains allowed strings:
        if stringoperations.check_allowed_strings(self.transactions[setup.DICT_KEY_ACTIONS],
                                                  setup.ACCOUNT_ALLOWED_ACTIONS) is False:
            raise RuntimeError("Actions-column contains faulty strings. Filename: " + self.filename)

        # Check, if the purpose-string only contains allowed purposes:
        if stringoperations.check_allowed_strings([self.purpose], cfg.ASSET_PURPOSES) is False:
            raise RuntimeError("Purpose of Account is not recognized. Filename: " + self.filename)

        # Create a list of consecutive calendar days that corresponds to the date-range of the recorded transactions:
        self.datelist = dateoperations.create_datelist(self.get_first_transaction_date(),
                                                       self.get_last_transaction_date(), self.analyzer)

        # Interpolate the balances, such that the entries in balancelist correspond to the days in datelist.
        _, self.balancelist = dateoperations.interpolate_data(self.transactions[setup.DICT_KEY_DATES],
                                                              self.transactions[setup.DICT_KEY_BALANCES],
                                                              self.analyzer)

        # The cost and interest does not need interpolation. The lists are populated (corresponding to datelist), i.e.,
        # the values correspond to the day they occur, all other values are set to zero
        self.costlist = self.populate_full_list(self.transactions[setup.DICT_KEY_DATES],
                                                self.transactions[setup.DICT_KEY_ACTIONS],
                                                self.transactions[setup.DICT_KEY_AMOUNTS],
                                                setup.STRING_ACCOUNT_ACTION_COST, self.datelist)
        self.interestlist = self.populate_full_list(self.transactions[setup.DICT_KEY_DATES],
                                                    self.transactions[setup.DICT_KEY_ACTIONS],
                                                    self.transactions[setup.DICT_KEY_AMOUNTS],
                                                    setup.STRING_ACCOUNT_ACTION_INTEREST,
                                                    self.datelist)

    def populate_full_list(self, trans_dates, trans_actions, trans_amounts, triggerstring, datelist):
        """Populates a list with amounts of certain transactions
        The dates correspond to the dates in both datelist and trans_dates.
        The type of transaction is given by "triggerstring"
        Values not covered by corresponding dates in trans_dates are set to zero.
        Multiple transactions can occur on the same day, the values are summed up.
        The datelist is created by the class constructor and should hence be in order (i.e., consecutive days only)
        :param trans_dates: List of strings of transaction-dates
        :param trans_actions: List of strings of transaction-actions (e.g., "fee")
        :param trans_amounts: List of floats of corresponding amounts
        :param triggerstring: String used to match the desired transactions (e.g., "fee")
        :param datelist: List of strings of the full date list, spanning all days between the transactions
        :param dateformat: String that specifies the format of the date-strings
        :return: List of transaction-values, for each date in datelist
        """
        # Sanity checks:
        if len(trans_dates) != len(trans_actions) and len(trans_dates) != len(trans_amounts):
            raise RuntimeError("Lists of transaction-dates, actions and amounts must be of equal length. "
                               "Account ID: " + self.id)

        # Convert to datetime objects:
        datelist_dt = [self.analyzer.str2datetime(x) for x in datelist]
        trans_dates_dt = [self.analyzer.str2datetime(x) for x in trans_dates]

        # Check if the date-list covers the full range of the transactions:
        if datelist_dt[0] != trans_dates_dt[0] or datelist_dt[-1] != trans_dates_dt[-1]:
            raise RuntimeError("Boundary-entries of transaction-dates do not match with provided list of dates. "
                               "Account ID: " + self.id)

        value_list = []
        # Iterate through all dates and check if there are any matches with the trigger string
        for date in datelist_dt:
            # Get all indexes of the current date, if it occurs in the transaction-dates-list:
            indexes = [i for i, x in enumerate(trans_dates_dt) if x == date]
            # If no index: current date is not a transaction
            if not indexes:
                value_list.append(0.0)  # No transaction happened
            else:  # indexes points to all transactions on the current day. Check for matching transactions
                sumval = 0
                for i in indexes:
                    if trans_actions[i] == triggerstring:  # Matching transaction: Add all values up
                        sumval += trans_amounts[i]
                value_list.append(sumval)

        # Unify the types, just to be sure:
        value_list = [float(x) for x in value_list]
        return value_list

    def write_forex_obj(self, forex_obj):
        """
        Stores a forex-object with this class, for currency conversions.
        :param forex_obj: The ForexRates-object
        """
        # This is only required if the account holds a foreign currency:
        if self.currency != self.basecurrency:
            # Sanity check: The forex-object must have the correct currency:
            if forex_obj.get_currency() != self.currency or forex_obj.get_basecurrency() != self.basecurrency:
                raise RuntimeError("Currencies of forex-object do not match the asset. Account-ID: " + self.id)
            self.forex_obj = forex_obj
            self.forex_data_given = True

    def set_analysis_data(self, date_start, date_stop):
        """Creates data for further analysis, within the desired date-range.
        Values are converted into the basecurrency.
        Data is cropped or extrapolated to fit the desired range.
        :param date_start: String of a date that designates the date where analysis starts from. Can be earlier
        than recorded data.
        :param date_stop: String of a date that designates the stop-date. Cannot be in the future.
        :param dateformat: String that specifies the format of the date-strings
        """

        # Extrapolate or crop the data:
        # The balance is extrapolated with zeroes into the past, and with the last known values into the future,
        # if extrapolation is necessary.
        self.analysis_dates, self.analysis_balances = dateoperations.format_datelist(self.datelist,
                                                                                     self.balancelist,
                                                                                     date_start, date_stop,
                                                                                     self.analyzer,
                                                                                     zero_padding_past=True,
                                                                                     zero_padding_future=False)
        # The cost and interest-lists need zero-padding in both directions
        _, self.analysis_costs = dateoperations.format_datelist(self.datelist,
                                                                self.costlist,
                                                                date_start, date_stop,
                                                                self.analyzer,
                                                                zero_padding_past=True,
                                                                zero_padding_future=True)

        _, self.analysis_interests = dateoperations.format_datelist(self.datelist,
                                                                    self.interestlist,
                                                                    date_start, date_stop,
                                                                    self.analyzer,
                                                                    zero_padding_past=True,
                                                                    zero_padding_future=True)

        # Check, if a forex-object is given (only required if the account holds foreign currencies)
        if self.currency != self.basecurrency and self.forex_data_given is False:
            raise RuntimeError(
                "Account holds foreign currency. Forex-object is required. Account-currency is: " + self.currency +
                ". Basecurrency is: " + self.basecurrency + ". Account-file is: " + self.filename)

        # Forex conversion required:
        elif self.currency != self.basecurrency and self.forex_data_given is True:
            # Do the currency-conversion:
            self.analysis_balances = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_balances)
            self.analysis_costs = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_costs)
            self.analysis_interests = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_interests)
        # Analysis-data is ready
        self.analysis_data_done = True

    def get_first_transaction_date(self):
        """Returns the date (as string) of the first recorded transaction of the account"""
        return self.transactions[setup.DICT_KEY_DATES][0]

    def get_last_transaction_date(self):
        """Returns the date (as string) of the last recorded transaction of the account"""
        return self.transactions[setup.DICT_KEY_DATES][-1]

    def get_analysis_datelist(self):
        """Return the list of dates of the analysis-data (dates as strings)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis datelist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_dates)

    def get_analysis_valuelist(self):
        """Return the list of values of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis datelist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_balances)

    def get_analysis_costlist(self):
        """Return the list of costs of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis costlist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_costs)

    def get_analysis_payoutlist(self):
        """Return the list of payouts/interest of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis payoutlist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_interests)

    def get_filename(self):
        """Returns the filename (as string) of the corresponding account-file"""
        return self.filename

    def get_currency(self):
        """Returns the currency of the account (as string)"""
        return self.currency

    def get_basecurrency(self):
        """Returns the basecurrency of the account (as string)"""
        return self.basecurrency

    def get_dateformat(self):
        """Returns the date-format of the stored dates (as string)"""
        return self.dateformat

    def get_purpose(self):
        """Returns the purpose of the account (as string)"""
        return self.purpose

    def get_type(self):
        """Returns the type of the account (as string)"""
        return self.type
