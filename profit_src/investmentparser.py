"""Implements functions that are used to parse investment files

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

from . import stringoperations
from . import investment
from . import config
from . import files


def parse_investment_file(filepath, dateformat, dataprovider, analyzer, basecurrency, assetpurposes, storage):
    """This function parses an investment-file.
    Any relevant information in the file may not contain whitespaces! They are all eliminated while parsing.
    The last line of the file must contain the string "EOF"
    The string config.STRING_TRANSACTIONS encodes the last line of the header-section.
    The transactions-section has its own header-line, which must adhere to a specific format
    :param filepath: String of the path of the file that is being parsed
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :param dataprovider: Object of the data provider class, e.g., dataprovider_yahoofinance
    :param analyzer: The analyzer-instance (cf. analysis.py)
    :return: Investment-object
    """

    # Read all lines in the file:
    lines = files.get_file_lines(filepath)

    # Get rid of white spaces in last line of file, then check if it ends with "EOF":
    endline = stringoperations.strip_whitespaces(lines[-1])
    if endline != "EOF":
        raise RuntimeError("File not ending with EOF. File: " + filepath)

    # These will be populated in the following:
    transact_line_nr = None
    invstmt_type = None
    invstmt_purpose = None
    invstmt_sym = None
    invstmt_exchange = None
    invstmt_id = None
    invstmt_currency = None

    # First, the header of the file is read to identify its type and other static information
    for line_nr, line in enumerate(lines):
        # Get rid of _any_ whitespace inside or at the end of the line
        stripline = stringoperations.strip_whitespaces(line)
        # Read the identifier, and also retain the value encoded after the delimiter:
        line_id, line_val = stringoperations.read_crop_string_delimited(stripline, config.DELIMITER)
        # First line in file _must_ be the ID:
        if line_nr == 0:
            # Store the file-ID
            if line_id == config.STRING_ID:
                invstmt_id = line_val
            else:
                raise RuntimeError("Asset-file does not start with 'ID'-string. File: " + filepath)
        # Not first line in file:
        else:
            # "Transactions;" is the last line of the header-section. Header-parsing can stop once this is found.
            if line_id == config.STRING_TRANSACTIONS:
                # Store where the transactions-section of the file begins, to parse transactions below
                transact_line_nr = line_nr
                # Leave for-loop, as the transactions are treated differently below
                break
            # Store the type, purpose, symbol, exchange and currency of the investment
            if line_id == config.STRING_TYPE:
                invstmt_type = line_val
            elif line_id == config.STRING_PURPOSE:
                invstmt_purpose = line_val
            elif line_id == config.STRING_CURRENCY:
                invstmt_currency = line_val
            elif line_id == config.STRING_SYMBOL:
                invstmt_sym = line_val
            elif line_id == config.STRING_EXCHANGE:
                invstmt_exchange = line_val

    # The header is now parsed. Basic info has to be present and/or correct:
    if transact_line_nr is None:
        raise RuntimeError("No transactions given. File: " + filepath)
    if invstmt_type is None:
        raise RuntimeError("Investment type not given. File: " + filepath)
    if invstmt_purpose is None:
        raise RuntimeError("Investment purpose not given. File: " + filepath)
    if invstmt_currency is None:
        raise RuntimeError("Investment currency not given. File: " + filepath)
    if invstmt_sym is None:
        raise RuntimeError("Investment symbol not given. File: " + filepath)
    if invstmt_exchange is None:
        raise RuntimeError("Investment exchange not given. File: " + filepath)

    # Read the remainder of the file (the transactions) into a list of strings:
    # Get the header of the transactions
    trans_header = lines[transact_line_nr + 1]
    trans_header = stringoperations.strip_whitespaces(trans_header)  # Get rid of white spaces

    # Read the identifier of the header of the transactions, and also retain the values
    # encoded after the first delimiter:
    line_id, line_val = stringoperations.read_crop_string_delimited(trans_header, config.DELIMITER)
    if line_id != config.STRING_DATE:
        raise RuntimeError("First transaction-column is not date or of wrong format. File: "
                           + filepath + ". Expected: " + config.STRING_DATE)

    # Process next element, up until next delimiter:
    line_id, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_ACTION:
        raise RuntimeError("Second transaction-column is not action. File: "
                           + filepath + ". Expected: " + config.STRING_ACTION)

    # Process next element, up until next delimiter:
    line_id, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_QUANTITY:
        raise RuntimeError("Third transaction-column is not quantity. File: "
                           + filepath + ". Expected: " + config.STRING_QUANTITY)

    # Process next element, up until next delimiter:
    line_id, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_PRICE:
        raise RuntimeError("Fourth transaction-column is not price. File: "
                           + filepath + ". Expected: " + config.STRING_PRICE)

    # Process next element, up until next delimiter:
    line_id, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_COST:
        raise RuntimeError("Fifth transaction-column is not cost. File: "
                           + filepath + ". Expected: " + config.STRING_COST)

    # Process next element, up until next delimiter:
    line_id, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_PAYOUT:
        raise RuntimeError("Sixth transaction-column is not payout. File: "
                           + filepath + ". Expected: " + config.STRING_PAYOUT)

    # Process next element, up until next delimiter:
    line_id, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_BALANCE:
        raise RuntimeError("Seventh transaction-column is not balance. File: "
                           + filepath + ". Expected: " + config.STRING_BALANCE)

    # Process next element, up until next delimiter:
    line_id, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_NOTES:
        raise RuntimeError("Seventh transaction-column is not notes. File: "
                           + filepath + ". Expected: " + config.STRING_NOTES)

    # Everything is in order. We can parse the transactions into individual lists of strings:
    # Go through the remaining lines, but don't read the EOF-string at the very end.
    # Data storage:
    date = []
    action = []
    quantity = []
    price = []
    cost = []
    payout = []
    balance = []
    notes = []
    for i, line in enumerate(lines[transact_line_nr + 2:-1]):  # Don't read the EOF, too
        stripline = stringoperations.strip_whitespaces(line)  # Get rid of any whitespaces

        if len(stripline) == 0:
            raise RuntimeError("File " + filepath
                               + " contains an empty line in the transaction-list. Transaction-Nr. " + repr(i + 1))

        # Parse the date. Parse it into a datetime-object. This allows some error detection here.
        trans_date, line_val = stringoperations.read_crop_string_delimited(stripline, config.DELIMITER)
        try:
            datetime_obj = stringoperations.str2datetime(trans_date, dateformat)
        except ValueError:
            raise RuntimeError("Date in transaction falsely specified. File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))
        date.append(datetime_obj)

        # Parse the action:
        trans_act, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
        action.append(trans_act)

        # Parse the quantity:
        trans_quant, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
        try:
            quantity.append(float(trans_quant))
        except ValueError:
            raise RuntimeError("Could not read quantity. Maybe a missing/wrong delimiter? File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))

        # Parse the price:
        trans_price, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
        try:
            price.append(float(trans_price))
        except ValueError:
            raise RuntimeError("Could not read price. Maybe a missing/wrong delimiter? File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))

        # Parse the cost:
        trans_cost, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
        try:
            cost.append(float(trans_cost))
        except ValueError:
            raise RuntimeError("Could not read cost. Maybe a missing/wrong delimiter? File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))

        # Parse the payout:
        trans_pay, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
        try:
            payout.append(float(trans_pay))
        except ValueError:
            raise RuntimeError("Could not read payout. Maybe a missing/wrong delimiter? File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))

        # Parse the balance:
        trans_bal, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
        try:
            balance.append(float(trans_bal))
        except ValueError:
            raise RuntimeError("Could not read balance. Maybe a missing/wrong delimiter? File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))

        # Parse the notes:
        trans_notes, line_val = stringoperations.read_crop_string_delimited(line_val, config.DELIMITER)
        notes.append(trans_notes)

    # Store the dates as strings, not as datetime objects.
    # This makes parsing between different date/time implementations later on potentially easier
    date = [analyzer.datetime2str(x) for x in date]

    # Store the results in a dictionary:
    transactions = {config.DICT_KEY_DATES: date, config.DICT_KEY_ACTIONS: action, config.DICT_KEY_QUANTITY: quantity,
                    config.DICT_KEY_PRICE: price, config.DICT_KEY_COST: cost, config.DICT_KEY_PAYOUT: payout,
                    config.DICT_KEY_BALANCES: balance, config.DICT_KEY_NOTES: notes}

    # Create and populate the account-object:
    invstmt = investment.Investment(invstmt_id, invstmt_type, invstmt_purpose, invstmt_currency, basecurrency,
                                    invstmt_sym, invstmt_exchange, filepath, transactions, dateformat, dataprovider,
                                    analyzer, assetpurposes, storage)
    return invstmt
