"""Provides various low-level configuration constants used throughout PROFIT

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

"""
All asset values are calculated in the base currency.
Provide a string like "CHF", "USD", "HKD" etc.
"""
BASECURRENCY = "CHF"

"""
This switch determines whether the plots are opened directly after creation or not.
If it is set to True, many PDFs will be opened
"""
OPEN_PLOTS = False

"""
Select, if existing plots are deleted before new ones are created. Might prevent confusion/mixups with old/new plots
"""
PURGE_OLD_PLOTS = True

"""
Window length (in days) of moving average filter. Some plots contain filtered data.
"""
WINLEN_MA = 30

"""
Purposes of the Assets
Each asset has a designated purpose. The following list of strings names them all.
The asset purpose must be a member of this list, as otherwise an error is thrown.
Don't use whitespaces in the strings - they are stripped when parsing the asset-files.
"""
ASSET_PURPOSES = ["Liquidity", "Cash", "Retirement_Open", "Retirement_Closed", "Safety_Reserve",
                  "Savings_Car", "Savings_House", "Other"]

"""
Asset Purpose-Groups
The different assets can be grouped according to their purpose, which is used for some plots and provides some insight
into the distribution of asset values.
The groups are given below as list of strings (with arbitrary names).
However, the overall list of lists that collects the groups must be named "ASSET_GROUPS".
"""
ASSET_GROUP_1 = [ASSET_PURPOSES[0], ASSET_PURPOSES[1], ASSET_PURPOSES[7]]
ASSET_GROUP_2 = [ASSET_PURPOSES[2], ASSET_PURPOSES[3]]
ASSET_GROUP_3 = [ASSET_PURPOSES[4]]
ASSET_GROUP_4 = [ASSET_PURPOSES[5], ASSET_PURPOSES[6]]
# This list collects all asset groups. Its name must be ASSET_GROUPS!
ASSET_GROUPS = [ASSET_GROUP_1, ASSET_GROUP_2, ASSET_GROUP_3, ASSET_GROUP_4]
# Corresponding user-defined names can be given for the groups, which will be used in the plots.
ASSET_GROUPNAMES = ["Freely Available Money", "Retirement", "Safety", "Savings"]

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
PLOTS_COLORS = ["#d7191c", "#fdae61", "#5e3c99", "#2c7bb6", "k", "r", "g", "b"]

# Plotting-Settings:
PLOTSIZE = (11.69, 8.27)  # Dimension of the plots, x,y, in inches

# Price-Sanity-Check threshold (in percent)
# Market-data prices are compared to recorded transactions-prices. If they deviate too much, a warning is printed.
# Note that there can be some error, as the online-obtained data is end-of-day, but transactions are usually not/during the day.
# This is used also for sanity-checking of the obtained market-data prices.
# PRICE_COMPARISON_THRESHOLD = 5.0 NOTE: Not being used due to possible/frequent interpolation of data... It would often trigger unneccessarily (see investment.py)

# Delimiter used in the database-files
DELIMITER = ";"

# Date-format used throughout the project (except marketdata; see above).
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
STRING_INVSTMT_ACTION_SPLIT = "Split"

# Allowed actions in the corresponding account-transactions column:
ACCOUNT_ALLOWED_ACTIONS = [STRING_ACCOUNT_ACTION_COST, STRING_ACCOUNT_ACTION_INTEREST, STRING_ACCOUNT_ACTION_UPDATE]

# Allowed actions in the corresponding investment-transactions column:
INVSTMT_ALLOWED_ACTIONS = [STRING_INVSTMT_ACTION_BUY, STRING_INVSTMT_ACTION_SELL, STRING_INVSTMT_ACTION_COST,
                           STRING_INVSTMT_ACTION_PAYOUT, STRING_INVSTMT_ACTION_UPDATE, STRING_INVSTMT_ACTION_SPLIT]

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
PROFIT_VERSION = 1.3

# Dashes for moving averages:
DASHES_MA = [4, 2]
