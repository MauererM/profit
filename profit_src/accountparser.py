"""Implements functions that are used to parse account files

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""
from . import stringoperations as stringops
from . import account
from . import files


def parse_account_file(filepath, dateformat, analyzer, basecurrency, assetpurposes, config):
    """Parses an account-file.
    Calls the constructor of the account-class at the end.
    Any relevant information in the file may not contain whitespaces! They are all eliminated while parsing.
    The last line of the file must contain the string "EOF"
    The string config.STRING_TRANSACTIONS encodes the last line of the header-section.
    The transactions-section has its own header-line, which must adhere to a specific format
    :param filepath: String of the path of the file that is being parsed
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Account-object
    """
    # Read all lines in the file:
    lines = files.get_file_lines(filepath)

    # Get rid of white spaces in last line of file, then check if it ends with "EOF":
    endline = stringops.strip_whitespaces(lines[-1])
    if endline != "EOF":
        raise RuntimeError("File not ending with EOF. File: " + filepath)

    # These will be populated in the following:
    transact_line_nr = None
    accnt_type = None
    accnt_purpose = None
    accnt_currency = None
    accnt_id = None

    # First, the header of the file is read to identify its type and other static information
    for line_nr, line in enumerate(lines):
        # Get rid of _any_ whitespace inside or at the end of the line
        stripline = stringops.strip_whitespaces(line)
        # Read the identifier, and also retain the value encoded after the delimiter:
        line_id, line_val = stringops.read_crop_string_delimited(stripline, config.DELIMITER)
        # First line in file _must_ be the ID:
        if line_nr == 0:
            # Store the file-ID
            if line_id == config.STRING_ID:
                accnt_id = line_val
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
            # Store the type, purpose and currency of the account:
            if line_id == config.STRING_TYPE:
                accnt_type = line_val
            elif line_id == config.STRING_PURPOSE:
                accnt_purpose = line_val
            elif line_id == config.STRING_CURRENCY:
                accnt_currency = line_val

    # The header is now parsed. Basic info has to be present and/or correct:
    if transact_line_nr is None:
        raise RuntimeError("No transactions given. File: " + filepath)
    if accnt_type is None:
        raise RuntimeError("Account type not given. File: " + filepath)
    if accnt_type != config.STRING_ASSET_ACCOUNT:
        raise RuntimeError("File does not encode an account. File: " + filepath)
    if accnt_purpose is None:
        raise RuntimeError("Account purpose not given. File: " + filepath)
    if accnt_currency is None:
        raise RuntimeError("Account currency not given. File: " + filepath)

    # Read the remainder of the file (the transactions) into a list of strings:
    # Get the header of the transactions
    trans_header = lines[transact_line_nr + 1]
    trans_header = stringops.strip_whitespaces(trans_header)  # Get rid of white spaces

    # Read the identifier of the header of the transactions, and also retain the values
    # encoded after the first delimiter:
    line_id, line_val = stringops.read_crop_string_delimited(trans_header, config.DELIMITER)
    if line_id != config.STRING_DATE:
        raise RuntimeError("First transaction-column is not date or of wrong format. File: "
                           + filepath + ". Expected: " + config.STRING_DATE)

    # Process next element, up until next delimiter:
    line_id, line_val = stringops.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_ACTION:
        raise RuntimeError("Second transaction-column is not action. File: "
                           + filepath + ". Expected: " + config.STRING_ACTION)

    # Process next element, up until next delimiter:
    line_id, line_val = stringops.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_AMOUNT:
        raise RuntimeError("Third transaction-column is not amount. File: "
                           + filepath + ". Expected: " + config.STRING_AMOUNT)

    # Process next element, up until next delimiter:
    line_id, line_val = stringops.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_BALANCE:
        raise RuntimeError("Fourth transaction-column is not balance. File: "
                           + filepath + ". Expected: " + config.STRING_BALANCE)

    # Process next element, up until next delimiter:
    line_id, line_val = stringops.read_crop_string_delimited(line_val, config.DELIMITER)
    if line_id != config.STRING_NOTES:
        raise RuntimeError("Fifth transaction-column is not notes. File: "
                           + filepath + ". Expected: " + config.STRING_NOTES)

    # Everything is in order. We can parse the transactions into individual lists of strings:
    # Go through the remaining lines, but don't read the EOF-string at the very end.
    # Data storage:
    date = []
    action = []
    amount = []
    balance = []
    notes = []
    for i, line in enumerate(lines[transact_line_nr + 2:-1]):  # Don't read the EOF, too
        stripline = stringops.strip_whitespaces(line)  # Get rid of any whitespaces

        if len(stripline) == 0:
            raise RuntimeError("File " + filepath
                               + " contains an empty line in the transaction-list. Transaction-Nr. " + repr(i + 1))

        # Parse the date. Parse it into a datetime-object. This allows some error detection here.
        trans_date, line_val = stringops.read_crop_string_delimited(stripline, config.DELIMITER)
        try:
            datetime_obj = analyzer.str2datetime(trans_date)
        except ValueError:
            raise RuntimeError("Date in transaction falsely specified. File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))
        date.append(datetime_obj)

        # Parse the action:
        trans_act, line_val = stringops.read_crop_string_delimited(line_val, config.DELIMITER)
        action.append(trans_act)

        # Parse the amount:
        trans_amount, line_val = stringops.read_crop_string_delimited(line_val, config.DELIMITER)
        try:
            amount.append(float(trans_amount))
        except ValueError:
            raise RuntimeError("Could not read amount. Maybe a missing/wrong delimiter? File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))

        # Parse the balance:
        trans_bal, line_val = stringops.read_crop_string_delimited(line_val, config.DELIMITER)
        try:
            balance.append(float(trans_bal))
        except ValueError:
            raise RuntimeError("Could not read balance. Maybe a missing/wrong delimiter? File: "
                               + filepath + ". Transaction-Nr. " + repr(i + 1))

        # Parse the notes:
        trans_notes, line_val = stringops.read_crop_string_delimited(line_val, config.DELIMITER)
        notes.append(trans_notes)

    # Store the dates as strings, not as datetime objects.
    # This makes parsing between different date/time implementations later on potentially easier
    date = [stringops.datetime2str(x, dateformat) for x in date]

    # Store the results in a dictionary:
    transactions = {config.DICT_KEY_DATES: date, config.DICT_KEY_ACTIONS: action, config.DICT_KEY_AMOUNTS: amount,
                    config.DICT_KEY_BALANCES: balance, config.DICT_KEY_NOTES: notes}

    # Create and populate the account-object:
    accnt = account.Account(accnt_id, accnt_type, accnt_purpose, accnt_currency, basecurrency, filepath,
                            transactions, dateformat, analyzer, assetpurposes, config)
    return accnt
