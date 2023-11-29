"""Implements classes and configurations for parsing account- and investment files.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

from . import stringoperations
from . import files
from . import account


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
    # This dateformat should be the same as the one specified in config.py # Todo un-hardcode this
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
        self.lines = self.__read_account_file()

    def __read_account_file(self):
        try:
            lines = files.get_file_lines(self.filepath)
            lines = [stringoperations.strip_whitespaces(x) for x in lines]
            return lines
        except:
            raise RuntimeError(f"Could not read lines of file {self.filepath}")

    def parse_account_file(self):
        """Parses an account-file.
        Calls the constructor of the account-class at the end, and returns the account-instance.
        Any relevant information in the file may not contain whitespaces! They are all eliminated while parsing.
        The last line of the file must contain the string "EOF"
        The string config.STRING_TRANSACTIONS encodes the last line of the header-section.
        The transactions-section has its own header-line, which must adhere to a specific format
        :return: Account-object
        """
        line_validators = {
            0: self.__parse_header_0,
            1: self.__parse_header_1,
            2: self.__parse_header_2,
            3: self.__parse_header_3,
            4: self.__parse_header_4,
            5: self.__parse_header_5
        }
        # Parse the header:
        for idx, line in enumerate(self.lines):
            if idx == 6:  # The last case is done separately/in bulk
                break
            validator = line_validators.get(idx)
            validator(line)

        # Parse the transactions:
        self.__parse_transactions_table(self.lines[6:])

        # Create the account-instance, and return it
        acnt = account.Account(self.account_dict[self.parsing_conf.STRING_ID],
                                  self.account_dict[self.parsing_conf.STRING_TYPE],
                                  self.account_dict[self.parsing_conf.STRING_PURPOSE],
                                  self.account_dict[self.parsing_conf.STRING_CURRENCY],
                                  self.profit_conf.BASECURRENCY,
                                  self.filepath,
                                  self.transactions,
                                  self.profit_conf.FORMAT_DATE,
                                  self.analyzer,
                                  self.profit_conf.ASSET_PURPOSES,
                                  self.parsing_conf)
        return acnt

    def __parse_header_0(self, line):
        """Store the ID of the account"""
        id, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id == self.parsing_conf.STRING_ID:
            self.account_dict[self.parsing_conf.STRING_ID] = val
        else:
            raise RuntimeError(f"Asset-file does not start with 'ID'-string. File: {self.filepath}")
        return True

    def __parse_header_1(self, line):
        """Check if it is actually an account-type"""
        id, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id == self.parsing_conf.STRING_TYPE:
            if val != self.parsing_conf.STRING_ASSET_ACCOUNT:
                raise RuntimeError(f"File does not encode an account. File: {self.filepath}")
            self.account_dict[self.parsing_conf.STRING_TYPE] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Type'-string on the 2nd line. File: {self.filepath}")
        return True

    def __parse_header_2(self, line):
        """Store the Purpose of the account"""
        id, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id == self.parsing_conf.STRING_PURPOSE:
            self.account_dict[self.parsing_conf.STRING_PURPOSE] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Purpose'-string on the 3rd line. File: {self.filepath}")
        return True

    def __parse_header_3(self, line):
        """Store the Currency of the account"""
        id, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id == self.parsing_conf.STRING_CURRENCY:
            self.account_dict[self.parsing_conf.STRING_CURRENCY] = val
        else:
            raise RuntimeError(f"Asset-file does not have 'Currency'-string on the 4th line. File: {self.filepath}")
        return True

    def __parse_header_4(self, line):
        """Check for the "Transactions"-String:"""
        id, val = stringoperations.read_crop_string_delimited(line, self.profit_conf.DELIMITER)
        if id != self.parsing_conf.STRING_TRANSACTIONS:
            raise RuntimeError(f"Asset-file does not have 'Transactions'-string on the 5th line. File: {self.filepath}")
        return True

    def __parse_header_5(self, line):
        """Check if the first row of the transactions-database is correctly formatted"""
        strings_to_check = [self.parsing_conf.STRING_DATE,
                            self.parsing_conf.STRING_ACTION,
                            self.parsing_conf.STRING_AMOUNT,
                            self.parsing_conf.STRING_BALANCE,
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
                raise RuntimeError(f"Actions-column contains faulty strings. Filename: {self.filename}")
            action.append(trans_act)

            # Parse the amount:
            trans_amount, line_val = stringoperations.read_crop_string_delimited(line_val, self.profit_conf.DELIMITER)
            try:
                amount.append(float(trans_amount))
            except:
                raise RuntimeError(f"Could not read amount. Maybe a missing/wrong delimiter? File: {self.filepath}. "
                                   f"Transaction-Line-Nr: {i + 1:d}")

            # Parse the balance:
            trans_bal, line_val = stringoperations.read_crop_string_delimited(line_val, self.profit_conf.DELIMITER)
            try:
                balance.append(float(trans_bal))
            except:
                raise RuntimeError(f"Could not read balance. Maybe a missing/wrong delimiter? File: {self.filepath}. "
                                   f"Transaction-Line-Nr: {i + 1:d}")

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
