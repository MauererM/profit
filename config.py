"""The configuration data of PROFIT.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

class ProfitConfig:
    # Data is always analyzed a certain number of days into the past, from today
    DAYS_ANALYSIS = 2000

    # All asset values are calculated in the base currency.
    # Provide the commonly used string like "CHF", "USD", "HKD" etc.
    BASECURRENCY = "CHF"

    """
    Purposes of the Assets:
    Each asset has a designated purpose. The following list of strings names them all.
    The asset purpose in the asset-file headers must be a member of this list, as otherwise an error is thrown.
    Don't use whitespaces in the strings - they are stripped when parsing the asset-files.
    """
    ASSET_PURPOSES = ["Liquidity", "Cash", "Retirement_Open", "Retirement_Closed", "Safety_Reserve",
                      "Savings_Car", "Savings_House", "Other"]

    """
    Asset Purpose-Groups:
    The different assets can be grouped according to their purpose, which is used for some plots and provides 
    some insight into the distribution of asset values.
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

    # The paths (absolute or relative) for the output- and input folders of PROFIT.
    # Stores market-data files:
    STORAGE_FOLDER = "marketdata_storage"
    # PROFIT's output plots/PDFs:
    PLOTS_FOLDER = "plots"
    # The accounts that PROFIT should parse:
    ACCOUNT_FOLDER = "accounts"
    # The investments that PROFIT should parse:
    INVESTMENT_FOLDER = "investments"

    """
    Stockmarket-Indices. They are also obtained from the dataprovider.
    They are given in the following as dicts, with a Name, Symbol and Exchange, 
    whereas the latter two are required by the data-provider tool.
    """
    # Dow Jones industrial average:
    INDEX_DOW = {"Name": "Dow Jones", "Symbol": "DJI"}
    # NASDAQ:
    INDEX_NASDAQ = {"Name": "NASDAQ", "Symbol": "^IXIC"}
    # DAX:
    INDEX_DAX = {"Name": "DAX", "Symbol": "^GDAXI"}
    # SP500:
    INDEX_SP = {"Name": "S&P500", "Symbol": "^GSPC"}
    # SMI:
    INDEX_SMI = {"Name": "SMI", "Symbol": "^SSMI"}

    # This list collects the dictionaries, its name must be INDICES! # Todo Why?
    INDICES = [INDEX_DOW, INDEX_NASDAQ, INDEX_DAX, INDEX_SP, INDEX_SMI]

    # Number of years to project the values of the investments into the future.
    NUM_YEARS_INVEST_PROJECTION = 20

    # Assumed interest rate (annual compounding) for the projection, in percent
    INTEREST_PROJECTION_PERCENT = 6.0

    # This switch determines whether the plots are opened after creation or not.
    # If set to True, many PDFs will be opened.
    OPEN_PLOTS = False

    # Select, if existing plots are deleted before new ones are created.
    PURGE_OLD_PLOTS = True

    # Window length (in days) of moving average filter. Some plots contain filtered data.
    WINLEN_MA = 90

    # Some colors for plotting.
    # Determined using http://colorbrewer2.org/
    PLOTS_COLORS = ["#d7191c", "#fdae61", "#5e3c99", "#2c7bb6", "k", "r", "g", "b"]

    # Dashes for moving averages:
    DASHES_MA = [4, 2]

    # Plotting-Settings:
    PLOTSIZE = (11.69, 8.27)  # Dimension of the plots, x,y, in inches

    # Delimiter used in all text- and csv-files throughout PROFIT
    DELIMITER = ";"

    # Date-format used throughout PROFIT
    FORMAT_DATE = "%d.%m.%Y"