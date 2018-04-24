"""Provides various low-level configuration constants used throughout PROFIT

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

# Account-files are located in the account-folder
ACCOUNT_FOLDER = "accounts"
# Investment-files are in the investment-folder
INVESTMENT_FOLDER = "investments"
# The marketdata-folder stores different files containing historic prices and forex-rates
MARKETDATA_FOLDER = "marketdata"
# The plots-folder:
PLOTS_FOLDER = "plots"

# The dateformat used by the marketdata-files may be different. Provide it as string, e.g., "%d.%m.%Y"
MARKETDATA_FORMAT_DATE = "%d.%m.%Y"
# The delimiter used to separate date and value in the marketdata-files, e.g., ";"
MARKETDATA_DELIMITER = ";"

# Some colors for plotting.
# Determined using http://colorbrewer2.org/
PLOTS_COLORS = ["#d7191c", "#fdae61", "#5e3c99", "#2c7bb6", "k"]

# Plotting-Settings:
PLOTSIZE = (11.69, 8.27)  # Dimension of the plots, x,y, in inches

# Price-Sanity-Check threshold (in percent)
# Market-data prices are compared to recorded transactions-prices. If they deviate too much, a warning is printed.
PRICE_COMPARISON_THRESHOLD = 2.0

# Delimiter used in the database-files
DELIMITER = ";"

# Date-format used throughout the project:
FORMAT_DATE = "%d.%m.%Y"

# String that identify asset types:
STRING_ASSET_ACCOUNT = "Account"
# Only when an investment is a security is it attempted to obtain online market data/prices.
STRING_ASSET_SECURITY = "Security"

# Strings that identify account action types:
STRING_ACCOUNT_ACTION_COST = "Fee"
STRING_ACCOUNT_ACTION_INTEREST = "Interest"
STRING_ACCOUNT_ACTION_UPDATE = "Update"

# Strings that identify investment action types:
STRING_INVSTMT_ACTION_BUY = "Buy"
STRING_INVSTMT_ACTION_SELL = "Sell"
STRING_INVSTMT_ACTION_COST = "Fee"
STRING_INVSTMT_ACTION_PAYOUT = "Payout"
STRING_INVSTMT_ACTION_UPDATE = "Update"

# Allowed actions in the corresponding account-transactions column:
ACCOUNT_ALLOWED_ACTIONS = [STRING_ACCOUNT_ACTION_COST, STRING_ACCOUNT_ACTION_INTEREST, STRING_ACCOUNT_ACTION_UPDATE]

# Allowed actions in the corresponding investment-transactions column:
INVSTMT_ALLOWED_ACTIONS = [STRING_INVSTMT_ACTION_BUY, STRING_INVSTMT_ACTION_SELL, STRING_INVSTMT_ACTION_COST,
                           STRING_INVSTMT_ACTION_PAYOUT, STRING_INVSTMT_ACTION_UPDATE]

# Strings for asset transactions-headers:
# These are used for accounts and investments:
# This dateformat should be the same as the one specified above...
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

# Version of PROFIT:
PROFIT_VERSION = 1.0
