"""This is the main file of PROFIT. Run it with a python 3 interpreter and marvel at the outputs in the plots-folder
This file also provides some user-definable constants that are used throughout the source-files.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""
import datetime
import logging
from pathlib import Path
from . import accountparser
from . import investmentparser
from . import files
from . import stringoperations
from . import dateoperations
from . import plotting
from . import analysis
from .dataprovider.dataprovider import DataproviderMain
from .storage.storage import MarketDataMain
from .timedomaindata import ForexTimeDomainData
from .timedomaindata import StockMarketIndicesData


def main(config):
    """The main entry-point of PROFIT"""
    # Print the current version of the tool
    print(f"PROFIT v{config.PROFIT_VERSION:.1f} starting")

    # Folder-paths for the outputs of PROFIT:
    storage_path = Path(config.STORAGE_FOLDER).resolve()
    plot_path = Path(config.PLOTS_FOLDER).resolve()
    account_path = Path(config.ACCOUNT_FOLDER).resolve()
    investment_path = Path(config.INVESTMENT_FOLDER).resolve()
    files.check_create_folder(storage_path, create_if_missing=True)
    files.check_create_folder(plot_path, create_if_missing=True)
    is_accnt_folder = files.check_create_folder(account_path, create_if_missing=False)
    is_investment_folder = files.check_create_folder(investment_path, create_if_missing=False)
    if not is_accnt_folder and not is_investment_folder:
        raise FileNotFoundError(f"Both folders {account_path} and {investment_path} are not found. "
                                f"Can not continue / I need either accounts or investments to do anything.")
    if not is_accnt_folder:
        logging.warning(f"Folder for accounts ({account_path}) not found. Will not parse accounts.")
    if not is_investment_folder:
        logging.warning(f"Folder for investments ({investment_path}) not found. Will not parse investments.")

    # Set logging:
    logging.basicConfig(level=logging.WARNING)
    matplotlib_logger = logging.getLogger('matplotlib')
    matplotlib_logger.setLevel(logging.INFO)  # Exclude matplotlib's debug-messages, as they otherwise spam a lot.

    # Initialize the caching datetime/string converter class (used in analyzer below):
    datetimeconverter = stringoperations.DateTimeConversion()

    """
    Define Analysis-Range:
    The analysis range always spans DAYS_ANALYSIS backwards from today.
    """
    date_today = dateoperations.get_date_today(config.FORMAT_DATE, datetime_obj=True)
    date_today_str = dateoperations.get_date_today(config.FORMAT_DATE, datetime_obj=False)
    date_analysis_start = date_today - datetime.timedelta(days=config.DAYS_ANALYSIS)
    date_analysis_start_str = stringoperations.datetime2str(date_analysis_start, config.FORMAT_DATE)
    print(f"\nData will be analyzed from the {date_analysis_start_str} to the {date_today_str}")
    # Create the analysis-instance that tracks some analysis-range-related data:
    analyzer = analysis.AnalysisRange(date_analysis_start_str, date_today_str, config.FORMAT_DATE, datetimeconverter)

    # Initialize the data provider. If none can be initialized, an empty fallback provider will be selected.
    provider = DataproviderMain(analyzer)

    # Initialize the market data system.
    storage = MarketDataMain(storage_path, config.FORMAT_DATE, analyzer)

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
    invstmtfiles = files.get_file_list(investment_path, ".txt")
    invstmtfiles.sort()  # Sort alphabetically
    if len(invstmtfiles) > 0:
        print(f"Found the following {len(invstmtfiles)} textfiles (.txt) in the investment-folder:")
        for x in invstmtfiles: print(x.name)
    else:
        print(f"Found no investment files in folder {investment_path}")
    # Parsing; also creates the investment-objects
    investments = []
    for file in invstmtfiles:
        filepath = file.resolve()
        investments.append(
            investmentparser.parse_investment_file(filepath, config.FORMAT_DATE, provider, analyzer,
                                                   config.BASECURRENCY,
                                                   config.ASSET_PURPOSES, storage, config))
    if len(investments) > 0:
        print(f"Successfully parsed {len(investments)} investments.")

    """
    Parse Accounts:
    """
    print("\nAcquiring and parsing account files")
    accountfiles = files.get_file_list(account_path, ".txt")
    accountfiles.sort()  # Sort alphabetically
    if len(accountfiles) > 0:
        print(f"Found the following {len(accountfiles)} textfiles (.txt) in the account-folder:")
        for x in accountfiles: print(x.name)
    else:
        print(f"Found no account files in folder {account_path}")
    # Parsing; also creates the account-objects
    accounts = []
    for file in accountfiles:
        filepath = file.resolve()
        accounts.append(
            accountparser.parse_account_file(filepath, config.FORMAT_DATE, analyzer, config.BASECURRENCY,
                                             config.ASSET_PURPOSES, config))
    if len(accounts) > 0:
        print(f"Successfully parsed {len(accounts)} accounts.")

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

    print(f"\nFound {len(forex_currencies):d} foreign currencies")

    # The full forex-data for all investment-transactions is required for the holding-period return:
    # Determine the earliest transaction of a foreign-currency investment:
    earliest_forex = dateoperations.asset_get_earliest_forex_trans_date(investments, config.FORMAT_DATE)
    # If the analysis-data-range goes further back than the earliest forex-transaction: adapt accordingly.
    if date_analysis_start < stringoperations.str2datetime(earliest_forex, config.FORMAT_DATE):
        earliest_forex = date_analysis_start_str

    print(f"Basecurrency is {config.BASECURRENCY}")
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
            forexdict[forexstring] = ForexTimeDomainData(forexstring, config.BASECURRENCY, storage, earliest_forex,
                                                         date_today_str, provider, analyzer)

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
        for stockidx in config.INDICES:
            sym = stockidx["Symbol"]
            name = stockidx["Name"]  # The name of the stock-index is stored as the currency
            # Obtain the prices
            obj = StockMarketIndicesData(sym, name, storage, date_analysis_start_str, date_today_str, provider,
                                         analyzer)
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
        fileslist = files.get_file_list(plot_path, None)  # Get all files
        for f in fileslist:
            files.delete_file(f)
    else:
        print("Existing plots are not deleted.")

    if len(accounts) > 0:
        # Plot all accounts:
        plotting.plot_asset_values_stacked(accounts, config.FILENAME_STACKPLOT_ACCOUNT_VALUES, "Value: All Accounts",
                                           analyzer, config)
        # Values of all accounts:
        plotting.plot_asset_values_cost_payout_individual(accounts, config.FILENAME_ACCOUNT_VALUES, analyzer, config)

    if len(investments) > 0:
        plotting.plot_asset_values_indices(investments, indexprices, config.FILENAME_INVESTMENT_VALUES_INDICES,
                                           "Investment Performance (normalized, payouts not reinvested)", analyzer,
                                           config)
        # Plot the values of all investments:
        plotting.plot_asset_values_cost_payout_individual(investments, config.FILENAME_INVESTMENT_VALUES, analyzer,
                                                          config)
        # Plot the returns of all investmets, for different periods:
        plotting.plot_asset_returns_individual(investments, config.FILENAME_INVESTMENT_RETURNS, analyzer, config)
        # Plot the daily absolute returns of all investmets:
        d, ret_total = plotting.plot_asset_returns_individual_absolute(investments,
                                                                       config.FILENAME_INVESTMENT_RETURNS_ABSOLUTE,
                                                                       analyzer, config)
        # Plot the accumulated/summed daily absolute returns of all investmets:
        plotting.plot_asset_total_absolute_returns_accumulated(d, ret_total,
                                                               config.FILENAME_INVESTMENT_RETURNS_ABSOLUTE_TOTAL,
                                                               analyzer, config)
        # Plot all investments:
        plotting.plot_asset_values_stacked(investments, config.FILENAME_STACKPLOT_INVESTMENT_VALUES,
                                           "Value: All Investments",
                                           analyzer, config)
        # Plot the returns of all investments accumulated, for the desired period:
        plotting.plot_assets_returns_total(investments, config.FILENAME_TOTAL_INVESTMENT_RETURNS,
                                           "Returns of Investments",
                                           analyzer, config)
        # Project the value of the investments into the future:
        plotting.plot_asset_projections(investments, config.INTEREST_PROJECTION_PERCENT,
                                        config.NUM_YEARS_INVEST_PROJECTION,
                                        config.FILENAME_INVESTMENT_PROJECTIONS,
                                        "Future Value of All Investments, Compounded Annual Interest", analyzer, config)
        # Calculate the return of all investments, for the considered analysis-period:
        tot_return = analysis.get_returns_assets_accumulated_analysisperiod(investments, analyzer)
        print(
            f"\nThe return of the investments of the considered analysis-period "
            f"(past {config.DAYS_ANALYSIS:d} days) is: {tot_return:.2f}%")

    if len(assets) > 0:
        # Plot the values of each asset purpose:
        plotting.plot_asset_purposes(assets, config.FILENAME_ASSETS_VALUES_PURPOSE,
                                     "Total Asset Values According to Purpose",
                                     analyzer, config)
        # Plot the values of each asset-group:
        plotting.plot_assets_grouped(assets, config.FILENAME_ASSETS_VALUES_GROUPS_STACKED,
                                     "Asset Values According to Group",
                                     "stacked", analyzer, config)
        plotting.plot_assets_grouped(assets, config.FILENAME_ASSETS_VALUES_GROUPS_LINE,
                                     "Asset Values According to Group",
                                     "line", analyzer, config)
        # Plot the value of all assets:
        plotting.plot_asset_values_stacked(assets, config.FILENAME_STACKPLOT_ASSET_VALUES, "Value: All Assets",
                                           analyzer, config)

        # Plot the values of each group:
        if len(config.ASSET_GROUPS) > 0:
            plotting.plot_asset_groups(assets, config.ASSET_GROUPS, config.ASSET_GROUPNAMES, config.FILENAME_PLOT_GROUP,
                                       f"Group Value ({config.BASECURRENCY})", analyzer, config)

        # Plot the values grouped according to currency:
        plotting.plot_currency_values(assets, config.FILENAME_CURRENCIES_STACKED,
                                      "Asset Values According to Currencies "
                                      "(in Basecurrency)", analyzer, config, drawstackedplot=True)
        plotting.plot_currency_values(assets, config.FILENAME_CURRENCIES_LINE,
                                      "Relative Asset Values According to Currencies",
                                      analyzer, config, drawstackedplot=False)

    # Plot the forex-rates. Note: one element of the forex-dict is the basecurrency, hence >1 and not >= 1
    if len(forexdict) > 1:
        plotting.plot_forex_rates(forexdict, config.FILENAME_FOREX_RATES,
                                  f"Forex Rates with the Basecurrency ({config.BASECURRENCY})", analyzer, config)

    print("\nPROFIT is done.")
