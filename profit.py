"""This is the main file of PROFIT. Run it with a python 3 interpreter and marvel at the outputs in the plots-folder
This file also provides some user-definable constants that are used throughout the source-files.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""
import datetime
import accountparser
import investmentparser
import files
import stringoperations
import dateoperations
import plotting
import analysis
import config
from dataprovider.dataprovider import DataproviderMain
from storage.storage import MarketDataMain
from timedomaindata import ForexTimeDomainData
from timedomaindata import StockMarketIndicesData

# Todo: Move the configs here to config.py?

"""
These strings specify the folders from which the account and investment files
are taken.
"""
ACCOUNT_FOLDER = "accounts_examples"
INVESTMENT_FOLDER = "investments_examples"

"""
Data is analyzed a certain number of days into the past, from today
"""
DAYS_ANALYSIS = 3500

"""
Number of years to project the values of the investments into the future. The interest rate is given below.
"""
NUM_YEARS_INVEST_PROJECTION = 20

"""
Assumed interest rate (annual compounding) for the projection, in percent
"""
INTEREST_PROJECTION_PERCENT = 3.0

"""
The following strings name the paths of the different plots that will be generated.
Do not provide the file-extension; PDF files will be created.
The plots are stored in the "plots" folder
"""
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

"""
Stockmarket-Indices. These are used in certain plots. They are also obtained from the dataprovider.
They are given in the following as dicts, with a Name, Symbol and Exchange, whereas the latter two are required by the
data-provider tool.
"""
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

# This list collects the dictionaries, its name must be INDICES!
INDICES = [INDEX_DOW, INDEX_NASDAQ, INDEX_DAX, INDEX_SP, INDEX_SMI]

"""
########################################################################################################################
########################################################################################################################
END OF USER_CONFIG
In the following, the main script begins
########################################################################################################################
########################################################################################################################
"""
if __name__ == '__main__':

    # Print the current version of the tool
    print("PROFIT V{:.1f} starting".format(config.PROFIT_VERSION))

    # Initialize classes:
    datetimeconverter = stringoperations.DateTimeConversion()

    """
    Define Analysis-Range:
    The analysis range always spans DAYS_ANALYSIS backwards from today.
    """
    date_today = dateoperations.get_date_today(config.FORMAT_DATE, datetime_obj=True)
    date_today_str = dateoperations.get_date_today(config.FORMAT_DATE, datetime_obj=False)
    date_analysis_start = date_today - datetime.timedelta(days=DAYS_ANALYSIS)
    date_analysis_start_str = stringoperations.datetime2str(date_analysis_start, config.FORMAT_DATE)
    print("\nData will be analyzed from the " + date_analysis_start_str + " to the " + date_today_str)
    # Create the analysis-instance that tracks some analysis-range-related data:
    analyzer = analysis.AnalysisRange(date_analysis_start_str, date_today_str, config.FORMAT_DATE, datetimeconverter)

    # Initialize the data provider. If none can be initialized, an empty fallback provider will be selected.
    provider = DataproviderMain(analyzer)

    # Initialize the market data system.
    # Todo use the path from config. Clean up old config entries.
    storage = MarketDataMain("marketdata_storage", config.FORMAT_DATE, analyzer)

    """
    Sanity checks:
    """
    if len(config.ASSET_GROUPNAMES) != len(config.ASSET_GROUPS):
        raise RuntimeError("ASSET_GROUPNAMES and ASSET_GROUPS (in the user configuration section of PROFIT_main) must "
                           "be lists with identical length.")

    """
    Parse Investments:
    """
    print("\nAcquiring and parsing investments")
    invstmtfiles = files.get_file_list(INVESTMENT_FOLDER, ".txt")
    invstmtfiles.sort()  # Sort alphabetically
    print("Found the following " + str(len(invstmtfiles)) + " textfiles (.txt) in the investment-folder:")
    [print(x) for x in invstmtfiles]
    # Parsing; also creates the investment-objects
    investments = []
    for file in invstmtfiles:
        filepath = files.create_path(INVESTMENT_FOLDER, file)  # Get path of file, including its folder
        investments.append(
            investmentparser.parse_investment_file(filepath, config.FORMAT_DATE, provider, analyzer,
                                                   config.BASECURRENCY,
                                                   config.ASSET_PURPOSES, storage))
    if len(investments) > 0:
        print("Successfully parsed " + str(len(investments)) + " investments.")

    """
    Parse Accounts:
    """
    print("\nAcquiring and parsing account files")
    accountfiles = files.get_file_list(ACCOUNT_FOLDER, ".txt")
    accountfiles.sort()  # Sort alphabetically
    print("Found the following " + str(len(accountfiles)) + " textfiles (.txt) in the account-folder:")
    [print(x) for x in accountfiles]
    # Parsing; also creates the account-objects
    accounts = []
    for file in accountfiles:
        filepath = files.create_path(ACCOUNT_FOLDER, file)  # Get path of file, including its folder
        accounts.append(
            accountparser.parse_account_file(filepath, config.FORMAT_DATE, analyzer, config.BASECURRENCY,
                                             config.ASSET_PURPOSES))
    if len(accounts) > 0:
        print("Successfully parsed " + str(len(accounts)) + " accounts.")

    # Combine accounts and investments into assets:
    assets = accounts + investments
    if len(assets) < 1:
        print("\nNo accounts or investments found. Terminating.")
        exit()

    """
    Collect the currencies of all assets, and the corresponding exchange-rates
    """
    currencies = []
    for asset in assets:
        currencies.append(asset.get_currency())
    # Remove duplicates:
    currencies = list(set(currencies))
    # Determine the foreign currencies:
    forex_currencies = [x for x in currencies if x != config.BASECURRENCY]

    print("\nFound " + repr(len(forex_currencies)) + " foreign currencies")

    # The full forex-data for all investment-transactions is required for the holding-period return:
    # Determine the earliest transaction of a foreign-currency investment:
    earliest_forex = dateoperations.asset_get_earliest_forex_trans_date(investments, config.FORMAT_DATE)
    # If the analysis-data-range goes further back than the earliest forex-transaction: adapt accordingly.
    if date_analysis_start < stringoperations.str2datetime(earliest_forex, config.FORMAT_DATE):
        earliest_forex = date_analysis_start_str

    print("Basecurrency is " + config.BASECURRENCY)
    # Dictionary for the forex-objects. The key is the corresponding currency.
    forexdict = {}
    if len(forex_currencies) > 0:
        if len(investments) > 0:
            print(f"Will obtain forex-data back to the {earliest_forex} "
                  f"(needed for holding period return calculation).")
        else:
            print(f"Will obtain forex-data back to the {earliest_forex}")

        for forexstring in forex_currencies:
            print(f"Getting forex-rates for {forexstring}")
            forexdict[forexstring] = ForexTimeDomainData(forexstring, config.BASECURRENCY, storage, earliest_forex, date_today_str, provider, analyzer)

    # Store an empty object in the basecurrency-key of the forex-dict:
    forexdict[config.BASECURRENCY] = None

    """
    Write the forex-objects into the assets:
    """
    for asset in assets:
        asset.write_forex_obj(forexdict[asset.get_currency()])

    """
    Set the analysis-data in the assets. This obtains market prices, among others, and may take a short while.
    """
    print("\nPreparing analysis-data for accounts and investments.")
    for asset in assets:
        asset.set_analysis_data(date_analysis_start_str, date_today_str)

    """
    Obtain Stockmarket-Indices
    The prices are obtained from the dataprovider, and a MarketPrices-object is generated.
    """
    # This is only required if there are any investments
    if len(investments) > 0:
        print("\nObtaining stockmarket-indices")
        indexprices = []
        for stockidx in INDICES:
            sym = stockidx["Symbol"]
            ex = stockidx["Exchange"] # Todo Get rid of this hack, we now have the proper class for this
            currency = stockidx["Name"]  # The name of the stock-index is stored as the currency
            # Obtain the prices
            obj = StockMarketIndicesData(sym, currency, storage, date_analysis_start_str, date_today_str, provider, analyzer)
            indexprices.append(obj)

    """
    Create the plots:
    """
    if config.OPEN_PLOTS is True:
        print("\nAnalyzing and plotting... Plots will be opened after creation.")
    else:
        print("\nAnalyzing and plotting... Plots will not be opened after creation.")

    if config.PURGE_OLD_PLOTS is True:
        print("Deleting existing plots.")
        fileslist = files.get_file_list(config.PLOTS_FOLDER, None)  # Get all files
        for f in fileslist:
            fname = files.create_path(config.PLOTS_FOLDER, f)
            files.delete_file(fname)
    else:
        print("Existing plots are not deleted.")

    if len(accounts) > 0:
        # Plot all accounts:
        plotting.plot_asset_values_stacked(accounts, FILENAME_STACKPLOT_ACCOUNT_VALUES, "Value: All Accounts", analyzer)
        # Values of all accounts:
        plotting.plot_asset_values_cost_payout_individual(accounts, FILENAME_ACCOUNT_VALUES, analyzer)

    if len(investments) > 0:
        plotting.plot_asset_values_indices(investments, indexprices, FILENAME_INVESTMENT_VALUES_INDICES,
                                           "Investment Performance (normalized, payouts not reinvested)", analyzer)
        # Plot the values of all investments:
        plotting.plot_asset_values_cost_payout_individual(investments, FILENAME_INVESTMENT_VALUES, analyzer)
        # Plot the returns of all investmets, for different periods:
        plotting.plot_asset_returns_individual(investments, FILENAME_INVESTMENT_RETURNS, analyzer)
        # Plot the daily absolute returns of all investmets:
        d, ret_total = plotting.plot_asset_returns_individual_absolute(investments,
                                                                       FILENAME_INVESTMENT_RETURNS_ABSOLUTE, analyzer)
        # Plot the accumulated/summed daily absolute returns of all investmets:
        plotting.plot_asset_total_absolute_returns_accumulated(d, ret_total, FILENAME_INVESTMENT_RETURNS_ABSOLUTE_TOTAL,
                                                               analyzer)
        # Plot all investments:
        plotting.plot_asset_values_stacked(investments, FILENAME_STACKPLOT_INVESTMENT_VALUES, "Value: All Investments",
                                           analyzer)
        # Plot the returns of all investments accumulated, for the desired period:
        plotting.plot_assets_returns_total(investments, FILENAME_TOTAL_INVESTMENT_RETURNS, "Returns of Investments",
                                           analyzer)
        # Project the value of the investments into the future:
        plotting.plot_asset_projections(investments, INTEREST_PROJECTION_PERCENT, NUM_YEARS_INVEST_PROJECTION,
                                        FILENAME_INVESTMENT_PROJECTIONS,
                                        "Future Value of All Investments, Compounded Annual Interest", analyzer)
        # Calculate the return of all investments, for the considered analysis-period:
        tot_return = analysis.get_returns_assets_accumulated_analysisperiod(investments, analyzer)
        print("\nThe return of the investments of the considered analysis-period (past {:d} days) is: {:.2f} %".format(
            DAYS_ANALYSIS, tot_return))

    if len(assets) > 0:
        # Plot the values of each asset purpose:
        plotting.plot_asset_purposes(assets, FILENAME_ASSETS_VALUES_PURPOSE, "Total Asset Values According to Purpose",
                                     analyzer)
        # Plot the values of each asset-group:
        plotting.plot_assets_grouped(assets, FILENAME_ASSETS_VALUES_GROUPS_STACKED, "Asset Values According to Group",
                                     "stacked", analyzer)
        plotting.plot_assets_grouped(assets, FILENAME_ASSETS_VALUES_GROUPS_LINE, "Asset Values According to Group",
                                     "line", analyzer)
        # Plot the value of all assets:
        plotting.plot_asset_values_stacked(assets, FILENAME_STACKPLOT_ASSET_VALUES, "Value: All Assets", analyzer)

        # Plot the values of each group:
        if len(config.ASSET_GROUPS) > 0:
            plotting.plot_asset_groups(assets, config.ASSET_GROUPS, config.ASSET_GROUPNAMES, FILENAME_PLOT_GROUP,
                                       "Group Value (" + config.BASECURRENCY + ")", analyzer)

        # Plot the values grouped according to currency:
        plotting.plot_currency_values(assets, FILENAME_CURRENCIES_STACKED, "Asset Values According to Currencies "
                                                                           "(in Basecurrency)", analyzer,
                                      drawstackedplot=True)
        plotting.plot_currency_values(assets, FILENAME_CURRENCIES_LINE, "Relative Asset Values According to Currencies",
                                      analyzer, drawstackedplot=False)

    # Plot the forex-rates. Note: one element of the forex-dict is the basecurrency, hence >1 and not >= 1
    if len(forexdict) > 1:
        plotting.plot_forex_rates(forexdict, FILENAME_FOREX_RATES,
                                  "Forex Rates with the Basecurrency (" + config.BASECURRENCY + ")", analyzer)

    print("\nPROFIT is done.")
