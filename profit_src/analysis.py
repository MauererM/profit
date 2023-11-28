"""Implements different functions for various analysis purposes, e.g., financial returns.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""
from . import dateoperations
from . import stringoperations
from . import helper


class AnalysisRange:
    """Stores data related to the analysis-data-range, which is often used across various functions
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


def project_values(datelist, valuelist, num_years, interest_percent, dateformat):
    """Projects values into the future given a certian interest rate. Annual compounding is assumed.
    Exponential growth will be displayed.
    :param datelist: List of dates corresponding to the values in valuelist
    :param valuelist: Values. The last value is used to start the projection
    :param num_years: Number of years to calculate into the future
    :param interest_percent: Annual interest rate in percent. Annual compounding is assumed
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Tuple of two lists: dates and values of both the past and future values, assuming the exponential growth.
    """
    # The projection starts from the next subsequent day:
    date_start = dateoperations.add_days(datelist[-1], 1, dateformat)
    # Find the end-date:
    date_end = dateoperations.add_years(datelist[-1], num_years, dateformat)
    # Create a datelist for the days of the projection:
    datelist_fut = dateoperations.create_datelist(date_start, date_end, None, dateformat)
    interest_day = (interest_percent / 100.0) / 365.0  # The daily interest rate. Annual compounding is assumed.
    vallist_fut = list(valuelist)
    for _ in datelist_fut:
        vallist_fut.append(vallist_fut[-1] * (1 + interest_day))
    # Concat the date lists to get one continuous list:
    datelist_fut = datelist + datelist_fut
    # Sanity check:
    if len(datelist_fut) != len(vallist_fut):
        raise RuntimeError('Lists are of unequal length')
    return datelist_fut, vallist_fut


def calc_moving_avg(xlist, ylist, winlen):
    """Calculates the moving-average of a XY data-set. The correspondingly filtered tuple is returned
    (which might be of a shorter length, if winlen > 1) ==> Values are only added, once the moving window is full of
    samples.
    If the list is shorter than the window, the average of the list is returned, together with the last entry in xlist
    :param xlist: List of x-values
    :param ylist: List of to-be-filtered y-values
    :param winlen: Length of the window, must be >= 1
    :return: tuple of filtered x,y values
    """
    if winlen < 1:
        raise RuntimeError("Window length of moving average filter must be >= 1")
    if len(xlist) != len(ylist):
        raise RuntimeError("X, Y lists of moving-avg filter must be of same length")

    # make sure the winlen is an integer:
    n = int(round(winlen, 0))
    if n == 1:
        return xlist, ylist

    # If the data is shorter than the window: simply return the averaged ylist
    if len(xlist) <= n:
        yfilt = sum(ylist) / len(ylist)
        # Get the middle index of the list:
        mididx = int(round(len(xlist) / 2.0)) - 1
        xfilt = xlist[mididx]
        return xfilt, yfilt

    # Window shorter than data lists:
    xfilt = []
    yfilt = []
    # Middle index:
    mididx = int(round(n / 2.0))
    for i, _ in enumerate(ylist, start=n):  # Todo: The start=n here seems to crash Pylint...
        if i == len(ylist) + 1:
            break
        win = ylist[i - n:i]
        avg = sum(win) / n
        xfilt.append(xlist[i - n + mididx - 1])
        yfilt.append(avg)
    return xfilt, yfilt


def get_asset_values_summed(assets):
    """Sum the daily values of the given assets
    :param assets: List of asset-objects
    :return: List of values, corresponding to the length of the analysis-period
    """
    if len(assets) > 1:
        sumval = assets[0].get_analysis_valuelist()
        for asset in assets[1:]:
            val = asset.get_analysis_valuelist()
            if len(val) != len(sumval):
                raise RuntimeError("Assets contain value-lists of differing length.")
            sumval = [x + y for x, y in zip(sumval, val)]
        return sumval
    sumval = assets[0].get_analysis_valuelist()
    return sumval


def get_asset_inflows_summed(assets):
    """Sum the daily inflows of the given assets
    :param assets: List of asset-objects
    :return: List of values, corresponding to the length of the analysis-period
    """
    if len(assets) > 1:
        sumval = assets[0].get_analysis_inflowlist()
        for asset in assets[1:]:
            val = asset.get_analysis_inflowlist()
            if len(val) != len(sumval):
                raise RuntimeError("Assets contain value-lists of differing length.")
            sumval = [x + y for x, y in zip(sumval, val)]
        return sumval
    sumval = assets[0].get_analysis_inflowlist()
    return sumval


def get_asset_outflows_summed(assets):
    """Sum the daily outflows of the given assets
    :param assets: List of asset-objects
    :return: List of values, corresponding to the length of the analysis-period
    """
    if len(assets) > 1:
        sumval = assets[0].get_analysis_outflowlist()
        for asset in assets[1:]:
            val = asset.get_analysis_outflowlist()
            if len(val) != len(sumval):
                raise RuntimeError("Assets contain value-lists of differing length.")
            sumval = [x + y for x, y in zip(sumval, val)]
        return sumval
    sumval = assets[0].get_analysis_outflowlist()
    return sumval


def get_asset_payouts_summed(assets):
    """Sum the daily payouts of the given assets
    :param assets: List of asset-objects
    :return: List of values, corresponding to the length of the analysis-period
    """
    if len(assets) > 1:
        sumval = assets[0].get_analysis_payoutlist()
        for asset in assets[1:]:
            val = asset.get_analysis_payoutlist()
            if len(val) != len(sumval):
                raise RuntimeError("Assets contain value-lists of differing length.")
            sumval = [x + y for x, y in zip(sumval, val)]
        return sumval
    sumval = assets[0].get_analysis_payoutlist()
    return sumval


def get_asset_costs_summed(assets):
    """Sum the daily costs of the given assets
    :param assets: List of asset-objects
    :return: List of values, corresponding to the length of the analysis-period
    """
    if len(assets) > 1:
        sumval = assets[0].get_analysis_costlist()
        for asset in assets[1:]:
            val = asset.get_analysis_costlist()
            if len(val) != len(sumval):
                raise RuntimeError("Assets contain value-lists of differing length.")
            sumval = [x + y for x, y in zip(sumval, val)]
        return sumval
    sumval = assets[0].get_analysis_costlist()
    return sumval


def get_return_asset_holdingperiod(asset, dateformat):
    """Calculates the holding period return of an asset
    It considers _all_ asset-transactions, and not just the analysis-data.
    The holding period ends _today_, i.e., on the day this function is executed. Hence, price data must be avilable
    today.
    Hence, forex-rates might have to be obtained further back than the analysis-data-range
    For this to be correct, make sure that either:
        - The asset can get the most recent prices from the dataprovider
        - The market-data-files contain the most recent price
        - Or there is an "update" transaction in the asset-transactions recently, that defines the price of the asset.
    The value of the asset of today is used to obtain the holding period return.
    :param asset: Asset-object
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
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

    # The value of the asset of today must be known, otherwise, errors are thrown, as the holding period return is
    # otherwise not very meaningful.
    today_dt = dateoperations.get_date_today(dateformat, datetime_obj=True)

    # If the asset is with a foreign currency, the values must be adapted:
    if asset.get_currency() != asset.get_basecurrency():
        forex_obj = asset.get_forex_obj()

    # If there is an asset-price available, get the latest possible one that is recorded:
    ret = asset.get_latest_price_date()
    if ret is not None:
        latest_date, latest_price = ret
        latest_date_dt = stringoperations.str2datetime(latest_date, dateformat)
        # The value can be determined from most recent price!
        if latest_date_dt >= today_dt:
            val2 = balancelist[-1] * latest_price  # The latest recorded balance is still valid
            # Forex conversion required:
            if asset.get_currency() != asset.get_basecurrency():
                val2 = forex_obj.perform_conversion([latest_date], [val2])
                val2 = val2[0]
            transact_price_necessary = False  # We have a price
        else:
            transact_price_necessary = True
    else:  # No market- or provider data was available.
        transact_price_necessary = True

    # Price must be derived from transaction-data:
    if transact_price_necessary is True:
        # Try to obtain the price from the transactions:
        latest_date_trans = stringoperations.str2datetime(datelist[-1], dateformat)
        # Only allow if the transactions contain data from today:
        if latest_date_trans >= today_dt and pricelist[-1] > 1e-9:
            val2 = pricelist[-1] * balancelist[-1]
            if asset.get_currency() != asset.get_basecurrency():
                val2 = forex_obj.perform_conversion([datelist[-1]], [val2])
                val2 = val2[0]
        else:
            print(f"WARNING: Cannot calculate holding period return of {asset.get_filename()} due to unavailable "
                  f"and missing price of today. Update the assets marketdata-file with values from today or add a "
                  f"price-defining update-transaction of today.")
            # Return a seemingly impossible (negative!) value:
            return -1e10

    # If the asset is with a foreign currency, the values must be adapted:
    if asset.get_currency() != asset.get_basecurrency():
        pricelist = forex_obj.perform_conversion(datelist, pricelist)
        costlist = forex_obj.perform_conversion(datelist, costlist)
        payoutlist = forex_obj.perform_conversion(datelist, payoutlist)
        inflowlist = forex_obj.perform_conversion(datelist, inflowlist)
        outflowlist = forex_obj.perform_conversion(datelist, outflowlist)

    # Val1 is the first value of the transactions. As the first transaction is a "buy", the first inflow has to be
    # omitted for the correct calculation of the return (it happened in the "previous" period...)
    val1 = pricelist[0] * balancelist[0]
    inflowlist[0] = 0.0
    cost = sum(costlist)
    payout = sum(payoutlist)
    inflow = sum(inflowlist)
    outflow = sum(outflowlist)

    return calc_return(val1, val2, outflow, inflow, payout, cost)


def get_returns_asset_analysisperiod(asset, analyzer):
    """Calculates the total return for the given asset over its full analysis period
    :param asset: Asset-object
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Return of considered analysis-period, in percent.
    """
    # Obtain the analysis-data of the asset:
    datelist = list(asset.get_analysis_datelist())
    valuelist = list(asset.get_analysis_valuelist())
    costlist = list(asset.get_analysis_costlist())
    payoutlist = list(asset.get_analysis_payoutlist())
    inflowlist = list(asset.get_analysis_inflowlist())
    outflowlist = list(asset.get_analysis_outflowlist())
    # We analyze the return over the full analysis period:
    period = len(datelist)
    # Get the return - Only a single value should be returned, as our analysis-period spans the whole range
    dates, returns = calc_returns_period(datelist, valuelist, costlist, payoutlist, inflowlist, outflowlist, period,
                                         analyzer)
    if len(dates) != 1:
        raise RuntimeError("Something went wrong, only one rate of return should have been given.")
    return returns[0]


def get_returns_assets_accumulated_analysisperiod(assets, analyzer):
    """Calculates the total return for the given multiple assets over the full analysis-period.
    The values of the assets are summed up (daily) and the return is calculated for the accumulated values.
    The analysis-data-range of each asset must be identical (in date and size)
    :param assets: List of asset-objects
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Return of considered analysis-period, in percent.
    """
    datelist = list(assets[0].get_analysis_datelist())
    # The return is calculated over the full analysis-period:
    period = len(datelist)
    dates, returns = get_returns_assets_accumulated(assets, period, analyzer)
    if len(dates) != 1:
        raise RuntimeError("Something went wrong, only one rate of return should have been given.")
    return returns[0]


def get_returns_asset(asset, period, analyzer):
    """Calculates the returns of a given asset, in the given periods.
    It's the holding period return of the specified periods, see: https://en.wikipedia.org/wiki/Holding_period_return)
    The data is intended to be provided with a granularity of days.
    :param asset: Asset-object
    :param period: The period over which the return is calculated. Must be integer.
    :param dateformat: String that specifies the format of the date-strings
    :return: Tuple of two lists: (date, return). The returns of the periods in the datelist. They correspond to the
    returned dates, whereas the last date of the analysis-interval is given. The return is in percent.
    """
    # Create new copies - just to be sure (the get-functions should already return copies)
    datelist = list(asset.get_analysis_datelist())
    valuelist = list(asset.get_analysis_valuelist())
    costlist = list(asset.get_analysis_costlist())
    payoutlist = list(asset.get_analysis_payoutlist())
    inflowlist = list(asset.get_analysis_inflowlist())
    outflowlist = list(asset.get_analysis_outflowlist())

    dates, returns = calc_returns_period(datelist, valuelist, costlist, payoutlist, inflowlist, outflowlist,
                                         period, analyzer)
    return dates, returns


def get_returns_assets_accumulated(assets, period, analyzer):
    """Calculates the returns of all given assets (the asset values are summed daily), in the given periods.
    It's the holding period return of the specified periods, see: https://en.wikipedia.org/wiki/Holding_period_return)
    The data is intended to be provided with a granularity of days.
    The analysis-data-range of each asset must be identical (in date and size)
    :param assets: List of assets (e.g., Account of Investment-Objects)
    :param period: The period over which the return is calculated. Must be integer.
    :param dateformat: String that specifies the format of the date-strings
    :return: Tuple of two lists: (dates, returns). The returns of the periods in the datelist. They correspond to the
    returned dates, whereas the last date of the analysis-interval is given. The return is in percent.
    """
    # Use the first asset as reference:
    # Create new copies - just to be sure (the get-functions should already return copies)
    datelist = list(assets[0].get_analysis_datelist())
    tot_valuelist = list(assets[0].get_analysis_valuelist())
    tot_costlist = list(assets[0].get_analysis_costlist())
    tot_payoutlist = list(assets[0].get_analysis_payoutlist())
    tot_inflowlist = list(assets[0].get_analysis_inflowlist())
    tot_outflowlist = list(assets[0].get_analysis_outflowlist())
    # Accumulate the asset-values:
    if len(assets) > 1:
        # Collect data from remaining assets:
        for asset in assets[1:]:
            dates = asset.get_analysis_datelist()
            values = asset.get_analysis_valuelist()
            costs = asset.get_analysis_costlist()
            payouts = asset.get_analysis_payoutlist()
            inflows = asset.get_analysis_inflowlist()
            outflows = asset.get_analysis_outflowlist()

            # Sanity checks:
            if len(dates) != len(datelist) or dates[0] != datelist[0] or dates[-1] != datelist[-1]:
                raise RuntimeError("All assets must have identical datelists for the return-analysis.")

            # Add the values up:
            for idx, _ in enumerate(dates):
                tot_valuelist[idx] += values[idx]
                tot_costlist[idx] += costs[idx]
                tot_payoutlist[idx] += payouts[idx]
                tot_inflowlist[idx] += inflows[idx]
                tot_outflowlist[idx] += outflows[idx]

    dates, returns = calc_returns_period(datelist, tot_valuelist, tot_costlist, tot_payoutlist, tot_inflowlist,
                                         tot_outflowlist, period, analyzer)
    return dates, returns


def calc_returns_period(datelist, valuelist, costlist, payoutlist, inflowlist, outflowlist, period, analyzer):
    """Calculates the returns of an asset over a set of time periods.
    It's the holding period return of the specified periods, see: https://en.wikipedia.org/wiki/Holding_period_return
    The data is intended to be provided with a granularity of days.
    Costs, payouts, inflows and outflows are to be given for the corresponding days (as given by datelist)
    The values are always given for the end of the day.
    The last analyzed block might not be a full period, as the period may not fit an integer-amount of times into the
    datelist
    :param datelist: List of strings of dates (days). The return of the data corresponding to this date-list is analyzed
    :param valuelist: List of asset-values, corresponding to the days in datelist
    :param costlist: List of costs, corresponding to the days in datelist
    :param payoutlist: List of payouts, corresponding to the days in datelist
    :param inflowlist: List of inflows into the investment (e.g., "Buy" transactions),
    corresponding to the days in datelist
    :param outflowlist: List of outflows of the investment (e.g., "Sell" transactions),
    corresponding to the days in datelist
    :param period: Number of days for which the return is calculated. Must be integer. If len(datelist) > period,
    the return is calculated for each block within the full date list. This is used by the plotting-functions, which
    plot different returns for different time periods.
    :param dateformat: String that specifies the format of the date-strings
    :return: Tuple of two lists: (date, return). The returns of the periods in the datelist. They correspond to the
    returned dates, whereas the last date of the analysis-interval is given. The return is in percent.
    """
    # Sanity-checks:
    if dateoperations.check_dates_consecutive(datelist, analyzer) is False:
        raise RuntimeError("datelist must contain consecutive days.")
    # Check the length of all lists - they must be identical:
    totlist = [datelist, valuelist, costlist, payoutlist, inflowlist, outflowlist]
    n = len(datelist)
    if all(len(x) == n for x in totlist) is False:
        raise RuntimeError("The lists must all be of equal lenghts.")

    # Partition the lists into blocks that correspond to the given period. The last block might be shorter.
    dateblocks = partition_list(datelist, period)
    valueblocks = partition_list(valuelist, period)
    costblocks = partition_list(costlist, period)
    payoutblocks = partition_list(payoutlist, period)
    inflowblocks = partition_list(inflowlist, period)
    outflowblocks = partition_list(outflowlist, period)

    # Iterate over all the blocks and determine the return of each block (=period)
    ret = []
    ret_dates = []
    for periodidx, dates in enumerate(dateblocks):
        values = valueblocks[periodidx]
        costs = costblocks[periodidx]
        payouts = payoutblocks[periodidx]
        inflows = inflowblocks[periodidx]
        outflows = outflowblocks[periodidx]

        # The determination of the period's first value is slightly tricky:
        # It is possible that the provided lists do not contain values at the beginning. Thus, the first index must be
        # found, where the asset contains value:
        startidx = len(values) + 1
        for idx, val in enumerate(values):
            if val > 1e-9:
                startidx = idx
                break
        # The entire block contains no value: Its return cannot be determined.
        if startidx == len(values) + 1:
            ret.append(0.0)
            ret_dates.append(dates[-1])
        else:  # There is value in the current period: Determine, where the value starts
            # The period contained some empty value at the beginning. Crop it.
            if startidx > 0:
                values = values[startidx:]
                costs = costs[startidx:]
                payouts = payouts[startidx:]
                inflows = inflows[startidx:]
                outflows = outflows[startidx:]
                # Now, the first transaction is most likely the inflow which bought the asset. Then, this inflow must be
                # subtracted to get the correct return (it happened in the "previous" period (which is nonexisting in
                # the considered treatment of day-wise transactions)
                val1 = values[0]  # asset-value at beginning of period
                if helper.isclose(val1, inflows[0]) is True:  # If the first transaction is the "buy":
                    inflows[0] = 0.0  # Adjust the border-case
            # The start-index is zero: The entire period contains value (at least at the beginning)
            else:
                # If we are not at the first period, take the value at the end of the last period as new start-value
                if periodidx > 0:
                    val1 = valueblocks[periodidx - 1][-1]  # Last value of previously analyzed period
                # This means that the start- and period-indices are zero: We have value at the very beginning of the
                # considered analysis-data:
                else:
                    val1 = values[0]  # No other option
                    # If the first value is created with an inflow, the first inflow has to be ignored
                    # (it happened in the last period; same as above.
                    if val1 > 1e-9 and helper.isclose(val1, inflows[0]) is True:
                        inflows[0] = 0.0

            # val2 is the asset-value at the end of the period
            val2 = values[-1]

            # Sum the individual contributions over the given period:
            cost_tot = sum(costs)
            payouts_tot = sum(payouts)
            inflows_tot = sum(inflows)
            outflows_tot = sum(outflows)

            ret.append(calc_return(val1, val2, outflows_tot, inflows_tot, payouts_tot, cost_tot))
            ret_dates.append(dates[-1])  # Add the last date of the analyzed period

    # Only retain returns of full periods; the rest is discarded (the last period is often going to be incomplete)
    if len(dateblocks[-1]) < period:
        ret_dates = ret_dates[0:-1]
        ret = ret[0:-1]

    return ret_dates, ret


def get_returns_asset_daily_absolute_analysisperiod(asset, dateformat, analyzer):
    """Calculates the absolute returns of a given asset, for the analysis period
    The data is intended to be provided with a granularity of days.
    :param asset: Asset-object
    :param dateformat: String that specifies the format of the date-strings
    :return: Tuple of two lists: (date, return). The returns of the periods in the datelist. They correspond to the
    returned dates, whereas the last date of the analysis-interval is given. The return is in the asset's currency
    """

    # The value of the asset of today must be known, otherwise, errors are thrown, as the holding period return is
    # otherwise not very meaningful.
    today_dt = dateoperations.get_date_today(dateformat, datetime_obj=True)

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


def calc_return(val1, val2, outflow, inflow, payout, cost):
    """Calculates the return of an investment (in percent)
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


def partition_list(inlist, blocksize):
    """Partitions a list into several lists, of blocksize each (or smaller)
    :param inlist: Input list
    :param blocksize: Size of desired blocks, integer
    :return: List of partitioned lists, each sub-list of length blocksize
    """
    # Make sure we are dealing with integers:
    blocksize = int(round(blocksize, 0))
    return [inlist[i:i + blocksize] for i in range(0, len(inlist), blocksize)]


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    dateformat = "%d.%m.%Y"
    datelist = ["01.01.2000", "02.01.2000", "03.01.2000", "04.01.2000", "05.01.2000", "06.01.2000"]
    valuelist = [1, 100, 105, 105, 55, -80]
    costlist = [0, 10, 0, 0, 0, 0]
    payoutlist = [0, 10, 0, 0, 0, 0]
    inflowlist = [0, 99, 0, 0, 0, 0]
    outflowlist = [0, 5, 0, 0, 160, 5]

    # print(calc_return_absolute(valuelist[0], valuelist[-1], sum(outflowlist), sum(inflowlist), sum(payoutlist), sum(costlist)))
    # print(calc_returns_daily_absolute(datelist, valuelist, costlist, payoutlist, inflowlist, outflowlist, dateformat))

    # xfilt, yfilt = calc_median_filt(datelist, valuelist, 3)
    # print(xfilt)
    # print(yfilt)

    # print(dates)
    # print(ror)
    # xvals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # yvals = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    # winlen = 8

    # xfilt, yfilt = calc_moving_avg(xvals, yvals, winlen)
    # print(repr(yvals))
    # print(repr(xfilt))
    # print(repr(yfilt))

    # lista = [1, 3, 4]
    # listb = [2, 3, 5]
    # sum1 = [x + y for x, y in zip(lista, listb)]
    # listc = [3, 5, 5]
    # sum1 = [x + y for x, y in zip(sum1, listc)]
    # print(sum1)

    # l = ["a", 1, 2, 3, 4, 5, 6, 7, 8]
    # n =3
    # test = partition_list(l, n)
    # print(test)
    # print(test[1][-1])
