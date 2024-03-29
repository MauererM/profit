"""Implements functions related to handling dates and the corresponding data
Dates are transferred as lists of strings between different functions, for compatibility and maintainability reasons

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import datetime
from . import stringoperations


def add_years(date, num_years, dateformat):
    """Adds (or subtracts) a number of years to a given date
    :param date: String of origninal date
    :param num_years: Number of years to add or subtract, can be negative. Will be rounded to nearest int!
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: String of newly obtained date
    """
    num_years_int = int(num_years)
    date_dt = stringoperations.str2datetime(date, dateformat)
    date_added_dt = date_dt + datetime.timedelta(days=num_years_int * 365)
    return stringoperations.datetime2str(date_added_dt, dateformat)


def add_days(date, num_days, dateformat):
    """Adds (or subtracts) a number of days to a given date
    :param date: String of origninal date
    :param num_days: Number of days to add or subtract, can be negative. Will be rounded to nearest int!
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: String of newly obtained date
    """
    num_days_int = int(num_days)
    date_dt = stringoperations.str2datetime(date, dateformat)
    date_added_dt = date_dt + datetime.timedelta(days=num_days_int)
    return stringoperations.datetime2str(date_added_dt, dateformat)


def asset_get_earliest_forex_trans_date(assets, dateformat):
    """Returns the earliest recorded transaction-date of an asset with foreign currencies.
    :param assets: List of assets
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: String of earliest recorded transaction-date
    """
    # It can't be earlier than today:
    earliest = get_date_today(dateformat, datetime_obj=True)
    for asset in assets:
        # Only consider assets with foreign currencies:
        if asset.get_currency() != asset.get_basecurrency():
            date_trans_earliest = stringoperations.str2datetime(asset.get_first_transaction_date(), dateformat)
            if date_trans_earliest < earliest:
                earliest = date_trans_earliest
    return stringoperations.datetime2str(earliest, dateformat)


def format_datelist(datelist, vallist, begin_date, stop_date, analyzer, zero_padding_past,
                    zero_padding_future):
    """Extends or crops a datelist (and the corresponding values) to fit a certain range of dates.
    Missing data is extrapolated forwards or backwards, either with zeros or with the last known values.
    :param datelist: List of strings of given dates
    :param vallist: List of values, corresponding to the dates in datelist
    :param begin_date: String, encoding the begin of the desired data
    :param stop_date: String, encoding the end of the desired data
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :param zero_padding_past: Boolean. If true: Values are extended with zeros into the past. Otherwise, with the last
    known value (zero-order hold)
    :param zero_padding_future: Boolean. If true: Values are extended with zeros into the future.
    Otherwise, with the last known value (zero-order hold)
    :return: Tuple of two lists: The formatted list of dates (as strings) and the formatted list of values:
    (dates, values)
    """
    # Sanity check:
    if not isinstance(datelist, list) or not isinstance(vallist, list):
        raise RuntimeError("Received empty lists!")
    if len(datelist) != len(vallist):
        raise RuntimeError("Datelist and vallist must be of identical length.")
    # Convert to datetime:
    begin_date_datelist_dt = analyzer.str2datetime(datelist[0])
    stop_date_datelist_dt = analyzer.str2datetime(datelist[-1])
    begin_date_dt = analyzer.str2datetime(begin_date)
    stop_date_dt = analyzer.str2datetime(stop_date)

    # Check, if data can be fully cropped:
    if begin_date_dt >= begin_date_datelist_dt and stop_date_dt <= stop_date_datelist_dt:
        datelist, vallist = crop_datelist(datelist, vallist, begin_date, stop_date, analyzer)
        return datelist, vallist

    # Check, if begin and end are both in the past:
    if begin_date_dt < begin_date_datelist_dt and stop_date_dt < begin_date_datelist_dt:
        # Extend it first into the past, then crop
        datelist, vallist = extend_data_past(datelist, vallist, begin_date, analyzer, zero_padding_past)
        datelist, vallist = crop_datelist(datelist, vallist, begin_date, stop_date, analyzer)
        return datelist, vallist

    # Check, if begin and end are both in the future:
    if begin_date_dt > begin_date_datelist_dt and stop_date_dt > begin_date_datelist_dt:
        # Extend it first into the future, then crop
        datelist, vallist = extend_data_future(datelist, vallist, stop_date, analyzer, zero_padding_future)
        datelist, vallist = crop_datelist(datelist, vallist, begin_date, stop_date, analyzer)
        return datelist, vallist

    # Check, if data needs to be extended into the past:
    if begin_date_dt < begin_date_datelist_dt:
        datelist, vallist = extend_data_past(datelist, vallist, begin_date, analyzer, zero_padding_past)
    # Crop the beginning, but not yet the end:
    else:
        datelist, vallist = crop_datelist(datelist, vallist, begin_date, datelist[-1], analyzer)

    # Check, if data needs to be extended into the future:
    if stop_date_dt > stop_date_datelist_dt:
        datelist, vallist = extend_data_future(datelist, vallist, stop_date, analyzer, zero_padding_future)
    # Crop, now, it can crop the beginning (it will not, since the beginning is handled above)
    else:
        datelist, vallist = crop_datelist(datelist, vallist, begin_date, stop_date, analyzer)

    return datelist, vallist


def crop_datelist(datelist, vallist, begin_date, stop_date, analyzer):
    """Takes a list of dates and corresponding values (they must not necessarily be consecutive) and crops them to a
    desired range.
    If the begin/stop dates match, and the date exists in datelist, one value is returned. If the date does not exist
    in datelist, an empty list is returned.
    The begin- and stop-dates can be outside of the data-range given by datelist, the values are then cropped just to
    the range given by datelist.
    If both dates are outside the datelist, an empty list is returned.
    :param datelist: List of strings of dates, not necessarily consecutive
    :param vallist: List of values, corresponding to dates in datelist
    :param begin_date: String, encodes the beginning of the desired date-interval
    :param stop_date: String, encodes the end of the desired date-interval
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Tuple of two lists: The cropped list of dates (as strings) and the cropped list of values: (dates, values)
    """
    # Use datetime (this also creates a local copy)
    datelist_dt = [analyzer.str2datetime(x) for x in datelist]
    begin_date_dt = analyzer.str2datetime(begin_date)
    stop_date_dt = analyzer.str2datetime(stop_date)
    # Sanity checks:
    if stop_date_dt < begin_date_dt:
        raise RuntimeError("Stop-date must be after start-date.")

    # Get the indices of the datelist whose dates match the desired cropping-range:
    indexes = [i for i, date in enumerate(datelist_dt) if begin_date_dt <= date <= stop_date_dt]
    dates_crop = [datelist[i] for i in indexes]
    vals_crop = [vallist[i] for i in indexes]

    return dates_crop, vals_crop


def interpolate_data(datelist_incompl, vallist_incompl, analyzer):
    """Takes a list of dates (strings) and corresponding values, and interpolates (zero-order hold) data into
    missing dates, such that a list of consecutive days is created.
    The newly created dates span the range of the provided, incomplete datelist.
    :param datelist_incompl: List of strings of dates (with potentially missing dates)
    :param vallist_incompl: List of values
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: Tuple of two lists, the fully populated date-list, and the corresponding interpolated values (dates, vals)
    """
    # Sanity checks:
    if len(datelist_incompl) != len(vallist_incompl):
        raise RuntimeError("Provided lists must be of equal length.")
    if len(datelist_incompl) == 0:
        raise RuntimeError("Received an empty list")
    if check_date_order(datelist_incompl, analyzer, allow_ident_days=True) is False:
        raise RuntimeError("The incomplete date list is not in order.")
    if len(datelist_incompl) != len(vallist_incompl):
        raise RuntimeError("The incomplete lists must be of identical length.")
    if len(datelist_incompl) == 0:
        raise RuntimeError("Requires at least one value to be able to interpolate.")

    start = datelist_incompl[0]
    stop = datelist_incompl[-1]
    # The complete list of all dates:
    datelist_full = create_datelist(start, stop, analyzer)

    # Create a dictionary that contains the last value in the incomplete datelist for faster lookup.
    # The last value is needed as datelist_incompl could contain duplicate entries.
    last_vals = {}
    for i, date in enumerate(datelist_incompl):
        last_vals[date] = i

    vallist_compl = []
    for date in datelist_full:
        if date in last_vals:  # We have a match: Do not interpolate
            v = vallist_incompl[last_vals[date]]
        else:  # No match found: Interpolation needed
            v = vallist_compl[-1]
        vallist_compl.append(v)

    if len(datelist_full) != len(vallist_compl):
        raise RuntimeError("Someting went wrong, these list should be of identical size")

    return datelist_full, vallist_compl


def extend_data_past(datelist, vallist, begin_date, analyzer, zero_padding):
    """Extends a list of dates and corresponding values into the past, until a specified date (included)
    :param datelist: List of strings of dates
    :param vallist: List of values, corresponding to the dates in datelist
    :param begin_date: String, encoding the date in the past until which the lists are extended backwards
    :param analyzer: Analyzer-instance for cached str2datetime conversions
    :param zero_padding: Boolean. If true: Values are extended with zeros. Otherwise, with the last
                        known value (zero-order hold)
    :return: Tuple of two lists: The extended list of dates (as strings) and the extended list of values:
    (dates, values)
    """
    if len(datelist) != len(vallist):
        raise RuntimeError("List of dates and values must be of identical length.")

    datelist_dt_0 = analyzer.str2datetime(datelist[0])
    begin_date_dt = analyzer.str2datetime(begin_date)

    if begin_date_dt > datelist_dt_0:
        raise RuntimeError("Begin-date is later than beginning of datelist. Cannot extrapolate into the past.")

    # Create new lists, before the existing list. Then join the lists.
    auxdates = create_datelist(begin_date, datelist[0], analyzer)
    del auxdates[-1]  # Avoid the duplicate date
    if zero_padding is True:
        auxvals = [0.0] * len(auxdates)
    else:
        auxvals = [vallist[0]] * len(auxdates)
    datelist_full = auxdates + datelist
    vallist_full = auxvals + vallist
    return datelist_full, vallist_full


def extend_data_future(datelist, vallist, stop_date, analyzer, zero_padding):
    """Extends a list of dates and the corresponding list of values into the future, until a given date.
    Increment: 1-day steps
    :param datelist: List of strings encoding the given dates
    :param vallist: List of values, corresponding to the dates in datelist
    :param stop_date: String, encodes the desired end of the extended dates/values
    :param analyzer: For cached string/datetime conversions
    :param zero_padding: Boolean. If true: Values are extended with zeros. Otherwise, with the last
                        known value (zero-order hold)
    :return: Tuple of two lists: The extended list of dates (as strings) and the extended list of values:
    (dates, values)
    """
    if len(datelist) != len(vallist):
        raise RuntimeError("List of dates and values must be of identical length.")

    datelist_dt_end = analyzer.str2datetime(datelist[-1])
    stop_date_dt = analyzer.str2datetime(stop_date)

    if stop_date_dt <= datelist_dt_end:
        raise RuntimeError("Stop-date is not in the future of the given datelist.")

    # Create new lists, before the existing list. Then join the lists.
    auxdates = create_datelist(datelist[-1], stop_date, analyzer)
    del auxdates[0]
    if zero_padding is True:
        auxvals = [0.0] * len(auxdates)
    else:
        auxvals = [vallist[-1]] * len(auxdates)

    datelist_full = datelist + auxdates
    vallist_full = vallist + auxvals
    return datelist_full, vallist_full


def get_date_today(dateformat, datetime_obj=False):
    """Get the date of today, re-formatted to fit the dateformat
    Return either a date-string, or a datetime-object.
    :param dateformat: String that specifies the format of the date-strings
    :param datetime_obj: Bool, if True, a datetime-object is returned. Otherwise, a date-string.
    :return: String or datetime-object of the date of today
    """
    # Get "now"
    today = datetime.datetime.now()
    if datetime_obj is False:
        # Strip the exact time of the day, such that only the desired date-format remains.
        return stringoperations.datetime2str(today, dateformat)
    # Strip the exact time of the day, such that only the desired date-format remains.
    today = stringoperations.datetime2str(today, dateformat)
    return stringoperations.str2datetime(today, dateformat)


def create_datelist(startdate, stopdate, analyzer, dateformat=None):
    """Takes two dates (as strings) and creates a list of days (strings) between (including) these dates.
    Granularity: day (step size between dates)
    startdate must be before stopdate
    If the dates are identical, a one-element list is returned
    :param startdate: String of start date
    :param stopdate: String of stop date
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: List of strings, containing dates between start and stop, including the boundary dates
    """
    # This distinction is needed as this function is needed when setting up the analyzer-object.
    if analyzer is None and dateformat is not None:
        def str2datetime_lambda(date):
            return stringoperations.str2datetime(date, dateformat)

        def datetime2str_lambda(obj):
            return stringoperations.datetime2str(obj, dateformat)
    elif analyzer is not None:
        def str2datetime_lambda(date):
            return analyzer.str2datetime(date)

        def datetime2str_lambda(obj):
            return analyzer.datetime2str(obj)
    else:
        raise RuntimeError("Provide either an analyzer or a dateformat")

    # Convert to datetime objects:
    start = str2datetime_lambda(startdate)
    stop = str2datetime_lambda(stopdate)

    if start > stop:
        raise RuntimeError("startdate is after stopdate")

    dur = stop - start
    dur = dur.days + 1
    datelist = [0] * dur
    curdate = start
    for i in range(dur):
        datelist[i] = datetime2str_lambda(curdate)
        curdate += datetime.timedelta(days=1)
    return datelist


def check_date_order(datelist, analyzer, allow_ident_days=False):
    """Checks if a list of dates/times is in order.
    Returns false, if an empty list is supplied.
    :param datelist: list of strings of dates
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :param allow_ident_days: boolean, indicates if successive dates may be identical or not
    :return: True if the earliest date is in the beginning and list is ordered correctly
    """
    if len(datelist) == 0:
        return False
    # convert to datetime for handling:
    datelist_dt = [analyzer.str2datetime(x) for x in datelist]
    # Don't begin with the first element with the iteration:
    if allow_ident_days:
        return all(curr_date >= prev_date for prev_date, curr_date in zip(datelist_dt, datelist_dt[1:]))
    return all(curr_date > prev_date for prev_date, curr_date in zip(datelist_dt, datelist_dt[1:]))


def find_holes_in_dates(datelist, analyzer):
    """Finds holes in a set of dates.
    Returns an empty list if there are no holes (i.e., all dates are consecutive).
    :param datelist: List of strings of dates
    :param analyzer: Analyzer-object
    :return: List of missing dates (list of strings, or empty list)"""
    if len(datelist) == 0:
        return []
    if not isinstance(datelist, list) or not isinstance(datelist[0], str):
        raise RuntimeError("Datelist must be a list of strings.")
    if not check_date_order(datelist, analyzer, allow_ident_days=False):
        raise RuntimeError("Initial list has duplicate days, or is not in order. This is likely fishy...")
    list_full = create_datelist(datelist[0], datelist[-1], analyzer)
    list_missing = list(set(list_full) - set(datelist))
    return list_missing


def check_dates_consecutive(datelist, analyzer):
    """Checks if a list of dates contains consecutive dates (1-day increments)
    Returns false, if an empty list is supplied.
    :param datelist: List of strings of dates
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: True if the list of dates is consecutive. False otherwise.
    """
    if len(datelist) == 0:
        return False
    if len(datelist) == 1:
        return True
    datelist = [analyzer.str2datetime(x) for x in datelist]
    for i in range(len(datelist) - 1):
        nextday = datelist[i] + datetime.timedelta(days=1)
        if datelist[i + 1] != nextday:
            return False
    return True


def fuse_two_value_lists(datelist_full, dates_1_partial, vals_1_partial_groundtruth, dates_2_partial, vals_2_partial,
                         analyzer, zero_padding_past, zero_padding_future, discard_zeroes=True):
    """Fuses two lists of values together, e.g., combines transactions-prices with market-prices.
    Applies extrapolation, too, to cover the full date-list.
    First, the two lists are merged fully, and then cropped/extended to datelist_full
    :param datelist_full: The final list of dates that the merged list will cover.
    :param dates_1_partial: Dates of first partial list
    :param vals_1_partial_groundtruth: Values of first partial list. If both lists have values at the same date,
    this value is taken.
    :param dates_2_partial: Dates of second partial list
    :param vals_2_partial: Values of second partial list
    :param discard_zeroes: If True, there will be zeroes inserted when the partial lists are merged! Otherwise,
    data will be interpolated.
    :return: A single list with interpolated and extrapolated values that corresponds to datelist_full
    """
    # Create a dictionary of the lists. Note: This will always store the most recent index, if there are duplicates.
    dates_1_dict = {}
    for i, date in enumerate(dates_1_partial):
        dates_1_dict[date] = i
    dates_2_dict = {}
    for i, date in enumerate(dates_2_partial):
        dates_2_dict[date] = i

    start_1 = analyzer.str2datetime(dates_1_partial[0])
    stop_1 = analyzer.str2datetime(dates_1_partial[-1])
    start_2 = analyzer.str2datetime(dates_2_partial[0])
    stop_2 = analyzer.str2datetime(dates_2_partial[-1])

    # Find the earliest and the latest date; create a new datelist and iterate over this list to fully merge the lists
    # Then, further below, we crop the list to the desired range of datelist_full
    start_earliest = analyzer.datetime2str(min(start_1, stop_1, start_2, stop_2))
    stop_latest = analyzer.datetime2str(max(start_1, stop_1, start_2, stop_2))
    merge_list_full = create_datelist(start_earliest, stop_latest, analyzer)

    output = []
    date_output = []
    for _, date in enumerate(merge_list_full):
        val = 0.0
        if date in dates_1_dict:
            val = vals_1_partial_groundtruth[dates_1_dict[date]]
        elif date in dates_2_dict:  # If no entry in list 1, check list 2
            val = vals_2_partial[dates_2_dict[date]]
        if discard_zeroes is True and val > 1e-6:
            output.append(val)
            date_output.append(date)
        elif discard_zeroes is False:
            output.append(val)
            date_output.append(date)

    # Interpolate the given range to ensure there are no holes (e.g., if no zeroes were inserted above):
    date_out, out = interpolate_data(date_output, output, analyzer)
    # Now, date_output and output need to be extrapolated (or cropped) to cover the range of datelist_full.
    _, values_final = format_datelist(date_out, out, datelist_full[0], datelist_full[-1], analyzer,
                                      zero_padding_past=zero_padding_past, zero_padding_future=zero_padding_future)
    return values_final


def is_date_valid(datestring, dateformat):
    """Checks if the provided date-string is a valid date
    :param datestring: String of a date
    :param dateformat: Desired date-format
    :return True, if datestring adheres to dateformat
    """
    try:
        datetime.datetime.strptime(datestring, dateformat)
        return True
    except:
        return False
