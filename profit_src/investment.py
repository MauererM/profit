"""Implements a class that stores data associated with investments

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import logging
from . import dateoperations
from . import stringoperations
from . import helper
from .timedomaindata import StockTimeDomainData
from . import files


class Investment:
    """Implements an investment. Parses transactions, provides analysis-data, performs currency conversions"""

    def __init__(self, investment_dict, filename, transactions_dict, dataprovider, analyzer, storage, parsing_config,
                 profit_config):
        """Investment constructor
        Use the function parse_investment_file to obtain the necessary information from an investment file.
        It sets up all internal data structures and analyzes the transactions, and creates some basic data
        :param investment_dict: The metadata-dict from parsing
        :param filename: File-path associated with this investment
        :param transactions_dict: Dictionary with the transactions-data, as lists for the individual keys, from parsing
        :param dataprovider: Object of the data provider class
        :param analyzer: The analyzer object (for caching)
        :param storage: The storage-object that manages the stored market data
        :param parsing_config: The configuration-instance of the parsing configuration
        :param profit_config: The main config-class/instance of PROFIT
        """
        self.config = parsing_config
        self.profit_conf = profit_config
        self.id = investment_dict[self.config.STRING_ID]
        self.type = investment_dict[self.config.STRING_TYPE]
        self.purpose = investment_dict[self.config.STRING_PURPOSE]
        self.currency = investment_dict[self.config.STRING_CURRENCY]
        self.symbol = investment_dict[self.config.STRING_SYMBOL]
        self.exchange = investment_dict[self.config.STRING_EXCHANGE]
        self.basecurrency = profit_config.BASECURRENCY
        self.filename = filename
        self.transactions = transactions_dict
        self.analyzer = analyzer
        self.dateformat = self.analyzer.get_dateformat()
        self.provider = dataprovider
        self.storage = storage
        self.assetpurposes = profit_config.ASSET_PURPOSES
        self.interactive_mode = profit_config.INTERACTIVE_MODE
        # Data not known yet:
        self.analysis_data_done = False  # Analysis data is not yet prepared
        self.forex_data_given = False
        self.forex_obj = None
        self.analysis_dates = None
        self.analysis_balances = None
        self.analysis_values = None
        self.analysis_inflows = None
        self.analysis_outflows = None
        self.analysis_costs = None
        self.analysis_payouts = None
        self.latestpricedata = None
        self.has_nonzero_balance_today = None

        # Check, if the transaction-dates are in order. Allow identical successive days
        if dateoperations.check_date_order(self.transactions[self.config.DICT_KEY_DATES], self.analyzer,
                                           allow_ident_days=True) is False:
            raise RuntimeError(f"Transaction-dates are not in temporal order "
                               f"(Note: Identical successive dates are allowed). Filename: {self.filename}")

        # Check, if the purpose-string only contains allowed purposes:
        if stringoperations.check_allowed_strings([self.purpose], self.assetpurposes) is False:
            raise RuntimeError(f"Purpose of investment is not recognized. Filename: {self.filename}")

        # Perform sanity-checks with the transactions.
        self.__transactions_sanity_check(self.transactions[self.config.DICT_KEY_DATES],
                                         self.transactions[self.config.DICT_KEY_ACTIONS],
                                         self.transactions[self.config.DICT_KEY_QUANTITY],
                                         self.transactions[self.config.DICT_KEY_PRICE],
                                         self.transactions[self.config.DICT_KEY_COST],
                                         self.transactions[self.config.DICT_KEY_PAYOUT],
                                         self.transactions[self.config.DICT_KEY_BALANCES])

        # Check for stock splits and adjust the balances, prices accordingly
        prices_mod, balances_mod, quantities_mod = self.__adjust_splits(self.transactions[self.config.DICT_KEY_ACTIONS],
                                                                        self.transactions[self.config.DICT_KEY_PRICE],
                                                                        self.transactions[
                                                                            self.config.DICT_KEY_BALANCES],
                                                                        self.transactions[
                                                                            self.config.DICT_KEY_QUANTITY])
        self.transactions[self.config.DICT_KEY_PRICE] = prices_mod
        self.transactions[self.config.DICT_KEY_BALANCES] = balances_mod
        self.transactions[self.config.DICT_KEY_QUANTITY] = quantities_mod

        # Process the transactions, extend the dates/data etc.
        # Create a list of consecutive calendar days that corresponds to the date-range of the recorded transactions:
        self.datelist = dateoperations.create_datelist(self.get_first_transaction_date(),
                                                       self.get_last_transaction_date(), self.analyzer)

        # Interpolate the balances, such that the entries in balancelist correspond to the days in datelist.
        _, self.balancelist = dateoperations.interpolate_data(self.transactions[self.config.DICT_KEY_DATES],
                                                              self.transactions[self.config.DICT_KEY_BALANCES],
                                                              self.analyzer)
        if self.balancelist[-1] < 1e-9:
            self.has_nonzero_balance_today = False
        else:
            self.has_nonzero_balance_today = True

        # The cost and payouts does not need interpolation. Lists are populated (corresponding to datelist), that
        # contain the transactions.
        self.costlist = self.__populate_full_list(self.transactions[self.config.DICT_KEY_DATES],
                                                  self.transactions[self.config.DICT_KEY_COST],
                                                  self.datelist, sum_ident_days=True)
        self.payoutlist = self.__populate_full_list(self.transactions[self.config.DICT_KEY_DATES],
                                                    self.transactions[self.config.DICT_KEY_PAYOUT],
                                                    self.datelist, sum_ident_days=True)
        # This list holds the prices that are recorded with the transactions:
        # Careful: Prices may not be summed up! The last price of a given day is taken
        # (if there are multiple transactions per day(date)
        self.pricelist = self.__populate_full_list(self.transactions[self.config.DICT_KEY_DATES],
                                                   self.transactions[self.config.DICT_KEY_PRICE],
                                                   self.datelist, sum_ident_days=False)

        # This list contains inflows into the investment (e.g., "Buy"-values). The values are in the currency of
        # the investment.
        self.inflowlist = self.__get_inoutflow_value(self.transactions[self.config.DICT_KEY_DATES],
                                                     self.transactions[self.config.DICT_KEY_ACTIONS],
                                                     self.transactions[self.config.DICT_KEY_QUANTITY],
                                                     self.transactions[self.config.DICT_KEY_PRICE],
                                                     self.config.STRING_INVSTMT_ACTION_BUY,
                                                     self.datelist)

        # This list contains outflows of the investment (e.g., "Sell"-values). The values are in the currency of
        # the investment.
        self.outflowlist = self.__get_inoutflow_value(self.transactions[self.config.DICT_KEY_DATES],
                                                      self.transactions[self.config.DICT_KEY_ACTIONS],
                                                      self.transactions[self.config.DICT_KEY_QUANTITY],
                                                      self.transactions[self.config.DICT_KEY_PRICE],
                                                      self.config.STRING_INVSTMT_ACTION_SELL,
                                                      self.datelist)

    def __adjust_splits(self, trans_actions, trans_price, trans_balance, trans_quantity):
        """A split affects the price and balance.
        This is needed as online data provider usually provide historical data that reflects the newest value after
        all splits. Thus, for the obtained data to match, the recorded data must be adjusted accordingly.
        The balances and prices are directly affected if a split is detected.
        Note that the dates must be in temporal order. This is checked above in the constructor, so we're good.
        Reverse splits are also possible.
        :param trans_actions: List of strings of actions, e.g, "sell" or "buy" (transactions)
        :param trans_price: List of values corresponding to the price of the investment (one unit) (transactions
        :param trans_balance: List of values, corresponding to the balance of the nr. of investments/stocks
        :param trans_quantity: List of values corresponding to the sold/bought (etc.) investments (transactions)
        :return: Three lists: Prices, balances and quantities, as modified for the splits.
        """
        price_mod = [0] * len(trans_actions)
        bal_mod = [0] * len(trans_actions)
        quant_mod = [0] * len(trans_actions)
        split_factor = 1.0  # tracks the running split factor (if multiple splits). Floats are allowed (reverse splits)
        # Iterate in reverse, i.e., start with the newest transaction:
        for idx in range(len(trans_actions) - 1, -1, -1):
            # Check for a split.
            # Note that in the split-transaction, the newest price and balance are already modified/given.
            if trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_SPLIT:
                if idx == 0:
                    raise RuntimeError("The first transaction is a split?! This should have been caught earlier!")
                logging.warning(f"Split detected. Stock: {self.symbol}. Double-check that data from dataprovider "
                                f"reflects this correctly.")
                if trans_balance[idx - 1] > 1e-9:  # Derive the ratio from the provided balance-entry
                    r = trans_balance[idx] / trans_balance[idx - 1]
                else:  # Balance is 0 (i.e., all stock sold): Derive ratio from the quantity-column
                    r = trans_quantity[idx]
                split_factor = split_factor * r
                # In the split transaction, price and balance are already updated:
                price_mod[idx] = trans_price[idx]
                bal_mod[idx] = trans_balance[idx]
                quant_mod[idx] = trans_quantity[idx]
            else:  # No split detected: adjust the price, quantities (e.g., sell, buy) and balances:
                price_mod[idx] = trans_price[idx] / float(split_factor)
                bal_mod[idx] = trans_balance[idx] * float(split_factor)
                quant_mod[idx] = trans_quantity[idx] * float(split_factor)
        return price_mod, bal_mod, quant_mod

    def __transactions_sanity_check(self, trans_dates, trans_actions, trans_quantity, trans_price, trans_cost,
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
        if trans_actions[0] != self.config.STRING_INVSTMT_ACTION_BUY:
            raise RuntimeError("First investment-transaction must be a buy.")

        # Check every transaction:
        for idx, _ in enumerate(trans_dates):
            # Negative investment-balances do not make sense:
            if trans_balance[idx] < 0.0:
                raise RuntimeError(f"Detected a negative balance. This does not make sense. "
                                   f"Transaction-Nr: {(idx + 1):d}")
            # If an investment is extended by buying more:
            if trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_BUY:
                if idx == 0:
                    if trans_balance[idx] != trans_quantity[idx]:
                        raise RuntimeError(f"Transactions not in order (balance or quantity not correct). "
                                           f"Transaction-Nr: {(idx + 1):d}")
                else:
                    if helper.isclose(trans_balance[idx],
                                      (trans_balance[idx - 1] + trans_quantity[idx])) is False:
                        raise RuntimeError(f"Transactions not in order (balance or quantity not correct). "
                                           f"Transaction-Nr: {(idx + 1):d}")
            elif trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_SELL:
                if idx == 0:
                    raise RuntimeError("First investment-transaction cannot be a sell.")
                if helper.isclose(trans_balance[idx], (trans_balance[idx - 1] - trans_quantity[idx])) is False:
                    raise RuntimeError(f"Transactions not in order (balance not correct). "
                                       f"Transaction-Nr: {(idx + 1):d}")
            elif trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_SPLIT:
                if idx == 0:
                    raise RuntimeError("First investment-transcation cannot be a split.")
                if trans_balance[idx - 1] > 1e-9:
                    split_ratio = trans_balance[idx] / trans_balance[idx - 1]
                else:  # If balance is 0 (e.g., all stock sold), the split ratio has to be given in the quantity column!
                    split_ratio = trans_quantity[idx]

                if split_ratio > 150:
                    logging.warning("Split ratio > 150 detected. Sensible?")

                if split_ratio < 1.0 / 150:
                    logging.warning("Split ratio < 1/150 detected. Sensible?")

                if trans_price[idx] < 1e-9:
                    raise RuntimeError("The new price must be given for a split-transaction!")
            else:
                if idx > 0 and trans_balance[idx] != trans_balance[idx - 1]:
                    raise RuntimeError("Balance changed without buy/sell action.")

                if trans_quantity[idx] > 1e-9:
                    raise RuntimeError(f"Only sell or buy transactions may provide a quantity."
                                       f"Transaction-Nr: {(idx + 1):d}")
            if trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_UPDATE:
                if trans_quantity[idx] > 1e-9 or trans_cost[idx] > 1e-9 or trans_payout[idx] > 1e-9:
                    raise RuntimeError(f"Update-actions may not have quantity, cost or payout, only price."
                                       f"Transaction-Nr: {(idx + 1):d}")
        # Do some further checks:
        # Check every transaction:
        for idx, _ in enumerate(trans_dates):
            if trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_BUY or \
                    trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_SELL or \
                    trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_SPLIT:
                if trans_payout[idx] > 1e-9:
                    raise RuntimeError(f"Buy, sell or split-transactions may not encode a payout. "
                                       f"Transaction-Nr: {(idx + 1):d}")
            if trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_PAYOUT:
                if trans_quantity[idx] > 1e-9 or trans_price[idx] > 1e-9:
                    raise RuntimeError(f"Payout-transactions may not have quantities or prices. "
                                       f"Transaction-Nr: {(idx + 1):d}")
            if trans_actions[idx] == self.config.STRING_INVSTMT_ACTION_COST:
                if trans_quantity[idx] > 1e-9 or trans_price[idx] > 1e-9 or trans_payout[idx] > 1e-9:
                    raise RuntimeError(f"Cost-transactions may not have quantities, prices or payouts. "
                                       f"Transaction-Nr: {(idx + 1):d}")

        # Check, if there are multiple transactions on the same date; This is in some cases (sadly) not allowed,
        # due to the 1-day assumed minimal granularity of PROFIT.
        duplicates = sorted(helper.find_duplicate_indices(trans_dates))
        if not duplicates:
            return True
        sequences = helper.extract_sequences(duplicates)
        for sequence in sequences:
            if len(sequence) < 2:
                raise RuntimeError("Something went wrong in calculating duplicates; "
                                   "There should always be a duplicate at this point")
            actions = trans_actions[sequence[0]:sequence[-1] + 1]
            if (self.config.STRING_INVSTMT_ACTION_BUY in actions and
                self.config.STRING_INVSTMT_ACTION_SELL in actions) or \
                    (self.config.STRING_INVSTMT_ACTION_BUY in actions and
                     self.config.STRING_INVSTMT_ACTION_SPLIT in actions) or \
                    (self.config.STRING_INVSTMT_ACTION_SELL in actions and
                     self.config.STRING_INVSTMT_ACTION_SPLIT in actions):
                raise RuntimeError(
                    "In PROFIT, it is (sadly) not allowed to have Buy, or Sell, or Split "
                    "transactions on the same date.")

        return True

    def __populate_full_list(self, trans_dates, trans_amounts, datelist, sum_ident_days=False):
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
        :param sum_ident_days: Bool, if True, transactions-amounts on identical days are summed. Otherwise, not.
        :return: List of transaction-values, for each date in datelist
        """
        # Sanity checks:
        if len(trans_dates) != len(trans_amounts):
            raise RuntimeError("Lists of transaction-dates, actions and amounts must be of equal length.")

        # Check, if the datelist is consecutive (this also checks that the dates are in order):
        if dateoperations.check_dates_consecutive(datelist, self.analyzer) is False:
            raise RuntimeError("Specified datelist is not made of consecutive days.")

        value_list = [0] * len(datelist)

        # Create a dictionary of the full datelist for faster indexing
        datelist_dict = {date: idx for idx, date in enumerate(datelist)}

        trans_dates_unique = list(dict.fromkeys(trans_dates))  # Maintain the order

        for trans_date in trans_dates_unique:
            idx_global = datelist_dict[trans_date]
            indexes = [i for i, date in enumerate(trans_dates) if date == trans_date]
            if sum_ident_days is True:
                # Sum all amounts of the current day:
                sum_amounts = [trans_amounts[i] for i in indexes]
                value_list[idx_global] = sum(sum_amounts)
            else:
                value_list[idx_global] = trans_amounts[indexes[-1]]

        # Homogenize to floats:
        value_list = [float(x) for x in value_list]
        return value_list

    def __get_inoutflow_value(self, trans_dates, trans_actions, trans_quantity, trans_prices, action_trigger_str,
                              datelist):
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
        values = self.__populate_full_list(trans_flow_dates, trans_flow_values, datelist, sum_ident_days=True)
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
        valid_actions = {str_action_buy, str_action_sell, str_action_update}
        for idx, action in enumerate(trans_actions):
            if action in valid_actions:
                trans_value.append(trans_balance[idx] * trans_price[idx])
            else:
                trans_value.append(trans_value[-1])

        return trans_value

    def __get_format_transactions_values(self):
        """ From the manually recorded transactions-data, get the prices of the asset and
            pre-format it.
        """
        # Obtain the values from the transactions:
        trans_values = self.get_values(self.transactions[self.config.DICT_KEY_ACTIONS],
                                       self.transactions[self.config.DICT_KEY_PRICE],
                                       self.transactions[self.config.DICT_KEY_BALANCES],
                                       self.config.STRING_INVSTMT_ACTION_BUY,
                                       self.config.STRING_INVSTMT_ACTION_SELL,
                                       self.config.STRING_INVSTMT_ACTION_UPDATE)
        # Interpolate the values, such that the value-list corresponds to the datelist:
        _, vals = dateoperations.interpolate_data(self.transactions[self.config.DICT_KEY_DATES],
                                                  trans_values, self.analyzer)
        return vals

    def set_analysis_data(self, date_start, date_stop):
        """Re-formats the balances, cost, payouts and prices for further analysis
        Values are converted into the basecurrency.
        Market prices are obtained to determine the value of the investment.
        Data is cropped or extrapolated to fit the desired range.
        :param date_start: String of a date that designates the date where analysis starts from. Can be earlier
        than recorded data.
        :param date_stop: String of a date that designates the stop-date. Cannot be in the future.
        """
        print(
            f"\n{self.symbol} ({self.filename.name}):")  # Show in the terminal what's going on/which investment is getting processed

        # Extrapolate or crop the data:
        # The balance is extrapolated with zeroes into the past, and with the last known values into the future,
        # if extrapolation is necessary.
        self.analysis_dates, self.analysis_balances = dateoperations.format_datelist(self.datelist,
                                                                                     self.balancelist,
                                                                                     date_start, date_stop,
                                                                                     self.analyzer,
                                                                                     zero_padding_past=True,
                                                                                     zero_padding_future=False)
        # The cost and payout-lists need zero-padding in both directions
        _, self.analysis_costs = dateoperations.format_datelist(self.datelist,
                                                                self.costlist,
                                                                date_start, date_stop,
                                                                self.analyzer,
                                                                zero_padding_past=True,
                                                                zero_padding_future=True)

        _, self.analysis_payouts = dateoperations.format_datelist(self.datelist,
                                                                  self.payoutlist,
                                                                  date_start, date_stop,
                                                                  self.analyzer,
                                                                  zero_padding_past=True,
                                                                  zero_padding_future=True)
        # The inflows and outflows also need zero-padding in both directions:
        _, self.analysis_inflows = dateoperations.format_datelist(self.datelist,
                                                                  self.inflowlist,
                                                                  date_start, date_stop,
                                                                  self.analyzer,
                                                                  zero_padding_past=True,
                                                                  zero_padding_future=True)
        _, self.analysis_outflows = dateoperations.format_datelist(self.datelist,
                                                                   self.outflowlist,
                                                                   date_start, date_stop,
                                                                   self.analyzer,
                                                                   zero_padding_past=True,
                                                                   zero_padding_future=True)

        # Determine the value of the investment:
        # If the investment is a security, obtain the market prices. If not, use the transaction-price to determine
        # the value
        if self.type == self.config.STRING_ASSET_SECURITY:
            # The prices need only be obtained from a time period onwards, where the balance > 0:
            startidx = next((idx for idx, val in enumerate(self.analysis_balances) if val > 1e-9), None)
            # If the balances are zero all the time (in the analysis-period)
            if startidx is None:
                # Set the startidx equal to the stop-idx:
                indexes = [i for i, x in enumerate(self.analysis_dates) if x == date_stop]
                startidx = indexes[0]
            # Use this start-value to get the asset-prices:
            startdate_prices = self.analysis_dates[startidx]
            startdate_analysis_dt = self.analyzer.str2datetime(startdate_prices)
            stopdate_analysis_dt = self.analyzer.str2datetime(date_stop)
            if startdate_analysis_dt > stopdate_analysis_dt:
                raise RuntimeError(f"Startdate cannot be after stopdate. Symbol: {self.symbol}. "
                                   f"Exchange: {self.exchange}")

            # Check if data is available from storage and/or obtain data via data provider:
            stockdata = StockTimeDomainData(self.symbol, self.exchange, self.currency, (startdate_prices, date_stop),
                                            self.analyzer, self.storage, self.provider, self.has_nonzero_balance_today,
                                            self.profit_conf)
            full_dates, full_prices = stockdata.get_price_data()

            if full_dates is not None:
                # The provided market-data can be incomplete. It is consecutive, but might not span the entire
                # analysis-range. We must merge it with the transactions-data and potentially extrapolate forwards and
                # backwards to get a combined, proper list of prices.
                transactions_prices = self.transactions[self.config.DICT_KEY_PRICE]
                transactions_dates = self.transactions[self.config.DICT_KEY_DATES]
                # Fuse the lists. Note that transactions_prices will be preferred, should market-data also be available
                # for a given date. Also: ZOH-extrapolation is used (going with ZOH into the past makes no diff, though)
                # The transactions-data also contains zero-values for price. Ignore those (discard_zeroes=True)
                prices_merged = dateoperations.fuse_two_value_lists(self.analysis_dates, transactions_dates,
                                                                    transactions_prices, full_dates, full_prices,
                                                                    self.analyzer,
                                                                    zero_padding_past=True,
                                                                    zero_padding_future=False,
                                                                    discard_zeroes=True)

                # Perform a sanity-check to see if the transactions-recorded and obtained prices do not
                # significantly deviate:
                marketdates_dict = {date: i for i, date in enumerate(full_dates)}
                mismatches = []
                for idx, date in enumerate(transactions_dates):
                    if date in marketdates_dict:
                        record = transactions_prices[idx]
                        data = full_prices[marketdates_dict[date]]
                        if record > 1e-6 and helper.within_tol(record, data, 5.0 / 100) is False:
                            mismatches.append((date, record, data))
                if len(mismatches) > 0:
                    logging.warning("Some obtained or stored prices deviate by >5% from the recorded transactions:")
                    print("Date;\t\t\tRecorded Price;\tObtained Price")
                    for i, entry in enumerate(mismatches):
                        print(f"{entry[0]};\t\t{entry[1]:.2f};\t\t\t{entry[2]:.2f};")
                    print("Could a split cause this? Potentially adjust via the split-option in the header "
                          "in the storage-csv file. Transaction-data is ground-truth.")

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

                # Store the latest available price and date, for the holding-period return analysis
                self.latestpricedata = (full_dates[-1], full_prices[-1])

                # Check if a) the investment has a balance today, and b) if there is a price for today (which has
                # not been extrapolated forward).
                # Depending on this, execute interactive mode or not.
                date_today_dt = dateoperations.get_date_today(self.dateformat, datetime_obj=True)
                latest_date_transactions = self.analyzer.str2datetime(transactions_dates[-1])
                latest_date_full = self.analyzer.str2datetime(full_dates[-1])
                latest_date = max(latest_date_full, latest_date_transactions)
                if self.has_nonzero_balance_today is True and latest_date < date_today_dt:
                    if self.__handle_interactive_mode() is False:
                        return False

            elif full_dates is None:  # Transactions-data needed!
                # Check how recent the transactions-data is:
                transactions_dates = self.transactions[self.config.DICT_KEY_DATES]
                last_transaction_date_dt = self.analyzer.str2datetime(transactions_dates[-1])
                date_today_dt = dateoperations.get_date_today(self.dateformat, datetime_obj=True)
                # We have holdings today, but no price of today.
                if self.has_nonzero_balance_today is True and last_transaction_date_dt < date_today_dt:
                    if self.__handle_interactive_mode() is False:
                        return False
                if last_transaction_date_dt < date_today_dt:
                    logging.warning(f"No financial data available for {self.symbol}.")
                    logging.warning("Provide an update-transaction to deliver the most recent price of the asset. "
                                    "\nOtherwise, the holding period returns cannot be calculated. Consider using the "
                                    "interactive mode to provide the data quickly.")
                else:
                    logging.info("Deriving prices (purely) from transactions-data, which is available for today.")

                trans_values_interp = self.__get_format_transactions_values()
                # Crop the values to the desired analysis-range; in this case, we can not merge data with market-prices:
                _, self.analysis_values = dateoperations.format_datelist(self.datelist,
                                                                         trans_values_interp,
                                                                         date_start, date_stop,
                                                                         self.analyzer,
                                                                         zero_padding_past=True,
                                                                         zero_padding_future=False)

        # Investment is not a security: Derive value from given transaction-prices
        else:
            # Check how recent the transactions-data is:
            transactions_dates = self.transactions[self.config.DICT_KEY_DATES]
            last_transaction_date_dt = self.analyzer.str2datetime(transactions_dates[-1])
            date_today_dt = dateoperations.get_date_today(self.dateformat, datetime_obj=True)
            # We have holdings today, but no price of today.
            if self.has_nonzero_balance_today is True and last_transaction_date_dt < date_today_dt:
                if self.__handle_interactive_mode() is False:
                    return False
            print(f"Investment is not listed as security. Deriving prices from transactions-data. "
                  f"File: {self.filename}")
            trans_values_interp = self.__get_format_transactions_values()

            # Crop the values to the desired analysis-range; in this case, we can not merge data with market-prices:
            _, self.analysis_values = dateoperations.format_datelist(self.datelist,
                                                                     trans_values_interp,
                                                                     date_start, date_stop,
                                                                     self.analyzer,
                                                                     zero_padding_past=True,
                                                                     zero_padding_future=False)
        # We now have the value of the investment calculated.
        # Sanity check:
        if len(self.analysis_dates) != len(self.analysis_values):
            raise RuntimeError("The analysis-values are not as long as the analysis dates.")

        # The value of the investment is now known. Calculate the value in the basecurrency, if applicable:
        # Check, if a forex-object is given (only required if the account holds foreign currencies)
        if self.currency != self.basecurrency and self.forex_data_given is False:
            raise RuntimeError(f"Investment is in a foreign currency. Forex-object is required. "
                               f"Investment-currency is: {self.currency}. Basecurrency is: {self.basecurrency}."
                               f"Investment-file is: {self.filename}")

        # Forex conversion required:
        if self.currency != self.basecurrency and self.forex_data_given is True:
            # Convert the recorded values, cost and payouts:
            self.analysis_values = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_values)
            self.analysis_payouts = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_payouts)
            self.analysis_inflows = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_inflows)
            self.analysis_outflows = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_outflows)
            self.analysis_costs = self.forex_obj.perform_conversion(self.analysis_dates, self.analysis_costs)

        self.analysis_data_done = True
        return True

    def __handle_interactive_mode(self):
        """Returns True if no interactions have happened. Returns False if the user has provided new data"""
        if self.interactive_mode is False:
            return True
        ret = self.__ask_user_for_update_transaction()
        if ret is None:
            return True
        self.__append_file_with_newest_price(ret)
        return False  # Changes have been made to the investment-file.

    def __append_file_with_newest_price(self, price):
        """The user wants to update the file with a new balance.
        Craft the newest transaction-string, write it to file, and update all data within this instance accordingly.
        """
        date_today = dateoperations.get_date_today(self.dateformat)
        action = self.config.STRING_ACCOUNT_ACTION_UPDATE
        quantity = "0"
        price = f"{price:.2f}"
        cost = "0"
        payout = "0"
        balance = self.transactions[self.config.DICT_KEY_BALANCES][-1]
        balance = f"{balance:.4f}"
        note = ""
        strings = [date_today, action, quantity, price, cost, payout, balance, note]
        # Write the data to file:
        files.append_transaction_line_to_file(self.filename, strings, self.config.STRING_EOF, self.profit_conf)

    def __ask_user_for_update_transaction(self):
        """Ask the user to provide the most recent end-of-day price for the asset/investment.
        Sanitize the input, and return the newest value/price.
        """
        user_input = input(f"A manually updated price is needed. Provide the most recent end-of-day price "
                           f"(in {self.currency}) or press enter to skip: ")
        if user_input == "":
            return None
        if helper.is_valid_float(user_input) is False:
            print("Received an invalid number. Please re-try.")
            return self.__ask_user_for_update_transaction()
        try:
            return float(user_input)
        except ValueError:
            raise RuntimeError("Could not convert the float. Is the float-checking-function not working?")

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
        return self.transactions[self.config.DICT_KEY_DATES][0]

    def get_last_transaction_date(self):
        """Returns the date (as string) of the last recorded transaction of the account"""
        return self.transactions[self.config.DICT_KEY_DATES][-1]

    def get_filename(self):
        """Return the filename of the associated investment-file (as string)"""
        return self.filename.name

    def get_filepath(self):
        return self.filename

    def get_currency(self):
        """Return the currency of the investment (as string)"""
        return self.currency

    def get_basecurrency(self):
        """Return the stored basecurrency (as string)"""
        return self.basecurrency

    def get_analysis_datelist(self):
        """Return the list of dates of the analysis-data (dates as strings)"""
        if self.analysis_data_done is False:
            raise RuntimeError(f"Cannot return analysis datelist. Set analysis data first. ID: {self.id}")
        return self.analysis_dates

    def get_analysis_valuelist(self):
        """Return the list of values of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError(f"Cannot return analysis valuelist. Set analysis data first. ID: {self.id}")
        return self.analysis_values

    def get_analysis_costlist(self):
        """Return the list of costs of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError(f"Cannot return analysis costlist. Set analysis data first. ID: {self.id}")
        return self.analysis_costs

    def get_analysis_payoutlist(self):
        """Return the list of payouts of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError(f"Cannot return analysis payoutlist. Set analysis data first. ID: {self.id}")
        return self.analysis_payouts

    def get_analysis_inflowlist(self):
        """Return the list of inflows of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError(f"Cannot return analysis inflowlist. Set analysis data first. ID: {self.id}")
        return self.analysis_inflows

    def get_analysis_outflowlist(self):
        """Return the list of outflows of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError(f"Cannot return analysis outflowlist. Set analysis data first. ID: {self.id}")
        return self.analysis_outflows

    def get_analysis_balances(self):
        """Return the list of balances of the analysis-data (floats)"""
        if self.analysis_data_done is False:
            raise RuntimeError(f"Cannot return analysis balance list. Set analysis data first. ID: {self.id}")
        return self.analysis_balances

    def get_dateformat(self):
        """Return the dateformat"""
        return self.dateformat

    def get_latest_price_date(self):
        """Returns the latest available price and date, that has not been extrapolated.
        For the calculation of the holding period return.
        :return: Tuple of date and value
        """
        return self.latestpricedata
