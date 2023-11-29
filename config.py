"""The configuration data of PROFIT.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

class ProfitConfig:
    # Data is always analyzed a certain number of days into the past, from today
    DAYS_ANALYSIS = 2000

    # All asset values are calculated in the base currency. Provide the commonly used string like "CHF", "USD", "HKD" etc.
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

    # The paths (absolute or relative) for the output- and input folders of PROFIT.
    # Stores market-data files:
    STORAGE_FOLDER = "marketdata_storage"
    # PROFIT's output plots/PDFs:
    PLOTS_FOLDER = "plots"
    # The accounts that PROFIT should parse:
    ACCOUNT_FOLDER = "accounts_examples"
    # The investments that PROFIT should parse:
    INVESTMENT_FOLDER = "investments_examples"

    """
    Stockmarket-Indices. They are also obtained from the dataprovider.
    They are given in the following as dicts, with a Name, Symbol and Exchange, whereas the latter two are required by the
    data-provider tool.
    """
    # Todo: Update this dict/format to the newest system that is used. Also, when obtaining them, output the name in the terminal (not the symbol)?
    # Dow Jones industrial average:
    INDEX_DOW = {"Name": "Dow Jones", "Symbol": "DJI", "Exchange": "INDEXDJX"}
    # NASDAQ:
    INDEX_NASDAQ = {"Name": "NASDAQ", "Symbol": "^IXIC", "Exchange": "INDEXNASDAQ"}
    # DAX:
    INDEX_DAX = {"Name": "DAX", "Symbol": "^GDAXI", "Exchange": "INDEXDAX"}
    # SP500:
    INDEX_SP = {"Name": "S&P500", "Symbol": "^GSPC", "Exchange": "INDEXSP500"}
    # SMI:
    INDEX_SMI = {"Name": "SMI", "Symbol": "^SSMI", "Exchange": "INDEXSMI"}

    # This list collects the dictionaries, its name must be INDICES! # Todo Why?
    INDICES = [INDEX_DOW, INDEX_NASDAQ, INDEX_DAX, INDEX_SP, INDEX_SMI]

    # Number of years to project the values of the investments into the future.
    NUM_YEARS_INVEST_PROJECTION = 20
    # Assumed interest rate (annual compounding) for the projection, in percent
    INTEREST_PROJECTION_PERCENT = 6.0

    # This switch determines whether the plots are opened after creation or not. If set to True, many PDFs will be opened.
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

    # Version of PROFIT:
    PROFIT_VERSION = 1.4 # Todo: Does not belong here

    """
    The following strings name the files of the different plots that will be generated.
    Do not provide the file-extension; PDF files will be created.
    The plots are stored in the "plots" folder
    """
    # Todo: Should these names live closer to the plotting-class?
    # Values of all assets, stacked:
    FILENAME_STACKPLOT_ASSET_VALUES = "Asset_Values_Stacked"
    # Values of all investments, stacked:
    FILENAME_STACKPLOT_INVESTMENT_VALUES = "Investment_Values_Stacked"
    # Values of all accounts, stacked:
    FILENAME_STACKPLOT_ACCOUNT_VALUES = "Account_Values_Stacked"
    # Returns of all investments, for different time periods:
    FILENAME_TOTAL_INVESTMENT_RETURNS = "Investments_Total_Returns"
    # Returns of individual investments, multiple plots per sheet:
    FILENAME_INVESTMENT_RETURNS = "Investments_Returns"
    # Absolute returns of individual investments, multiple plots per sheet:
    FILENAME_INVESTMENT_RETURNS_ABSOLUTE = "Investments_Returns_Absolute"
    # Absolute returns of all investments, summed up:
    FILENAME_INVESTMENT_RETURNS_ABSOLUTE_TOTAL = "Investments_Returns_Absolute_Summed"
    # Values of individual investments, multiple plots per sheet:
    FILENAME_INVESTMENT_VALUES = "Investments_Values"
    # Values of individual accounts, multiple plots per sheet:
    FILENAME_ACCOUNT_VALUES = "Accounts_Values"
    # Value of all investments, compared to some indices:
    FILENAME_INVESTMENT_VALUES_INDICES = "Investment_Values_Indices"
    # Value of all assets, sorted according to their purpose:
    FILENAME_ASSETS_VALUES_PURPOSE = "Assets_Values_Purpose"
    # Value of the groups of assets (see below for groups), two plots are done; one line, one stacked
    FILENAME_ASSETS_VALUES_GROUPS_STACKED = "Assets_Values_Groups_Stacked"
    FILENAME_ASSETS_VALUES_GROUPS_LINE = "Assets_Values_Groups_Line"
    # Forex rates:
    FILENAME_FOREX_RATES = "Forex_Rates"
    # Plots of the groups (can be multiple plots), will be extended with the corresponding group name.
    FILENAME_PLOT_GROUP = "Group"
    # Plots of asset values according to currency:
    FILENAME_CURRENCIES_STACKED = "Asset_Values_Currencies_Stacked"
    FILENAME_CURRENCIES_LINE = "Asset_Values_Currencies_Line"
    # Projected investment values:
    FILENAME_INVESTMENT_PROJECTIONS = "Investments_Values_Projected"