"""Implements a class that stores data associated with investments

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import dateoperations
import PROFIT_main as cfg
import stringoperations
import prices
import setup
import helper


class Investment:
    """Implements an investment. Parses transactions, provides analysis-data, performs currency conversions"""

    def __init__(self, id_str, type_str, purpose_str, currency_str, basecurrency_str, symbol_str, exchange_str,
                 filename_str, transactions_dict, dateformat_str, dataprovider):
        """Investment constructor
        Use the function parse_investment_file to obtain the necessary information from an investment file.
        It sets up all internal data structures and analyzes the transactions, and creates some basic data
        :param id_str: String containing the account ID
        :param type_str: String containing the type of asset
        :param purpose_str: String containing the purpose of the account
        :param currency_str: String of the account currency
        :param basecurrency_str: String of the basecurrency
        :param symbol_str: String of the investment's symbol, e.g., "AAPL"
        :param exchange_str: String of the exchange, where the investment is traded, e.g., "NASDAQ"
        :param filename_str: Filename associated with this account which info was obtained
        :param transactions_dict: Dictionary with the transactions-data, as lists for the individual keys
        :param dateformat_str: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        :param dataprovider: Object of the data provider class, e.g., dataprovider_yahoofinance
        """
        self.id = id_str
        self.type = type_str
        self.purpose = purpose_str
        self.currency = currency_str
        self.basecurrency = basecurrency_str
        self.symbol = symbol_str
        self.exchange = exchange_str
        self.filename = filename_str
        self.transactions = transactions_dict
        self.dateformat = dateformat_str
        self.analysis_data_done = False  # Analysis data is not yet prepared
        self.forex_data_given = False
        self.provider = dataprovider
        # Data not known yet:
        self.forex_obj = None
        self.analysis_dates = None
        self.analysis_balances = None
        self.analysis_prices = None
        self.analysis_values = None
        self.analysis_inflows = None
        self.analysis_outflows = None
        self.analysis_costs = None
        self.marketpricesobj = None
        self.analysis_payouts = None

        # Check, if the transaction-dates are in order. Allow identical successive days
        if dateoperations.check_date_order(self.transactions[setup.DICT_KEY_DATES], dateformat=setup.FORMAT_DATE,
                                           allow_ident_days=True) is False:
            raise RuntimeError(
                "Transaction-dates are not in temporal order (Note: Identical successive dates are allowed). "
                "Filename: " + self.filename)

        # Check, if the transactions-actions-column only contains allowed strings:
        if stringoperations.check_allowed_strings(self.transactions[setup.DICT_KEY_ACTIONS],
                                                  setup.INVSTMT_ALLOWED_ACTIONS) is False:
            raise RuntimeError("Actions-column contains faulty strings. Filename: " + self.filename)

        # Check, if the purpose-string only contains allowed purposes:
        if stringoperations.check_allowed_strings([self.purpose], cfg.ASSET_PURPOSES) is False:
            raise RuntimeError("Purpose of investment is not recognized. Filename: " + self.filename)

        # Perform sanity-checks with the transactions.
        self.transactions_sanity_check(self.transactions[setup.DICT_KEY_DATES],
                                       self.transactions[setup.DICT_KEY_ACTIONS],
                                       self.transactions[setup.DICT_KEY_QUANTITY],
                                       self.transactions[setup.DICT_KEY_PRICE],
                                       self.transactions[setup.DICT_KEY_COST],
                                       self.transactions[setup.DICT_KEY_PAYOUT],
                                       self.transactions[setup.DICT_KEY_BALANCES])

        # Check for stock splits and adjust the balances, prices accordingly
        prices_mod, balances_mod, quantities_mod = self.adjust_splits(self.transactions[setup.DICT_KEY_ACTIONS],
                                                                      self.transactions[setup.DICT_KEY_PRICE],
                                                                      self.transactions[setup.DICT_KEY_BALANCES],
                                                                      self.transactions[setup.DICT_KEY_QUANTITY])
        self.transactions[setup.DICT_KEY_PRICE] = prices_mod
        self.transactions[setup.DICT_KEY_BALANCES] = balances_mod
        self.transactions[setup.DICT_KEY_QUANTITY] = quantities_mod

        # Process the transactions, extend the dates/data etc.
        # Create a list of consecutive calendar days that corresponds to the date-range of the recorded transactions:
        self.datelist = dateoperations.create_datelist(self.get_first_transaction_date(),
                                                       self.get_last_transaction_date(), self.dateformat)

        # Interpolate the balances, such that the entries in balancelist correspond to the days in datelist.
        _, self.balancelist = dateoperations.interpolate_data(self.transactions[setup.DICT_KEY_DATES],
                                                              self.transactions[setup.DICT_KEY_BALANCES],
                                                              self.dateformat)

        # The cost and payouts does not need interpolation. Lists are populated (corresponding to datelist), that
        # contain the transactions.
        self.costlist = self.populate_full_list(self.transactions[setup.DICT_KEY_DATES],
                                                self.transactions[setup.DICT_KEY_COST],
                                                self.datelist, self.dateformat, sum_ident_days=True)
        self.payoutlist = self.populate_full_list(self.transactions[setup.DICT_KEY_DATES],
                                                  self.transactions[setup.DICT_KEY_PAYOUT],
                                                  self.datelist, self.dateformat, sum_ident_days=True)
        # This list holds the prices that are recorded with the transactions:
        # Careful: Prices may not be summed up! The last price of a given day is taken (if there are multiple transactions per day(date)
        self.pricelist = self.populate_full_list(self.transactions[setup.DICT_KEY_DATES],
                                                 self.transactions[setup.DICT_KEY_PRICE],
                                                 self.datelist, self.dateformat, sum_ident_days=False)

        # This list contains inflows into the investment (e.g., "Buy"-values). The values are in the currency of
        # the investment.
        self.inflowlist = self.get_inoutflow_value(self.transactions[setup.DICT_KEY_DATES],
                                                   self.transactions[setup.DICT_KEY_ACTIONS],
                                                   self.transactions[setup.DICT_KEY_QUANTITY],
                                                   self.transactions[setup.DICT_KEY_PRICE],
                                                   setup.STRING_INVSTMT_ACTION_BUY,
                                                   self.datelist, self.dateformat)

        # This list contains outflows of the investment (e.g., "Sell"-values). The values are in the currency of
        # the investment.
        self.outflowlist = self.get_inoutflow_value(self.transactions[setup.DICT_KEY_DATES],
                                                    self.transactions[setup.DICT_KEY_ACTIONS],
                                                    self.transactions[setup.DICT_KEY_QUANTITY],
                                                    self.transactions[setup.DICT_KEY_PRICE],
                                                    setup.STRING_INVSTMT_ACTION_SELL,
                                                    self.datelist, self.dateformat)

    def adjust_splits(self, trans_actions, trans_price, trans_balance, trans_quantity):
        """
         A split affects the price and balance
        This is needed as online data provider usually provide historical data that reflects the newest value after
        all splits. Thus, for the obtained data to match, the recorded data must be adjusted accordingly.
        The balances and prices are directly affected if a split is detected.
        Note that the dates must be in temporal order. This is checked above in the constructor, so we're good.
        :param trans_actions: List of strings of actions, e.g, "sell" or "buy" (transactions)
        :param trans_price: List of values corresponding to the price of the investment (one unit) (transactions
        :param trans_balance: List of values, corresponding to the balance of the nr. of investments/stocks
        :param trans_quantity: List of values corresponding to the sold/bought (etc.) investments (transactions)
        :return: Three lists: Prices, balances and quantities, as modified for the splits.
        """
        price_mod = [0] * len(trans_actions)
        bal_mod = [0] * len(trans_actions)
        quant_mod = [0] * len(trans_actions)
        split_factor = int(1)  # tracks the running split factor (if multiple splits). Only integer splits allowed.
        # Iterate in reverse, i.e., start with the newest transaction:
        for idx in range(len(trans_actions) - 1, -1, -1):
            # Check for a split. Note that in the split-transaction, the newest price and balance are already modified/given.
            if trans_actions[idx] == setup.STRING_INVSTMT_ACTION_SPLIT:
                if idx == 0:
                    raise RuntimeError(
                        "Seems like the first transaction is a split. This should have been caught earlier! Something is really wrong!")
                print(
                    "Split detected. Stock: " + self.symbol + ". Double-check data provided by dataprovider, if all is in order.")
                if trans_balance[idx - 1] > 1e-9:
                    r = trans_balance[idx] / trans_balance[idx - 1]
                else:
                    r = trans_quantity[
                        idx]  # If balance is 0 (e.g., all stock sold), the split ratio has to be given in the quantity column!
                if not helper.isinteger(r):
                    raise RuntimeError("Non-integer split detected!")
                else:
                    split_factor = split_factor * int(r)
                # In the split transaction, price and balance are already updated:
                price_mod[idx] = trans_price[idx]
                bal_mod[idx] = trans_balance[idx]
                quant_mod[idx] = trans_quantity[idx]
            else:  # No split detected: adjust the price, quantities (e.g., sell, buy) and balances:
                price_mod[idx] = trans_price[idx] / float(split_factor)
                bal_mod[idx] = trans_balance[idx] * float(split_factor)
                quant_mod[idx] = trans_quantity[idx] * int(split_factor)
        return price_mod, bal_mod, quant_mod

    def transactions_sanity_check(self, trans_dates, trans_actions, trans_quantity, trans_price, trans_cost,
                                  trans_payout, trans_balance):
        """Checks, if the recorded balances of the transactions are in order and match with the "sell" and "buy" entries
        :param trans_dates: List of strings of transaction-dates
        :param trans_actions: List of strings of actions, e.g, "sell" or "buy" (transactions)
        :param trans_quantity: List of values corresponding to the sold/bought (etc.) investments (transactions)
        :param trans_price: List of values corresponding to the price of the investment (one unit) (transactions)
        :param trans_cost: List of costs as recorded in the transactions
        :param trans_payout: List of payouts as recorded in the transactions
        :param trans_balance: List of values, corresponding to the balance of the nr. of investments/stocks
        :return: True, if everything in order. Otherwise, RuntimeErrors are raised.
        """
        # Sanity-check:
        totlist = [trans_dates, trans_actions, trans_quantity, trans_price, trans_cost, trans_payout, trans_balance]
        n = len(trans_dates)
        if all(len(x) == n for x in totlist) is False:
            raise RuntimeError("The transaction-lists must be of equal lenghts.")

        # First transaction must be a buy:
        if trans_actions[0] != setup.STRING_INVSTMT_ACTION_BUY:
            raise RuntimeError("First investment-transaction must be a buy.")

        # Check every transaction:
        for idx, date in enumerate(trans_dates):
            # Negative investment-balances do not make sense:
            if trans_balance[idx] < 0.0:
                raise RuntimeError("Detected a negative balance. This does not make sense. "
                                   "Transaction-Nr: " + repr(idx + 1))
            # If an investment is extended by buying more:
            if trans_actions[idx] == setup.STRING_INVSTMT_ACTION_BUY:
                if idx == 0:
                    if trans_balance[idx] != trans_quantity[idx]:
                        raise RuntimeError("Transactions not in order (balance not correct). "
                                           "Transaction-Nr: " + repr(idx + 1))
                else:
                    if helper.isclose(trans_balance[idx],
                                      (trans_balance[idx - 1] + trans_quantity[idx])) is False:
                        raise RuntimeError("Transactions not in order (balance not correct). "
                                           "Transaction-Nr: " + repr(idx + 1))
            elif trans_actions[idx] == setup.STRING_INVSTMT_ACTION_SELL:
                if idx == 0:
                    raise RuntimeError("First investment-transaction cannot be a sell.")
                else:
                    if helper.isclose(trans_balance[idx], (trans_balance[idx - 1] - trans_quantity[idx])) is False:
                        raise RuntimeError("Transactions not in order (balance not correct). "
                                           "Transaction-Nr: " + repr(idx + 1))
            elif trans_actions[idx] == setup.STRING_INVSTMT_ACTION_SPLIT:
                if idx == 0:
                    raise RuntimeError("First investment-transcation cannot be a split.")
                if trans_balance[idx - 1] > 1e-9:
                    split_ratio = trans_balance[idx] / trans_balance[idx - 1]
                else:
                    split_ratio = trans_quantity[
                        idx]  # If balance is 0 (e.g., all stock sold), the split ratio has to be given in the quantity column!
                if not helper.isinteger(split_ratio):
                    raise RuntimeError("Non-integer split detected. Transaction-Nr: " + repr(idx + 1))

                if split_ratio > 150:
                    raise RuntimeError("Split ratio > 150 detected. Sensible?!")

                if trans_price[idx] < 1e-9:
                    raise RuntimeError("The new price must be given for a split-transaction!")
            else:
                if idx > 0 and trans_balance[idx] != trans_balance[idx - 1]:
                    raise RuntimeError("Balance changed without buy/sell action.")

                if trans_quantity[idx] > 1e-9:
                    raise RuntimeError("Only sell or buy transactions may provide a quantity."
                                       "Transaction-Nr: " + repr(idx + 1))
            if trans_actions[idx] == setup.STRING_INVSTMT_ACTION_UPDATE:
                if trans_quantity[idx] > 1e-9 or trans_cost[idx] > 1e-9 or trans_payout[idx] > 1e-9:
                    raise RuntimeError("Update-actions may not have quantity, cost or payout, only price."
                                       "Transaction-Nr: " + repr(idx + 1))
        # Do some further checks:
        # Check every transaction:
        for idx, date in enumerate(trans_dates):
            if trans_actions[idx] == setup.STRING_INVSTMT_ACTION_BUY or trans_actions[idx] \
                    == setup.STRING_INVSTMT_ACTION_SELL or trans_actions[idx] == setup.STRING_INVSTMT_ACTION_SPLIT:
                if trans_payout[idx] > 1e-9:
                    raise RuntimeError("Buy, sell or split-transactions may not encode a payout. "
                                       "Transaction-Nr: " + repr(idx + 1))
            if trans_actions[idx] == setup.STRING_INVSTMT_ACTION_PAYOUT:
                if trans_quantity[idx] > 1e-9 or trans_price[idx] > 1e-9:
                    raise RuntimeError("Payout-transactions may not have quantities or prices. "
                                       "Transaction-Nr: " + repr(idx + 1))
            if trans_actions[idx] == setup.STRING_INVSTMT_ACTION_COST:
                if trans_quantity[idx] > 1e-9 or trans_price[idx] > 1e-9 or trans_payout[idx] > 1e-9:
                    raise RuntimeError("Cost-transactions may not have quantities, prices or payouts. "
                                       "Transaction-Nr: " + repr(idx + 1))
        return True

    def populate_full_list(self, trans_dates, trans_amounts, datelist, dateformat, sum_ident_days=False):
        """Populates a list of len(datelist) with amounts of certain transactions, that correspond to the dates in
        datelist and trans_dates.
        All values (trans_amounts) on a given day can be summed up and added to the list.
        This is needed for cost or interest. However, for prices, this is not desired. The last value is taken.
        This is needed for the analysis of "prices", as the prices of different transactions on the same day should
        not be summed...
        Values not covered by corresponding dates in trans_dates are set to zero.
        :param trans_dates: List of strings of transaction-dates
        :param trans_amounts: List of floats of corresponding amounts
        :param datelist: List of strings of the full date list, spanning all days between the transactions
        :param dateformat: String that specifies the format of the date-strings
        :param sum_ident_days: Bool, if True, transactions-amounts on identical days are summed. Otherwise, not.
        :return: List of transaction-values, for each date in datelist
        """
        # Sanity checks:
        if len(trans_dates) != len(trans_amounts):
            raise RuntimeError("Lists of transaction-dates, actions and amounts must be of equal length.")

        # Check, if transaction-dates are in order (they should be, it's checked when an account is generated)
        if dateoperations.check_date_order(trans_dates, dateformat, allow_ident_days=True) is False:
            raise RuntimeError("Specified transaction-date list is not in order.")

        # Check, if the datelist is consecutive:
        if dateoperations.check_dates_consecutive(datelist, dateformat) is False:
            raise RuntimeError("Specified datelist is not containing of consecutive days.")

        # Convert to datetime objects:
        datelist_dt = [stringoperations.str2datetime(x, dateformat) for x in datelist]
        trans_dates_dt = [stringoperations.str2datetime(x, dateformat) for x in trans_dates]

        value_list = []
        # Iterate through all dates and check if there are any matches with the trigger string
        for date in datelist_dt:
            # Get all indexes of the current date, if it occurs in the transaction-dates-list:
            indexes = [i for i, x in enumerate(trans_dates_dt) if x == date]
            # If no index: current date is not a transaction
            if not indexes:
                value_list.append(0.0)  # No transaction happened
            else:  # Indexes points to all transactions on the current day.
                if sum_ident_days is True:
                    # Sum all amounts of the current day:
                    sum_amounts = [trans_amounts[i] for i in indexes]
                    value_list.append(sum(sum_amounts))
                else:
                    # Do not sum, take the last value of the current day
                    v = trans_amounts[indexes[-1]]
                    value_list.append(v)
        # Homogenize to floats:
        value_list = [float(x) for x in value_list]
        return value_list

    def get_inoutflow_value(self, trans_dates, trans_actions, trans_quantity, trans_prices, action_trigger_str,
                            datelist, dateformat):
        """Determines the inflow or outflow into an investment from the transactions.
        The buy/sell transactions are selected and the corresponding value obtained (=quantity*price)
        The data is then also populated onto a full date-list, such that it corresponds to the dates in datelist
        :param trans_dates: List of strings of transaction-dates
        :param trans_actions: List of strings of actions (e.g., "Buy"
        :param trans_quantity: List of values, of bought quantities
        :param trans_prices: List of values, of a single-unit price
        :param action_trigger_str: String that encodes the desired action to be included, e.g., "Buy"
        :param datelist: List of strings of dates, the results are populated according to this list
        :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        :return: List of values, according to the dates in datelist
        """
        # Determine all inflow/outflow transactions, from the actions-string:
        trans_flow_dates = []
        trans_flow_values = []
        for idx, trans_date in enumerate(trans_dates):
            if trans_actions[idx] == action_trigger_str:
                trans_flow_dates.append(trans_date)
                trans_flow_values.append(trans_quantity[idx] * trans_prices[idx])  # The value is the quantity * price

        # If no transaction recorded: Add zero-values.
        if len(trans_flow_dates) == 0:
            trans_flow_dates.append(datelist[0])
            trans_flow_values.append(0.0)
        # Extend the lists to the full range
        values = self.populate_full_list(trans_flow_dates, trans_flow_values, datelist, dateformat, sum_ident_days=True)
        return values

    def get_values(self, trans_actions, trans_price, trans_balance, str_action_buy, str_action_sell,
                   str_action_update):
        """Calculates the value of an investment from price-data given in the transactions-data.
        Buy-, sell- and update-actions come with a price that can be used to determine the value.
        :param trans_actions: List of strings of transaction-actions
        :param trans_price: List of values, corresponding prices
        :param trans_balance: List of investment-balances (e.g., nr. of stocks)
        :param str_action_buy: String that encodes the "buy"-action
        :param str_action_sell: String that encodes the "sell"-action
        :param str_action_update: String that encodes an update-transaction
        :return: List of corresponding transaction-values
        """
        if trans_actions[0] != str_action_buy:
            raise RuntimeError("First investment transaction must be a buy. Cannot calculate investment-values.")
        # Check the individual transactions for updates in price, and update the value according to the balance.
        # If no price-updates are given, the last value is used.
        trans_value = []
        for idx, action in enumerate(trans_actions):
            if action == str_action_buy or action == str_action_sell or action == str_action_update:
                trans_value.append(trans_balance[idx] * trans_price[idx])
            else:
                trans_value.append(trans_value[-1])

        return trans_value

    def __get_format_transactions_values(self, startdate, stopdate, dateformat):
        """ From the manually recorded transactions-data, get the prices of the asset and
            pre-format it.
        """
        # Obtain the values from the transactions:
        trans_values = self.get_values(self.transactions[setup.DICT_KEY_ACTIONS],
                                       self.transactions[setup.DICT_KEY_PRICE],
                                       self.transactions[setup.DICT_KEY_BALANCES],
                                       setup.STRING_INVSTMT_ACTION_BUY,
                                       setup.STRING_INVSTMT_ACTION_SELL,
                                       setup.STRING_INVSTMT_ACTION_UPDATE)
        # Interpolate the values, such that the value-list corresponds to the datelist:
        _, vals = dateoperations.interpolate_data(self.transactions[setup.DICT_KEY_DATES],
                                                  trans_values, dateformat)
        return vals

    def set_analysis_data(self, date_start, date_stop, dateformat):
        """Re-formats the balances, cost, payouts and prices for further analysis
        Values are converted into the basecurrency.
        Market prices are obtained to determine the value of the investment.
        Data is cropped or extrapolated to fit the desired range.
        :param date_start: String of a date that designates the date where analysis starts from. Can be earlier
        than recorded data.
        :param date_stop: String of a date that designates the stop-date. Cannot be in the future.
        :param dateformat: String that specifies the format of the date-strings
        """
        print("\n" + self.symbol + ":")
        # Convert to datetime
        date_stop_dt = stringoperations.str2datetime(date_stop, dateformat)

        # Extrapolate or crop the data:
        # The balance is extrapolated with zeroes into the past, and with the last known values into the future,
        # if extrapolation is necessary.
        self.analysis_dates, self.analysis_balances = dateoperations.format_datelist(self.datelist,
                                                                                     self.balancelist,
                                                                                     date_start, date_stop,
                                                                                     dateformat,
                                                                                     zero_padding_past=True,
                                                                                     zero_padding_future=False)
        # The cost and payout-lists need zero-padding in both directions
        _, self.analysis_costs = dateoperations.format_datelist(self.datelist,
                                                                self.costlist,
                                                                date_start, date_stop,
                                                                dateformat,
                                                                zero_padding_past=True,
                                                                zero_padding_future=True)

        _, self.analysis_payouts = dateoperations.format_datelist(self.datelist,
                                                                  self.payoutlist,
                                                                  date_start, date_stop,
                                                                  dateformat,
                                                                  zero_padding_past=True,
                                                                  zero_padding_future=True)
        # The inflows and outflows also need zero-padding in both directions:
        _, self.analysis_inflows = dateoperations.format_datelist(self.datelist,
                                                                  self.inflowlist,
                                                                  date_start, date_stop,
                                                                  dateformat,
                                                                  zero_padding_past=True,
                                                                  zero_padding_future=True)
        _, self.analysis_outflows = dateoperations.format_datelist(self.datelist,
                                                                   self.outflowlist,
                                                                   date_start, date_stop,
                                                                   dateformat,
                                                                   zero_padding_past=True,
                                                                   zero_padding_future=True)
        _, self.analysis_prices = dateoperations.format_datelist(self.datelist,
                                                                 self.pricelist,
                                                                 date_start, date_stop,
                                                                 dateformat,
                                                                 zero_padding_past=True,
                                                                 zero_padding_future=True)

        # Determine the value of the investment:
        # If the investment is a security, obtain the market prices. If not, use the transaction-price to determine
        # the value
        if self.type == setup.STRING_ASSET_SECURITY:
            # The prices need only be obtained from a time period onwards, where the balance > 0:
            startidx = len(self.analysis_balances) + 1  # Needed further below, in case
            for idx, bal in enumerate(self.analysis_balances):
                if bal > 1e-9:
                    startidx = idx
                    break
            # If the balances are zero all the time (in the analysis-period)
            if startidx == len(self.analysis_balances) + 1:
                # Set the startidx equal to the stop-idx:
                indexes = [i for i, x in enumerate(self.analysis_dates) if x == date_stop]
                startidx = indexes[0]
            # Use this start-value to get the asset-prices:
            startdate_prices = self.analysis_dates[startidx]

            # Create a market-prices object; it will obtain the desired data, if possible. It uses the marketdata-folder
            # to store and update the obtained prices, for future use / offline use.
            self.marketpricesobj = prices.MarketPrices(self.symbol, self.exchange, self.currency,
                                                       setup.MARKETDATA_FOLDER,
                                                       setup.MARKETDATA_FORMAT_DATE, setup.MARKETDATA_DELIMITER,
                                                       startdate_prices, date_stop, dateformat, self.provider)

            # Asset prices during the analysis-period are available:
            if self.marketpricesobj.is_price_avail() is True:
                marketdates = self.marketpricesobj.get_price_dates()
                marketprices = self.marketpricesobj.get_price_values()
                # Sanity-checks, just to be sure:
                if dateoperations.check_dates_consecutive(marketdates, dateformat) is False:
                    raise RuntimeError("The obtained market-price-dates are not consecutive. Investment: "
                                       + self.filename)

                # The provided market-data can be incomplete. It is consecutive, but might not span the entire
                # analysis-range. We must merge it with the transactions-data and potentially extrapolate forwards and
                # backwards to get a combined, proper list of prices.
                transactions_prices = self.transactions[setup.DICT_KEY_PRICE]
                transactions_dates = self.transactions[setup.DICT_KEY_DATES]
                # Fuse the lists. Note that transactions_prices will be preferred, should market-data also be available
                # for a given date. Also: ZOH-extrapolation is used (going with ZOH into the past makes no diff, though)
                prices_merged = dateoperations.fuse_two_value_lists(self.analysis_dates, transactions_dates,
                                                                    transactions_prices, marketdates, marketprices,
                                                                    self.dateformat, zero_padding_past=True,
                                                                    zero_padding_future=False)
                # Calculate the values of the investment:
                self.analysis_values = []
                for idx, date in enumerate(self.analysis_dates):
                    # Only consider dates, where there is a balance > 0
                    if self.analysis_balances[idx] > 1e-9:
                        v = self.analysis_balances[idx] * prices_merged[idx]
                        self.analysis_values.append(v)
                    # Balance is zero: no value:
                    else:
                        self.analysis_values.append(0.0)

            # No online/marke prices are available:
            else:
                # Market prices could not be obtained, or other errors occurred.
                # Fallback: obtain prices from transactions-data
                # print("WARNING: Could not obtain any prices for " + self.symbol + " traded at " + self.exchange +
                #      ". Investment-File: " + self.filename)
                print("Deriving prices from transactions-data.")
                trans_values_interp = self.__get_format_transactions_values(date_start, date_stop, dateformat)
                # Crop the values to the desired analysis-range; in this case, we can not merge data with market-prices:
                _, self.analysis_values = dateoperations.format_datelist(self.datelist,
                                                                         trans_values_interp,
                                                                         date_start, date_stop,
                                                                         dateformat,
                                                                         zero_padding_past=True,
                                                                         zero_padding_future=False)

        # Investment is not a security: Derive value from given transaction-prices
        else:
            # print("Investment in file " + self.filename + " cannot obtain prices.")
            print(
                "Investment is not listed as security. Deriving prices from transactions-data. File: " + self.filename)
            trans_values_interp = self.__get_format_transactions_values(date_start, date_stop, dateformat)
            # Crop the values to the desired analysis-range; in this case, we can not merge data with market-prices:
            _, self.analysis_values = dateoperations.format_datelist(self.datelist,
                                                                     trans_values_interp,
                                                                     date_start, date_stop,
                                                                     self.dateformat,
                                                                     zero_padding_past=True,
                                                                     zero_padding_future=False)
        # Sanity check:
        if len(self.analysis_dates) != len(self.analysis_values):
            raise RuntimeError("The analysis-values are not as long as the analysis dates.")

        # The value of the investment is now known. Calculate the value in the basecurrency, if applicable:
        # Check, if a forex-object is given (only required if the account holds foreign currencies)
        if self.currency != self.basecurrency and self.forex_data_given is False:
            raise RuntimeError("Investment is in a foreign currency. Forex-object is required. "
                               "Investment-currency is: " + self.currency + ". Basecurrency is: " + self.basecurrency +
                               ". Investment-file is: " + self.filename)

        # Forex conversion required:
        elif self.currency != self.basecurrency and self.forex_data_given is True:
            # Convert the recorded values, cost and payouts:
            self.analysis_values = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_values)
            self.analysis_payouts = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_payouts)
            self.analysis_inflows = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_inflows)
            self.analysis_outflows = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_outflows)
            self.analysis_costs = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_costs)

        self.analysis_data_done = True

    def get_trans_datelist(self):
        """Return the list of transaction-dates (as strings)"""
        return list(self.datelist)

    def get_trans_balancelist(self):
        """Return the list of transaction-balances (as floats)"""
        return list(self.balancelist)

    def get_trans_costlist(self):
        """Return the list of recorded transactions-costs (as floats)"""
        return list(self.costlist)

    def get_trans_payoutlist(self):
        """Return the list of transactions-payouts (as floats)"""
        return list(self.payoutlist)

    def get_trans_pricelist(self):
        """Return the list of transaction-prices (as floats)"""
        return list(self.pricelist)

    def get_trans_inflowlist(self):
        """Return the list of transaction-inflows (as floats)"""
        return list(self.inflowlist)

    def get_trans_outflowlist(self):
        """Return the list of transaction-outflows (as floats):"""
        return list(self.outflowlist)

    def get_forex_obj(self):
        """Return the forex-object"""
        return self.forex_obj

    def get_purpose(self):
        """Return the purpose of the investment (as string)"""
        return self.purpose

    def get_type(self):
        """Return the type of the investment (as string)"""
        return self.type

    def write_forex_obj(self, forex_obj):
        """Stores a forex-object with this class, for currency conversions.
        :param forex_obj: The ForexRates-object
        """
        # Only required, if the investment is in a foreign currency:
        if self.currency != self.basecurrency:
            if forex_obj.get_currency() != self.currency or forex_obj.get_basecurrency() != self.basecurrency:
                raise RuntimeError("Currencies of forex-object do not match the investment.")
            self.forex_obj = forex_obj
            self.forex_data_given = True

    def get_first_transaction_date(self):
        """Returns the date (as string) of the first recorded transaction of the account"""
        return self.transactions[setup.DICT_KEY_DATES][0]

    def get_last_transaction_date(self):
        """Returns the date (as string) of the last recorded transaction of the account"""
        return self.transactions[setup.DICT_KEY_DATES][-1]

    def get_filename(self):
        """Return the filename of the associated investment-file (as string)"""
        return self.filename

    def get_currency(self):
        """Return the currency of the investment (as string)"""
        return self.currency

    def get_basecurrency(self):
        """Return the stored basecurrency (as string)"""
        return self.basecurrency

    def get_symbol(self):
        """Return the symbol of the investment (ticker symbol, as string)"""
        return self.symbol

    def get_exchange(self):
        """Return the stock exchange, where the investment is traded (as string)"""
        return self.exchange

    def get_analysis_datelist(self):
        """Return the list of dates of the analysis-data (dates as strings)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis datelist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_dates)

    def get_analysis_valuelist(self):
        """Return the list of values of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis valuelist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_values)

    def get_analysis_costlist(self):
        """Return the list of costs of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis costlist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_costs)

    def get_analysis_payoutlist(self):
        """Return the list of payouts of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis payoutlist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_payouts)

    def get_analysis_inflowlist(self):
        """Return the list of inflows of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis inflowlist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_inflows)

    def get_analysis_outflowlist(self):
        """Return the list of outflows of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError("Cannot return analysis outflowlist. Set analysis data first. Account ID: " + self.id)
        else:
            return list(self.analysis_outflows)

    def get_marketprice_obj(self):
        """Return the marketprices-object"""
        return self.marketpricesobj

    def get_dateformat(self):
        """Return the dateformat"""
        return self.dateformat

    def is_investment(self):
        """Returns True, if the object is an Investment"""
        return True
