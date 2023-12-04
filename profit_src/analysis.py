"""Implements different functions for various analysis purposes, e.g., financial returns.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import itertools
import logging
from . import dateoperations
from . import stringoperations
from . import helper


class AnalysisRange:
    """Stores data related to the analysis-data-range, which is often used across various functions
    Used to implement caching for frequent datetime conversions, and provides access to commonly
    used configs (e.g., dateformat).
    """

    def __init__(self, startdate, stopdate, dateformat_str, datetime_converter):
        """Constructor
        :param startdate: String for start-date
        :param stopdate: String for stop-date
        :param dateformat_str: The utilized date-format string
        :param datetime_converter: Object of the datetime-converter functions that use caching
        """
        self.dateformat = dateformat_str
        self.datetime_converter = datetime_converter  # Note: This instance is referenced, not copied
        self.startdate_dt = self.datetime_converter.str2datetimecached(startdate, self.dateformat)
        self.stopdate_dt = self.datetime_converter.str2datetimecached(stopdate, self.dateformat)
        self.analysis_datelist = dateoperations.create_datelist(startdate, stopdate, None, dateformat=self.dateformat)
        self.analysis_datelist_dt = [self.str2datetime(x) for x in self.analysis_datelist]

    def str2datetime(self, string):
        return self.datetime_converter.str2datetimecached(string, self.dateformat)

    def datetime2str(self, dt):
        return self.datetime_converter.datetime2strcached(dt, self.dateformat)

    def get_analysis_datelist(self):
        return self.analysis_datelist

    def get_analysis_datelist_dt(self):
        return self.analysis_datelist_dt

    def get_dateformat(self):
        return self.dateformat


def project_values(datelist, valuelist, num_years, interest_percent, analyzer):
    """Projects values into the future given a certian interest rate. Annual compounding is assumed.
    Exponential growth will be displayed.
    :param datelist: List of dates corresponding to the values in valuelist
    :param valuelist: Values. The last value is used to start the projection
    :param num_years: Number of years to calculate into the future
    :param interest_percent: Annual interest rate in percent. Annual compounding is assumed
    :param analyzer: Analyzer-instance for cached conversions
    :return: Tuple of two lists: dates and values of both the past and future values, assuming the exponential growth.
    """
    # The projection starts from the next subsequent day:
    date_start = dateoperations.add_days(datelist[-1], 1, analyzer.get_dateformat())
    # Find the end-date:
    date_end = dateoperations.add_years(datelist[-1], num_years, analyzer.get_dateformat())
    # Create a datelist for the days of the projection:
    datelist_fut = dateoperations.create_datelist(date_start, date_end, analyzer)
    interest_day = (interest_percent / 100.0) / 365.0  # The daily interest rate. Annual compounding is assumed.

    vallist_fut = [valuelist[-1]] * len(datelist_fut)  # Create the placeholder-list for the interest-rate accumulation
    vallist_fut = list(itertools.accumulate(vallist_fut, lambda x, _: x * (1.0 + interest_day)))
    vallist_full = valuelist + vallist_fut

    # Concat the date lists to get one continuous list:
    datelist_full = datelist + datelist_fut
    # Sanity check:
    if len(datelist_full) != len(vallist_full):
        raise RuntimeError('Lists are of unequal length')
    return datelist_full, vallist_full


def get_asset_values_summed(assets):
    """Sum the daily values of the given assets element-wise/daily"""
    lists = [asset.get_analysis_valuelist() for asset in assets]
    return helper.sum_lists(lists)


def get_asset_inflows_summed(assets):
    """Sum the daily inflows of the given assets element-wise/daily"""
    lists = [asset.get_analysis_inflowlist() for asset in assets]
    return helper.sum_lists(lists)


def get_asset_outflows_summed(assets):
    """Sum the daily outflows of the given assets element-wise/daily"""
    lists = [asset.get_analysis_outflowlist() for asset in assets]
    return helper.sum_lists(lists)


def get_asset_payouts_summed(assets):
    """"Sum the daily payouts of the given assets element-wise/daily"""
    lists = [asset.get_analysis_payoutlist() for asset in assets]
    return helper.sum_lists(lists)


def get_asset_costs_summed(assets):
    """"Sum the daily costs of the given assets element-wise/daily"""
    lists = [asset.get_analysis_costlist() for asset in assets]
    return helper.sum_lists(lists)


def calc_hpr_full_block(dateformat, filename, asset_data, latest_date_price, valuelist=None):
    """Calculate the holding period of an asset for a full valid "block" (meaning: without containing periods
    where the asset was fully sold. https://en.wikipedia.org/wiki/Holding_period_return
    The asset may still be held today. The first balance must be nonzero.
    The data is intended to be provided with a granularity of days, as end-of-day values.
    The holding period assumes that an investment is done once, and has no cashflows during its lifetime. Hence,
    the return is calculated in relation to this initial investment. This function _does_ consider cashflows during
    the investment period, however, it might muddle the "sharpness" of the HPR. Also, this function only calculates the
    HPR for a single ownership-period of an investment (i.e., no zero-balances during the ownership).
    # Todo Implement time-weighted return; this measure might be more interesting for PROFIT (?)
    :param dateformat: String of utilized dateformat
    :param filename: File name of the asset the calculation belongs to.
    :param asset_data: Tuple of lists containing the data ordered as dates, balances, costs, payouts,
    prices, inflows, outflows (individual lists). Price can be "None", then, valuelist is used.
    :param latest_date_price: Tuple of the asset's latest available date and corresponding price-data (date, price),
    or None
    :param valuelist: List of values, can be used if prices are not available (e.g., during analysis period calcs).
    :return: The holding period return of the given holding period-block
    """
    dates, balances, costs, payouts, prices, inflows, outflows = asset_data
    if prices is None and valuelist is None:
        raise RuntimeError("Either prices or values must be given")
    if valuelist is not None:
        if len(balances) != len(valuelist):
            raise RuntimeError("Balances and value list must be of identical length")
    # Here, only the last balance may (or may not) be zero, there may not be any zero-balances within the interval that
    # we analyze here.
    if any(x < 1e-9 for x in balances[0:]):
        raise RuntimeError("This function can only deal with contiguous balance-intervals, i.e., "
                           "no balance may be zero within this interval. Something went wrong elsewhere.")
    if balances[0] < 1e-9:
        raise RuntimeError("This can not be the case, the first balance must come from a buy-transaction. "
                           "Something went wrong elsewhere. Are the balance-blocks being correctly split up?")

    # If the balance of the asset of today is zero, then the value today is also zero.
    if balances[-1] < 1e-9:
        val2 = 0.0
    else:  # There is still a balance today.
        today_dt = dateoperations.get_date_today(dateformat, datetime_obj=True)
        # If there is an asset-price available, get the latest possible one that is recorded:
        if latest_date_price is not None:
            latest_date, latest_price = latest_date_price
            latest_date_dt = stringoperations.str2datetime(latest_date, dateformat)
            # The value can be determined from most recent price!
            if latest_date_dt >= today_dt:
                if valuelist is not None:
                    val2 = valuelist[-1]
                else:
                    val2 = balances[-1] * latest_price  # The latest recorded balance is still valid
                transact_price_necessary = False  # We have a price
            else:
                transact_price_necessary = True
        else:  # No market- or provider data was available.
            transact_price_necessary = True

        # Price must be derived from transaction-data:
        if transact_price_necessary is True:
            # Try to obtain the price from the transactions:
            latest_date_trans = stringoperations.str2datetime(dates[-1], dateformat)
            # Only allow if the transactions contain data from today:
            if latest_date_trans >= today_dt and ((prices is not None and prices[-1] > 1e-9) or
                                                  (valuelist is not None and valuelist[-1] > 1e-9)):
                if valuelist is not None:
                    val2 = valuelist[-1]
                else:
                    val2 = prices[-1] * balances[-1]
            else:
                logging.warning(f"Cannot calculate holding period return of {filename} "
                                f"(with nonzero balance as of today) due to unavailable price of today. "
                                f"Update the assets marketdata storage file or transactions-data with "
                                f"values from today.")
                return None

    # Val1 is the first value of the transactions. As the first transaction is a "buy", the first inflow has to be
    # omitted for the correct calculation of the return.
    if valuelist is not None:
        val1 = valuelist[0]
    else:
        val1 = prices[0] * balances[0]

    inflows[0] = 0.0
    cost = sum(costs)
    payout = sum(payouts)
    inflow = sum(inflows)
    outflow = sum(outflows)
    return calc_hpr(val1, val2, outflow, inflow, payout, cost)


def calc_hpr_blocks(asset_data, dateformat, filename, latest_date_price, valuelist=None):
    """Calculates the holding period return of the provided data. Note: The data can span any interval/time of the
    investment (i.e., it must not necessarily start at the beginning or end of an investment's lifetime).
    If there are several buy- or sell-events, and/or other cashflows during the provided data/duration, they will
    be correctly considered, but the holding period return is still being calculated relative to the _initial_
    investment (or, the value provided at the beginning of the data).
    If there are several blocks of asset-ownership in the provided data, the HPR will be averaged for each block of
    stock-ownership.
    See the documentation in calc_hpr_full_block for more details/insights.
    :param asset_data: Tuple of lists containing the balances and cashflows of the asset, as: datelist, balancelist,
    costlist, payoutlist, pricelist, inflowlist, outflowlist
    :param dateformat: String encoding the dateformat.
    :param filename: File name of the considered asset
    :param latest_date_price: Tuple of date-value of latest available asset price, or None
    :param valuelist: List of values, corresponding to the lists in asset_data, can be used if prices are not available.
    """
    datelist, balancelist, costlist, payoutlist, pricelist, inflowlist, outflowlist = asset_data

    # We need to check if there are several "blocks" of asset-ownership, separated by periods of zero balances
    # (i.e., several periods where the asset was held, but also fully sold inbetween).
    # We separate these blocks, calculate the holding period returns individually, and in the end, average the returns
    # of the different periods.

    # All transactions- indices, where the balance is zero
    zero_balance_idx = [i for i, val in enumerate(balancelist) if val < 1e-9]
    # All indices where the balance is nonzero - used to find the transition between zero- and nonzero balances.
    nonzero_balance_idx = [i for i, val in enumerate(balancelist) if val > 1e-9]

    if 0 in zero_balance_idx:
        raise RuntimeError("Balance-list may not start with zero-balance.")

    # Only a single block of asset-ownership. Asset may still be owned (or not, both is fine).
    # Todo there is a bug here. LYINR is failing, due to obvious reasons. Fix it. Find holes properly!
    if len(zero_balance_idx) == 0 or (len(zero_balance_idx) == 1 and balancelist[-1] < 1e-9):
        return calc_hpr_full_block(dateformat, filename, (datelist, balancelist, costlist,
                                                          payoutlist, pricelist, inflowlist,
                                                          outflowlist),
                                   latest_date_price, valuelist)

    logging.info(f"Found multiple distinct blocks of asset-ownership in {filename}. Will average their "
                 f"respective holding period returns. ")

    idx_start = 0
    returns = []
    for idx in zero_balance_idx:
        if idx_start > 0 and (idx - 1) not in nonzero_balance_idx:
            # If this is the case, we encountered several subsequent entries with balance=0, e.g., because an update-
            # transaction follows a fully sold block, prior to the next buy-block. Or, more naturally, if there are
            # several days between the last sell and first buy action.
            # This essentially detects a transition from zero-balance back to nonzero balance (a repeat-buy condition).
            idx_start = idx_start + 1
            continue
        balances_block = balancelist[idx_start:idx + 1]
        dates_block = datelist[idx_start:idx + 1]
        costs_block = costlist[idx_start:idx + 1]
        payouts_block = payoutlist[idx_start:idx + 1]
        if pricelist is not None:
            prices_block = pricelist[idx_start:idx + 1]
        else:
            prices_block = None
        inflows_block = inflowlist[idx_start:idx + 1]
        outflows_block = outflowlist[idx_start:idx + 1]
        returns.append(calc_hpr_full_block(dateformat, filename, (dates_block, balances_block,
                                                                  costs_block, payouts_block,
                                                                  prices_block, inflows_block,
                                                                  outflows_block),
                                           latest_date_price, valuelist))
        idx_start = idx + 1
    # If the last block of ownership is still "ongoing", i.e., assets are still owned, we need to calculate the last
    # holding period return, too.
    if balancelist[-1] > 1e-9:
        idx_start = zero_balance_idx[-1] + 1
        idx_stop = nonzero_balance_idx[-1] + 1
        balances_block = balancelist[idx_start:idx_stop]
        dates_block = datelist[idx_start:idx_stop]
        costs_block = costlist[idx_start:idx_stop]
        payouts_block = payoutlist[idx_start:idx_stop]
        if pricelist is not None:
            prices_block = pricelist[idx_start:idx_stop]
        else:
            prices_block = None
        inflows_block = inflowlist[idx_start:idx_stop]
        outflows_block = outflowlist[idx_start:idx_stop]
        returns.append(calc_hpr_full_block(dateformat, filename, (dates_block, balances_block,
                                                                  costs_block, payouts_block,
                                                                  prices_block, inflows_block,
                                                                  outflows_block),
                                           latest_date_price, valuelist))
    if None in returns:
        return None
    return sum(returns) / len(returns)  # Build the average of all returns


def calc_hpr_return_asset_holdingperiod(asset):
    """Calculates the holding period return (HPR) of the given, single asset
    It considers _all_ asset-transactions, and not just the analysis-data.
    The holding period ends _today_, i.e., on the day this function is executed. Hence, price data must be avilable
    today (BUT: only if there is still a balance today...)
    Forex-rates might have to be obtained further back than the analysis-data-range, due to this.
    If there are several isolated blocks of asset-ownership, the holding period return of each block is calculated,
    and this function returns the average of the returns of each block.
    The reason this is done is because the holding period return calculates the return relative to the _initial_
    investment. If there are several blocks of asset-ownership, then each has its own initial investment. Calculating
    the holing period return over the whole period would give distorted outputs. This assumes that an initial investment
    is not "modified" too significantly (i.e., not too many subsequent additional buy-events to top up the investment (
    but in any case, the holding period return is correctly calculated, even if there are top-ups)).
    :param asset: Asset-object
    :return: The holding period return of the asset, in %
    """
    # Get the full transaction-data:
    datelist = asset.get_trans_datelist()
    balancelist = asset.get_trans_balancelist()
    costlist = asset.get_trans_costlist()
    payoutlist = asset.get_trans_payoutlist()
    pricelist = asset.get_trans_pricelist()
    inflowlist = asset.get_trans_inflowlist()
    outflowlist = asset.get_trans_outflowlist()

    # If the asset is with a foreign currency, the values must be adapted:
    if asset.get_currency() != asset.get_basecurrency():
        forex_obj = asset.get_forex_obj()
        pricelist = forex_obj.perform_conversion(datelist, pricelist)
        costlist = forex_obj.perform_conversion(datelist, costlist)
        payoutlist = forex_obj.perform_conversion(datelist, payoutlist)
        inflowlist = forex_obj.perform_conversion(datelist, inflowlist)
        outflowlist = forex_obj.perform_conversion(datelist, outflowlist)

    return calc_hpr_blocks((datelist, balancelist, costlist, payoutlist, pricelist, inflowlist, outflowlist),
                    asset.get_dateformat(), asset.get_filename(), asset.get_latest_price_date())


def calc_hpr_return_assets_analysisperiod(assets):
    """Calculates the total return for the given asset(s) over the analysis-period.
    If multiple assets are provided, the asset values are summed, and then the HPR is calculated.
    The values of the assets are summed up (daily) and the return is calculated for the accumulated values.
    It's the holding period return of the specified periods, see: https://en.wikipedia.org/wiki/Holding_period_return)
    The data is intended to be provided with a granularity of days.
    The analysis-data-range of each asset must be identical (in date and size).
    If there are several isolated blocks of asset-ownership, the holding period return of each block is calculated,
    and this function returns the average of the returns of each block.
    :param assets: List of asset-objects, can be a single asset.
    :return: Return of considered analysis-period, in percent, either of the single asset, or of the assets summed.
    """
    if not isinstance(assets, list):
        assets = [assets]
        filename = assets[0].get_filename()
        latest_price_date = assets[0].get_latest_price_date()
    else:
        filename = "Multiple Assets"
        latest_price_date = None
    tot_dates = [asset.get_analysis_datelist() for asset in assets]
    if not helper.are_sublists_same_length(tot_dates):
        raise RuntimeError("List of dates are of unequal length")
    tot_balances = [asset.get_analysis_balances() for asset in assets]
    tot_values = [asset.get_analysis_valuelist() for asset in assets]
    tot_costs = [asset.get_analysis_costlist() for asset in assets]
    tot_payouts = [asset.get_analysis_payoutlist() for asset in assets]
    tot_inflows = [asset.get_analysis_inflowlist() for asset in assets]
    tot_outflows = [asset.get_analysis_outflowlist() for asset in assets]
    balances = helper.sum_lists(tot_balances)
    values = helper.sum_lists(tot_values)
    costs = helper.sum_lists(tot_costs)
    payouts = helper.sum_lists(tot_payouts)
    inflows = helper.sum_lists(tot_inflows)
    outflows = helper.sum_lists(tot_outflows)

    datelist = tot_dates[0]

    # Find the first nonzero balance. In the analysis period, the balances could have been extrapolated backwards.
    idx_start = next((idx for idx, val in enumerate(balances) if val > 1e-9), None)
    if idx_start is None:
        raise RuntimeError("Could not find a balance >0.")
    blocks = [list_[idx_start:] for list_ in [datelist, balances, values, costs,
                                              payouts, inflows, outflows]]
    datelist, balances, values, costs, payouts, inflows, outflows = blocks

    # Todo is this correct? Do the values contain values up until today in all cases? Test this.
    return calc_hpr_blocks((datelist, balances, costs, payouts, None, inflows, outflows),
                    assets[0].get_dateformat(), filename, latest_price_date, values)


# Todo rename to "calc"?
def get_returns_asset_daily_absolute_analysisperiod(asset, analyzer):
    """Calculates the absolute returns of a given asset, for the analysis period
    The data is intended to be provided with a granularity of days.
    :param asset: Asset-object
    :param dateformat: String that specifies the format of the date-strings
    :return: Tuple of two lists: (date, return). The returns of the periods in the datelist. They correspond to the
    returned dates, whereas the last date of the analysis-interval is given. The return is in the asset's currency
    """
    # The value of the asset of today must be known, otherwise, errors are thrown, as the holding period return is
    # otherwise not very meaningful.
    today_dt = dateoperations.get_date_today(analyzer.get_dateformat(), datetime_obj=True)

    # If there is an asset-price available, get the latest possible one that is recorded:
    today_price_avail = False
    ret = asset.get_latest_price_date()
    if ret is not None:
        latest_date, _ = ret
        latest_date_dt = analyzer.str2datetime(latest_date)
        # The value can be determined from most recent price!
        if latest_date_dt >= today_dt:  # We have a price, even for today; this is good.
            today_price_avail = True

    if today_price_avail is False:  # transactions-data needed to get price of today
        datelist_check = asset.get_trans_datelist()
        pricelist_check = asset.get_trans_pricelist()
        latest_date_trans = analyzer.str2datetime(datelist_check[-1])
        # Only allow if the transactions contain data from today:
        if latest_date_trans >= today_dt and pricelist_check[-1] > 1e-9:
            today_price_avail = True

    if today_price_avail is False:
        # Do not repeat this warning here, it's already outputted in the relative holding period calculation function.
        # print("WARNING: Cannot calculate holding period return of "
        #      + asset.get_filename() + " due to unavailable and missing price of today. "
        #                               "Update the assets marketdata-file with values from today or "
        #                               "add a price-defining update-transaction of today.")
        # Return a seemingly impossible (negative!) value:
        # return -1e10
        # raise RuntimeError("Require price of today. Abort plotting")
        pass  # Allow plotting anyways

    # Create new copies - just to be sure (the get-functions should already return copies)
    # Get the analysis period data:
    datelist = asset.get_analysis_datelist()
    costlist = asset.get_analysis_costlist()
    payoutlist = asset.get_analysis_payoutlist()
    valuelist = asset.get_analysis_valuelist()
    inflowlist = asset.get_analysis_inflowlist()
    outflowlist = asset.get_analysis_outflowlist()

    returns = calc_returns_daily_absolute(datelist, valuelist, costlist, payoutlist, inflowlist, outflowlist,
                                          analyzer)
    return datelist, returns

    # Todo fuse these two functions together?


def calc_returns_daily_absolute(datelist, valuelist, costlist, payoutlist, inflowlist, outflowlist, analyzer):
    """Calculates the absolute returns of an asset in the given period (analysis period).
    This function returns the gains (or losses) of the asset _since the start of the analysis period_.
    The data is intended to be provided with a granularity of days.
    Costs, payouts, inflows and outflows are to be given for the corresponding days (as given by datelist)
    The values are always given for the end of the day.
    :param datelist: List of strings of dates (days).
    :param valuelist: List of asset-values, corresponding to the days in datelist
    :param costlist: List of costs, corresponding to the days in datelist
    :param payoutlist: List of payouts, corresponding to the days in datelist
    :param inflowlist: List of inflows into the investment (e.g., "Buy" transactions),
    corresponding to the days in datelist
    :param outflowlist: List of outflows of the investment (e.g., "Sell" transactions),
    corresponding to the days in datelist
    :param dateformat: String that specifies the format of the date-strings
    :return: A single list that for each date in datelist contains the absolute returns of the asset at/up to each date.
    """
    # Sanity-checks:
    if dateoperations.check_dates_consecutive(datelist, analyzer) is False:
        raise RuntimeError("datelist must contain consecutive days.")
    # Check the length of all lists - they must be identical:
    totlist = [datelist, valuelist, costlist, payoutlist, inflowlist, outflowlist]
    n = len(datelist)
    if all(len(x) == n for x in totlist) is False:
        raise RuntimeError("The lists must all be of equal lenghts.")

    ret = []
    for idx, _ in enumerate(datelist):
        cost = sum(costlist[0:idx + 1])
        payout = sum(payoutlist[0:idx + 1])
        inflow = sum(inflowlist[0:idx + 1])
        outflow = sum(outflowlist[0:idx + 1])
        value_current = valuelist[idx]
        abs_gain = value_current - inflow + payout - cost + outflow
        ret.append(abs_gain)
    return ret


def calc_hpr(val1, val2, outflow, inflow, payout, cost):
    """Calculates the holding period return of an investment (in percent)
    :param val1: Value at beginning of period
    :param val2: Value at end of period
    :param outflow: Outflows (e.g., "Sell"-transactions) during period
    :param inflow: Inflows (e.g., "Buy"-transactions) during period
    :param payout: Payouts of the asset
    :param cost: Costs...
    :return: Return of the asset in percent
    """
    # Avoid division by zero:
    if val1 < 1e-9:
        return 0.0
    else:
        return (val2 + outflow + payout - cost - inflow - val1) / val1 * 100.0

# Todo re-order the functions in here.
