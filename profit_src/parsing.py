"""Implements classes and configurations for parsing account- and investment files.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

from . import stringoperations
from . import files
from . import account
from . import investment
from . import helper
from . import dateoperations


def read_strip_file_lines(fpath):
    """Reads all lines froma file and strips all white spaces.
    :param fpath: Path-object of the file to be read
    :return: List of lines, as strings
    """
    try:
        lines = files.get_file_lines(fpath)
        lines = [stringoperations.strip_whitespaces(x) for x in lines]
        return lines
    except:
        raise RuntimeError(f"Could not read lines of file {fpath}")


def parse_transaction_amount(line, delimiter, error_msg, error_line_nr, filepath):
    """Read a float from a transactions-line. Raise an error if it fails.
    Return the converted value, adn the remainder of the line for further column-processing"""
    val, remainder = stringoperations.read_crop_string_delimited(line, delimiter)
    try:
        val = float(val)
    except:
        raise RuntimeError(f"{error_msg}.File: {filepath}. Transaction-Line-Nr: {error_line_nr:d}")
    return val, remainder


class ParsingConfig:
    """Common configuration data for parsing the text-files"""

    STRING_ASSET_ACCOUNT = "Account"
    STRING_ASSET_SECURITY = "Security"
    STRING_EOF = "EOF"

    # Strings that identify account action types:
    STRING_ACCOUNT_ACTION_COST = "Fee"
    STRING_ACCOUNT_ACTION_INTEREST = "Interest"
    STRING_ACCOUNT_ACTION_UPDATE = "Update"

    # Allowed actions in the corresponding account-transactions column:
    ACCOUNT_ALLOWED_ACTIONS = [STRING_ACCOUNT_ACTION_COST, STRING_ACCOUNT_ACTION_INTEREST, STRING_ACCOUNT_ACTION_UPDATE]

    # Strings that identify investment action types:
    STRING_INVSTMT_ACTION_BUY = "Buy"
    STRING_INVSTMT_ACTION_SELL = "Sell"
    STRING_INVSTMT_ACTION_COST = "Fee"
    STRING_INVSTMT_ACTION_PAYOUT = "Payout"
    STRING_INVSTMT_ACTION_UPDATE = "Update"
    STRING_INVSTMT_ACTION_SPLIT = "Split"

    # Allowed actions in the corresponding investment-transactions column:
    INVSTMT_ALLOWED_ACTIONS = [STRING_INVSTMT_ACTION_BUY, STRING_INVSTMT_ACTION_SELL, STRING_INVSTMT_ACTION_COST,
                               STRING_INVSTMT_ACTION_PAYOUT, STRING_INVSTMT_ACTION_UPDATE, STRING_INVSTMT_ACTION_SPLIT]

    # Strings for asset transactions-headers:
    # These are used for accounts and investments:
    # This dateformat should be the same as the one specified in config.py # Todo un-hardcode this.
    STRING_DATE = "Date(DD.MM.YYYY)"
    STRING_ACTION = "Action"
    STRING_AMOUNT = "Amount"
    STRING_BALANCE = "Balance"
    STRING_NOTES = "Notes"
    # These are only used for investments:
    STRING_QUANTITY = "Quantity"
    STRING_PRICE = "Price"
    STRING_COST = "Cost"
    STRING_PAYOUT = "Payout"

    # Naming of dictionary-keys (The dict stores transaction-data)
    DICT_KEY_DATES = "dates"
    DICT_KEY_ACTIONS = "actions"
    DICT_KEY_AMOUNTS = "amounts"
    DICT_KEY_BALANCES = "balances"
    DICT_KEY_NOTES = "notes"
    DICT_KEY_QUANTITY = "quantity"
    DICT_KEY_PRICE = "price"
    DICT_KEY_COST = "cost"
    DICT_KEY_PAYOUT = "payout"

    # Identification strings for the asset headers:
    STRING_ID = "ID"
    STRING_TYPE = "Type"
    STRING_PURPOSE = "Purpose"
    STRING_CURRENCY = "Currency"
    STRING_SYMBOL = "Symbol"
    STRING_EXCHANGE = "Exchange"
    STRING_TRANSACTIONS = "Transactions"


class AccountFile:
    """Creates the structure/template for an account-file.
        Provides functions to parse the file and check for errors."""

    def __init__(self, parsing_config, profit_config, filepath, analyzer):
        """Sets up the account-parsing class.
        :param parsing_config: The instance of the parsing-configuration (see above)
        :param profit_config: The instance of the overall configuration of profit
        :param filepath: The path to the file to be read, Path-object
        :analyzer: The instance of the used analyzer-class (to do caching)
        """
        self.parsing_conf = parsing_config
        self.profit_conf = profit_config
        self.account_dict = {self.parsing_conf.STRING_ID: None,
                             self.parsing_conf.STRING_TYPE: None,
                             self.parsing_conf.STRING_PURPOSE: None,
                             self.parsing_conf.STRING_CURRENCY: None}
        self.transactions = {self.parsing_conf.DICT_KEY_DATES: None,
                             self.parsing_conf.DICT_KEY_ACTIONS: None,
                             self.parsing_conf.DICT_KEY_AMOUNTS: None,
                             self.parsing_conf.DICT_KEY_BALANCES: None,
                             self.parsing_conf.DICT_KEY_NOTES: None}
        self.filepath = filepath
        self.analyzer = analyzer
        # Get the lines, strip all white spaces:
        self.lines = read_strip_file_lines(self.filepath)

    def parse_account_file(self, skip_interactive_mode=False):
        """Parses an account-file.
        Calls the constructor of the account-class at the end, and returns the account-instance.
        Any relevant information in the file may not contain whitespaces! They are all eliminated while parsing.
        The last line of the file must contain the string "EOF"
        The string config.STRING_TRANSACTIONS encodes the last line of the header-section.
        The transactions-section has its own header-line, which must adhere to a specific format
        :return: Account-object
        """
        line_validators = {
            0: self.__parse_header_0, 1: self.__parse_header_1, 2: self.__parse_header_2,
            3: self.__parse_header_3, 4: self.__parse_header_4, 5: self.__parse_header_5
        }
        LAST_HEADER_LINE = 6
        # Parse the header:
        for idx, line in enumerate(self.lines):
            if idx == LAST_HEADER_LINE:  # The last case is done separately/in bulk
                break
            validator = line_validators.get(idx)
            validator(line)

        # Parse the transactions:
        self.__parse_transactions_table(self.lines[LAST_HEADER_LINE:])

        if self.profit_conf.INTERACTIVE_MODE is False or skip_interactive_mode is True:
            return self.__create_account_instance()
        else:
            print(f"\nAccount: {self.filepath.name} ({self.account_dict[self.parsing_conf.STRING_ID]}, "
                  f"{self.account_dict[self.parsing_conf.STRING_CURRENCY]})")
            ret = self.__ask_user_for_updated_balance()
            if ret is None:  # No balance-update needed
                return self.__create_account_instance()
            self.__append_file_with_newest_balance(ret)  # Update the file and local data
            return self.__create_account_instance()

    def __append_file_with_newest_balance(self, balance):
        """The user wants to update the file with a new balance.
        Craft the newest transaction-string, write it to file, and update all data within this instance accordingly.
        """
        date_today = dateoperations.get_date_today(self.profit_conf.FORMAT_DATE)
        action = self.parsing_conf.STRING_ACCOUNT_ACTION_UPDATE
        amount = "0"
        balance = f"{balance:.2f}"
        note = ""
        strings = [date_today, action, amount, balance, note]
        # Write the data to file:
        files.append_transaction_line_to_file(self.filepath, strings, self.profit_conf.DELIMITER,
                                              self.parsing_conf.STRING_EOF, self.profit_conf)
        # Reset and then update the local data of this instance:
        self.account_dict = {self.parsing_conf.STRING_ID: None,
                             self.parsing_conf.STRING_TYPE: None,
                             self.parsing_conf.STRING_PURPOSE: None,
                             self.parsing_conf.STRING_CURRENCY: None}
        self.transactions = {self.parsing_conf.DICT_KEY_DATES: None,
                             self.parsing_conf.DICT_KEY_ACTIONS: None,
                             self.parsing_conf.DICT_KEY_AMOUNTS: None,
                             self.parsing_conf.DICT_KEY_BALANCES: None,
                             self.parsing_conf.DICT_KEY_NOTES: None}
        self.lines = read_strip_file_lines(self.filepath)  # Re-read the new file
        self.parse_account_file(skip_interactive_mode=True)  # Re-parse the file, and don't ask again for an update

    def __ask_user_for_updated_balance(self):
        """Show the user the current balance. They can provide a new value.
        Sanitize the input, and return the value if given."""
        user_input = input(f"The most recent balance ({self.transactions[self.parsing_conf.DICT_KEY_DATES][-1]}) is "
                           f"{self.account_dict[self.parsing_conf.STRING_CURRENCY]} "
                           f"{self.transactions[self.parsing_conf.DICT_KEY_BALANCES][-1]:.2f}. "
                           f"Provide an updated balance, or press enter to continue: ")
        if user_input == "":
            return None
        if helper.is_valid_float(user_input) is False:
            print("Received an invalid number. Please re-try.")
            return self.__ask_user_for_updated_balance()
        try:
            return float(user_input)
        except ValueError:
            raise RuntimeError("Could not convert the float. Is the float-checking-function not working?")

    def __create_account_instance(self):
        """Create and return the account-instance from the parsed data"""
        acnt = account.Account(self.account_dict, self.filepath, self.transactions, self.analyzer, self.parsing_conf,
                               self.profit_conf)
        return acnt

    def __parse_header_0(self, line):
        """Store the ID of the account"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_ID:
            self.account_dict[self.parsing_conf.STRING_ID] = val
        else:
            raise RuntimeError(f"Asset-file does not start with 'ID'-string. File: {self.filepath}")
        return True

    def __parse_header_1(self, line):
        """Check if it is actually an account-type"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_TYPE:
            if val != self.parsing_conf.STRING_ASSET_ACCOUNT:
                raise RuntimeError(f"File does not encode an account. File: {self.filepath}")
            self.account_dict[self.parsing_conf.STRING_TYPE] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Type'-string on the 2nd line. File: {self.filepath}")
        return True

    def __parse_header_2(self, line):
        """Store the Purpose of the account"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_PURPOSE:
            self.account_dict[self.parsing_conf.STRING_PURPOSE] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Purpose'-string on the 3rd line. File: {self.filepath}")
        return True

    def __parse_header_3(self, line):
        """Store the Currency of the account"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_CURRENCY:
            self.account_dict[self.parsing_conf.STRING_CURRENCY] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Currency'-string on the 4th line. File: {self.filepath}")
        return True

    def __parse_header_4(self, line):
        """Check for the "Transactions"-String:"""
        id_, _ = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ != self.parsing_conf.STRING_TRANSACTIONS:
            raise RuntimeError(f"Asset-file does not have 'Transactions'-string on the 5th line. File: {self.filepath}")
        return True

    def __parse_header_5(self, line):
        """Check if the first row of the transactions-database is correctly formatted"""
        strings_to_check = [self.parsing_conf.STRING_DATE, self.parsing_conf.STRING_ACTION,
                            self.parsing_conf.STRING_AMOUNT, self.parsing_conf.STRING_BALANCE,
                            self.parsing_conf.STRING_NOTES]
        for i in range(5):
            if i == 0:
                line_id, line_val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
            else:
                line_id, line_val = stringoperations.read_crop_string_delimited(line_val, self.profit_conf.DELIMITER)
            if line_id != strings_to_check[i]:
                raise RuntimeError(f"Column {i + 1:d} of transactions-data does not start with "
                                   f"string '{strings_to_check[i]}'. File: {self.filepath}")
        return True

    def __parse_transactions_table(self, lines):
        """Store the transactions-data. Read all lines until EOF is found.
        :param lines: List of lines of the transactions-data; without any headers.
        """
        date, action, amount, balance, note = [], [], [], [], []
        eof_reached = False
        for i, line in enumerate(lines):
            if line == self.parsing_conf.STRING_EOF:
                eof_reached = True
                break  # We are done, reached the EOF-string
            if len(line) == 0:
                raise RuntimeError(f"File {self.filepath} contains an empty line in the transaction-list. "
                                   f"Transaction-Line-Nr. {i + 1:d}")

            # Parse the date, and check if it is valid:
            trans_date, line_val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
            try:
                datetime_obj = self.analyzer.str2datetime(trans_date)
            except:
                raise RuntimeError(f"Date in transaction falsely specified. File: {self.filepath}. "
                                   f"Transaction-Line-Nr: {i + 1:d}")
            date.append(datetime_obj)

            # Parse the action:
            trans_act, line_val = stringoperations.read_crop_string_delimited(line_val, self.profit_conf.DELIMITER)
            if trans_act not in self.parsing_conf.ACCOUNT_ALLOWED_ACTIONS:
                raise RuntimeError(f"Actions-column contains faulty strings. Filename: {self.filepath}")
            action.append(trans_act)

            # Parse the amount:
            val, line_val = parse_transaction_amount(line_val, self.profit_conf.DELIMITER,
                                                     "Could not read amount. Maybe a missing/wrong delimiter?", i + 1,
                                                     self.filepath)
            amount.append(val)

            # Parse the balance:
            val, line_val = parse_transaction_amount(line_val, self.profit_conf.DELIMITER,
                                                     "Could not read balance. Maybe a missing/wrong delimiter?", i + 1,
                                                     self.filepath)
            balance.append(val)

            # Parse the notes:
            trans_notes, line_val = stringoperations.read_crop_string_delimited(line_val, self.profit_conf.DELIMITER)
            note.append(trans_notes)

        if eof_reached is False:
            raise RuntimeError(f"File does not end with EOF-string. File: {self.filepath}")

        # Store the dates as strings, not as datetime objects.
        date = [self.analyzer.datetime2str(x) for x in date]
        self.transactions[self.parsing_conf.DICT_KEY_DATES] = date
        self.transactions[self.parsing_conf.DICT_KEY_ACTIONS] = action
        self.transactions[self.parsing_conf.DICT_KEY_AMOUNTS] = amount
        self.transactions[self.parsing_conf.DICT_KEY_BALANCES] = balance
        self.transactions[self.parsing_conf.DICT_KEY_NOTES] = note
        return True


class InvestmentFile:
    """Creates the structure/template for an investment-file.
        Provides functions to parse the file and check for errors."""

    def __init__(self, parsing_config, profit_config, filepath, analyzer, dataprovider, storage):
        """Sets up the investment-parsing class.
        :param parsing_config: The instance of the parsing-configuration (see above)
        :param profit_config: The instance of the overall configuration of profit
        :param filepath: The path to the file to be read, Path-object
        :analyzer: The instance of the used analyzer-class (to do caching)
        """
        self.parsing_conf = parsing_config
        self.profit_conf = profit_config
        self.investment_dict = {self.parsing_conf.STRING_ID: None,
                                self.parsing_conf.STRING_TYPE: None,
                                self.parsing_conf.STRING_PURPOSE: None,
                                self.parsing_conf.STRING_CURRENCY: None,
                                self.parsing_conf.STRING_SYMBOL: None,
                                self.parsing_conf.STRING_EXCHANGE: None}
        self.transactions = {self.parsing_conf.DICT_KEY_DATES: None,
                             self.parsing_conf.DICT_KEY_ACTIONS: None,
                             self.parsing_conf.DICT_KEY_QUANTITY: None,
                             self.parsing_conf.DICT_KEY_PRICE: None,
                             self.parsing_conf.DICT_KEY_COST: None,
                             self.parsing_conf.DICT_KEY_PAYOUT: None,
                             self.parsing_conf.DICT_KEY_BALANCES: None,
                             self.parsing_conf.DICT_KEY_NOTES: None}
        self.filepath = filepath
        self.analyzer = analyzer
        self.dataprovider = dataprovider
        self.storage = storage
        # Get the lines, strip all white spaces:
        self.lines = read_strip_file_lines(self.filepath)

    def parse_investment_file(self):
        """Parses an investment-file.
        Calls the constructor of the investment-class at the end, and returns the investment-instance.
        Any relevant information in the file may not contain whitespaces! They are all eliminated while parsing.
        The last line of the file must contain the string "EOF"
        The string config.STRING_TRANSACTIONS encodes the last line of the header-section.
        The transactions-section has its own header-line, which must adhere to a specific format
        :return: Investment-object
        """
        line_validators = {
            0: self.__parse_header_0, 1: self.__parse_header_1, 2: self.__parse_header_2,
            3: self.__parse_header_3, 4: self.__parse_header_4, 5: self.__parse_header_5,
            6: self.__parse_header_6, 7: self.__parse_header_7
        }
        LAST_HEADER_LINE = 8
        # Parse the header:
        for idx, line in enumerate(self.lines):
            if idx == LAST_HEADER_LINE:  # The last case is done separately/in bulk
                break
            validator = line_validators.get(idx)
            validator(line)

        # Parse the transactions:
        self.__parse_transactions_table(self.lines[LAST_HEADER_LINE:])

        # Create the investment-instance, and return it
        invstmt = investment.Investment(self.investment_dict, self.filepath, self.transactions, self.dataprovider,
                                        self.analyzer, self.storage, self.parsing_conf, self.profit_conf)
        return invstmt

    def __parse_header_0(self, line):
        """Store the ID of the Investment"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_ID:
            self.investment_dict[self.parsing_conf.STRING_ID] = val
        else:
            raise RuntimeError(f"Asset-file does not start with 'ID'-string. File: {self.filepath}")
        return True

    def __parse_header_1(self, line):
        """Check if it is actually an investment-type"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_TYPE:
            self.investment_dict[self.parsing_conf.STRING_TYPE] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Type'-string on the 2nd line. File: {self.filepath}")
        return True

    def __parse_header_2(self, line):
        """Store the Purpose of the investment"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_PURPOSE:
            self.investment_dict[self.parsing_conf.STRING_PURPOSE] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Purpose'-string on the 3rd line. File: {self.filepath}")
        return True

    def __parse_header_3(self, line):
        """Store the Currency of the investment"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_CURRENCY:
            self.investment_dict[self.parsing_conf.STRING_CURRENCY] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Currency'-string on the 4th line. File: {self.filepath}")
        return True

    def __parse_header_4(self, line):
        """Store the symbol of the investment"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_SYMBOL:
            self.investment_dict[self.parsing_conf.STRING_SYMBOL] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Symbol'-string on the 5th line. File: {self.filepath}")
        return True

    def __parse_header_5(self, line):
        """Store the Exchange of the investment"""
        id_, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ == self.parsing_conf.STRING_EXCHANGE:
            self.investment_dict[self.parsing_conf.STRING_EXCHANGE] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Exchange'-string on the 6th line. File: {self.filepath}")
        return True

    def __parse_header_6(self, line):
        """Check for the "Transactions"-String:"""
        id_, _ = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id_ != self.parsing_conf.STRING_TRANSACTIONS:
            raise RuntimeError(f"Asset-file does not have 'Transactions'-string on the 7th line. File: {self.filepath}")
        return True

    def __parse_header_7(self, line):
        """Check if the first row of the transactions-database is correctly formatted"""
        strings_to_check = [self.parsing_conf.STRING_DATE, self.parsing_conf.STRING_ACTION,
                            self.parsing_conf.STRING_QUANTITY, self.parsing_conf.STRING_PRICE,
                            self.parsing_conf.STRING_COST, self.parsing_conf.STRING_PAYOUT,
                            self.parsing_conf.STRING_BALANCE, self.parsing_conf.STRING_NOTES]
        for i in range(8):
            if i == 0:
                line_id, line_val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
            else:
                line_id, line_val = stringoperations.read_crop_string_delimited(line_val, self.profit_conf.DELIMITER)
            if line_id != strings_to_check[i]:
                raise RuntimeError(f"Column {i + 1:d} of transactions-data does not start with "
                                   f"string '{strings_to_check[i]}'. File: {self.filepath}")
        return True

    def __parse_transactions_table(self, lines):
        """Store the transactions-data. Read all lines until EOF is found.
        :param lines: List of lines of the transactions-data; without any headers.
        """
        date, action, quantity, price, cost, payout, balance, note = [], [], [], [], [], [], [], []
        eof_reached = False
        for i, line in enumerate(lines):
            if line == self.parsing_conf.STRING_EOF:
                eof_reached = True
                break  # We are done, reached the EOF-string
            if len(line) == 0:
                raise RuntimeError(f"File {self.filepath} contains an empty line in the transaction-list. "
                                   f"Transaction-Line-Nr. {i + 1:d}")

            # Parse the date, and check if it is valid:
            trans_date, line_val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
            try:
                datetime_obj = self.analyzer.str2datetime(trans_date)
            except:
                raise RuntimeError(f"Date in transaction falsely specified. File: {self.filepath}. "
                                   f"Transaction-Line-Nr: {i + 1:d}")
            date.append(datetime_obj)

            # Parse the action:
            trans_act, line_val = stringoperations.read_crop_string_delimited(line_val, self.profit_conf.DELIMITER)
            if trans_act not in self.parsing_conf.INVSTMT_ALLOWED_ACTIONS:
                raise RuntimeError(f"Actions-column contains faulty strings. Filename: {self.filepath}")
            action.append(trans_act)

            # Parse the quantity:
            val, line_val = parse_transaction_amount(line_val, self.profit_conf.DELIMITER,
                                                     "Could not read quantity. Maybe a missing/wrong delimiter?", i + 1,
                                                     self.filepath)
            quantity.append(val)

            # Parse the price:
            val, line_val = parse_transaction_amount(line_val, self.profit_conf.DELIMITER,
                                                     "Could not read price. Maybe a missing/wrong delimiter?", i + 1,
                                                     self.filepath)
            price.append(val)

            # Parse the cost:
            val, line_val = parse_transaction_amount(line_val, self.profit_conf.DELIMITER,
                                                     "Could not read cost. Maybe a missing/wrong delimiter?", i + 1,
                                                     self.filepath)
            cost.append(val)

            # Parse the payout:
            val, line_val = parse_transaction_amount(line_val, self.profit_conf.DELIMITER,
                                                     "Could not read payout. Maybe a missing/wrong delimiter?", i + 1,
                                                     self.filepath)
            payout.append(val)

            # Parse the balance:
            val, line_val = parse_transaction_amount(line_val, self.profit_conf.DELIMITER,
                                                     "Could not read balance. Maybe a missing/wrong delimiter?", i + 1,
                                                     self.filepath)
            balance.append(val)

            # Parse the notes:
            trans_notes, line_val = stringoperations.read_crop_string_delimited(line_val, self.profit_conf.DELIMITER)
            note.append(trans_notes)

        if eof_reached is False:
            raise RuntimeError(f"File does not end with EOF-string. File: {self.filepath}")

        # Store the dates as strings, not as datetime objects.
        date = [self.analyzer.datetime2str(x) for x in date]
        self.transactions[self.parsing_conf.DICT_KEY_DATES] = date
        self.transactions[self.parsing_conf.DICT_KEY_ACTIONS] = action
        self.transactions[self.parsing_conf.DICT_KEY_QUANTITY] = quantity
        self.transactions[self.parsing_conf.DICT_KEY_PRICE] = price
        self.transactions[self.parsing_conf.DICT_KEY_COST] = cost
        self.transactions[self.parsing_conf.DICT_KEY_PAYOUT] = payout
        self.transactions[self.parsing_conf.DICT_KEY_BALANCES] = balance
        self.transactions[self.parsing_conf.DICT_KEY_NOTES] = note
        return True
