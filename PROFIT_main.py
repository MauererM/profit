"""This is the main file of PROFIT. Run it with a python 3 interpreter and marvel at the outputs in the plots-folder
This file also provides some user-definable constants that are used throughout the source-files.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import accountparser
import investmentparser
import files
import stringoperations
import forex
import datetime
import dateoperations
import plotting
import analysis
import prices
import setup

"""
These strings specify the folders from which the account and investment files
are taken.
"""
ACCOUNT_FOLDER = "accounts_examples"
INVESTMENT_FOLDER = "investments_examples"

"""
All asset values are calculated in the base currency.
Provide a string like "CHF", "USD", "HKD" etc.
"""
BASECURRENCY = "CHF"

"""
Data is analyzed a certain number of days into the past, from today
"""
DAYS_ANALYSIS = 730

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

"""
Stockmarket-Indices. These are used in certain plots. They are also obtained from the dataprovider.
They are given in the following as dicts, with a Name, Symbol and Exchange, whereas the latter two are required by the
data-provider tool.
"""
# Swiss market index:
INDEX_SMI = {"Name": "SMI", "Symbol": "SMI", "Exchange": "INDEXSWX"}
# Dow Jones industrial average:
INDEX_DOW = {"Name": "Dow Jones", "Symbol": ".DJI", "Exchange": "INDEXDJX"}
# NASDAQ:
INDEX_NASDAQ = {"Name": "NASDAQ", "Symbol": ".IXIC", "Exchange": "INDEXNASDAQ"}
# This list collects the dictionaries, its name must be INDICES!
INDICES = [INDEX_SMI, INDEX_DOW, INDEX_NASDAQ]

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
    print("PROFIT V{:.1f} starting".format(setup.PROFIT_VERSION))

    """
    Sanity checks:
    """
    if len(ASSET_GROUPNAMES) != len(ASSET_GROUPS):
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
        investments.append(investmentparser.parse_investment_file(filepath, setup.FORMAT_DATE))
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
        accounts.append(accountparser.parse_account_file(filepath, setup.FORMAT_DATE))
    if len(accounts) > 0:
        print("Successfully parsed " + str(len(accounts)) + " accounts.")

    # Combine accounts and investments into assets:
    assets = accounts + investments
    if len(assets) < 1:
        print("\nNo accounts or investments found. Terminating.")
        exit()

    """
    Define Analysis-Range:
    The analysis range always spans DAYS_ANALYSIS backwards from today.
    """
    date_today = dateoperations.get_date_today(setup.FORMAT_DATE, datetime_obj=True)
    date_today_str = dateoperations.get_date_today(setup.FORMAT_DATE, datetime_obj=False)
    date_analysis_start = date_today - datetime.timedelta(days=DAYS_ANALYSIS)
    date_analysis_start_str = stringoperations.datetime2str(date_analysis_start, setup.FORMAT_DATE)
    print("\nData will be analyzed from the " + date_analysis_start_str + " to the " + date_today_str)

    """
    Collect the currencies of all assets, and the corresponding exchange-rates
    """
    currencies = []
    for asset in assets:
        currencies.append(asset.get_currency())
    # Remove duplicates:
    currencies = list(set(currencies))
    # Determine the foreign currencies:
    forex_currencies = [x for x in currencies if x != BASECURRENCY]

    print("\nFound " + repr(len(forex_currencies)) + " foreign currencies")

    # The full forex-data for all investment-transactions is required for the holding-period return:
    # Determine the earliest transaction of a foreign-currency investment:
    earliest_forex = dateoperations.asset_get_earliest_forex_trans_date(investments, setup.FORMAT_DATE)
    # If the analysis-data-range goes further back than the earliest forex-transaction: adapt accordingly.
    if date_analysis_start < stringoperations.str2datetime(earliest_forex, setup.FORMAT_DATE):
        earliest_forex = date_analysis_start_str

    print("Basecurrency is " + BASECURRENCY)
    # Dictionary for the forex-objects. The key is the corresponding currency.
    forexdict = {}
    if len(forex_currencies) > 0:
        if len(investments) > 0:
            print(
                "Will obtain forex-data back to the " + earliest_forex +
                " (needed for holding period return calculation)")
        else:
            print(
                "Will obtain forex-data back to the " + earliest_forex)

        for forexstring in forex_currencies:
            print("Getting forex-rates for " + forexstring)
            forexdict[forexstring] = forex.ForexRates(forexstring, BASECURRENCY, setup.MARKETDATA_FOLDER,
                                                      setup.MARKETDATA_FORMAT_DATE, setup.MARKETDATA_DELIMITER,
                                                      earliest_forex,
                                                      date_today_str, setup.FORMAT_DATE)
    # Store an empty object in the basecurrency-key of the forex-dict:
    forexdict[BASECURRENCY] = None

    """
    Write the forex-objects into the assets:
    """
    for asset in assets:
        asset.write_forex_obj(forexdict[asset.get_currency()])

    """
    Set the analysis-data in the assets. This obtains market prices, among others, and may take a short while.
    """
    print("\nPreparing analysis-data for accounts and investments. "
          "\nThis also obtains market prices and may take a while")
    for asset in assets:
        asset.set_analysis_data(date_analysis_start_str, date_today_str, setup.FORMAT_DATE)

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
            ex = stockidx["Exchange"]
            currency = stockidx["Name"]  # The name of the stock-index is stored as the currency
            # Obtain the prices
            obj = prices.MarketPrices(sym, ex, currency, setup.MARKETDATA_FOLDER, setup.MARKETDATA_FORMAT_DATE,
                                      setup.MARKETDATA_DELIMITER, date_analysis_start_str, date_today_str,
                                      setup.FORMAT_DATE)
            indexprices.append(obj)

    """
    Create the plots:
    """
    if OPEN_PLOTS is True:
        print("\nPlotting. Plots will be opened after creation.")
    else:
        print("\nPlotting. Plots will not be opened after creation.")

    if PURGE_OLD_PLOTS is True:
        print("Deleting existing plots.")
        fileslist = files.get_file_list(setup.PLOTS_FOLDER, None)  # Get all files
        for f in fileslist:
            fname = files.create_path(setup.PLOTS_FOLDER, f)
            files.delete_file(fname)
    else:
        print("Existing plots are not deleted.")

    if len(accounts) > 0:
        # Plot all accounts:
        plotting.plot_asset_values_stacked(accounts, FILENAME_STACKPLOT_ACCOUNT_VALUES, "Value: All Accounts")
        # Values of all accounts:
        plotting.plot_asset_values_cost_payout_individual(accounts, FILENAME_ACCOUNT_VALUES)

    if len(investments) > 0:
        plotting.plot_asset_values_indices(investments, indexprices, FILENAME_INVESTMENT_VALUES_INDICES,
                                           "Value: All Investments (Indexes are relative to start of analysis-period, "
                                           "or first values > 0)")
        # Plot the values of all investments:
        plotting.plot_asset_values_cost_payout_individual(investments, FILENAME_INVESTMENT_VALUES)
        # Plot the returns of all investmets, for different periods:
        plotting.plot_asset_returns_individual(investments, FILENAME_INVESTMENT_RETURNS)
        # Plot all investments:
        plotting.plot_asset_values_stacked(investments, FILENAME_STACKPLOT_INVESTMENT_VALUES, "Value: All Investments")
        # Plot the returns of all investments accumulated, for the desired period:
        plotting.plot_assets_returns_total(investments, FILENAME_TOTAL_INVESTMENT_RETURNS, "Returns of Investments")
        # Calculate the return of all investments, for the considered analysis-period:
        tot_return = analysis.get_returns_assets_accumulated_analysisperiod(investments, setup.FORMAT_DATE)
        print("\nThe return of the investments of the considered analysis-period (past {:d} days) is: {:.2f} %".format(
            DAYS_ANALYSIS, tot_return))

    if len(assets) > 0:
        # Plot the values of each asset purpose:
        plotting.plot_asset_purposes(assets, FILENAME_ASSETS_VALUES_PURPOSE, "Total Asset Values According to Purpose")
        # Plot the values of each asset-group:
        plotting.plot_assets_grouped(assets, FILENAME_ASSETS_VALUES_GROUPS_STACKED, "Asset Values According to Group",
                                     "stacked")
        plotting.plot_assets_grouped(assets, FILENAME_ASSETS_VALUES_GROUPS_LINE, "Asset Values According to Group",
                                     "line")
        # Plot the value of all assets:
        plotting.plot_asset_values_stacked(assets, FILENAME_STACKPLOT_ASSET_VALUES, "Value: All Assets")

        # Plot the values of each group:
        if len(ASSET_GROUPS) > 0:
            plotting.plot_asset_groups(assets, ASSET_GROUPS, ASSET_GROUPNAMES, FILENAME_PLOT_GROUP,
                                       "Group Value (" + BASECURRENCY + ")")

        # Plot the values grouped according to currency:
        plotting.plot_currency_values(assets, FILENAME_CURRENCIES_STACKED, "Asset Values According to Currencies "
                                                                           "(in Basecurrency)", drawstackedplot=True)
        plotting.plot_currency_values(assets, FILENAME_CURRENCIES_LINE, "Relative Asset Values According to Currencies",
                                      drawstackedplot=False)

    # Plot the forex-rates. Note: one element of the forex-dict is the basecurrency, hence >1 and not >= 1
    if len(forexdict) > 1:
        plotting.plot_forex_rates(forexdict, FILENAME_FOREX_RATES,
                                  "Forex Rates with the Basecurrency (" + BASECURRENCY + ")")

    print("\nPROFIT is done.")
