"""Implements functions related to handling dates and the corresponding data
Dates are transferred as lists of strings between different functions, for compatibility and maintainability reasons

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import datetime
import stringoperations


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


def format_datelist(datelist, vallist, begin_date, stop_date, dateformat, analyzer, zero_padding_past,
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


def interpolate_data(datelist_incompl, vallist_incompl, dateformat, analyzer):
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
    if check_date_order(datelist_incompl, analyzer, allow_ident_days=True) is False:
        raise RuntimeError("The incomplete date list is not in order.")
    if len(datelist_incompl) != len(vallist_incompl):
        raise RuntimeError("The incomplete lists must be of identical length.")
    if len(datelist_incompl) == 0:
        raise RuntimeError("Requires at least one value to be able to interpolate.")

    start = datelist_incompl[0]
    stop = datelist_incompl[-1]
    # The complete list of all dates:
    datelist_full = create_datelist(start, stop, dateformat)

    vallist_compl = []
    for date in datelist_full:  # Todo: Improve/speed this code up
        # Check, if the current date is in the incomplete list, and how many times it is there:
        indexes = [i for i, x in enumerate(datelist_incompl) if x == date]
        # Current date is not in the incomplete list: Extrapolation is required
        if not indexes:
            # There are already some values in the filled list: use the last value given
            if len(vallist_compl) > 0:
                vallist_compl.append(vallist_compl[-1])
            # No value has yet been found. Simply use the first value of the incomplete list, as it's closest.
            else:
                vallist_compl.append(vallist_incompl[0])
        # The current date is (at least once) in the incomplete list: take the last occurrence:
        else:
            vallist_compl.append(vallist_incompl[indexes[-1]])

    return datelist_full, vallist_compl


def extend_data_past(datelist, vallist, begin_date, analyzer, zero_padding):
    """Extends a list of dates and corresponding values into the past, until a specified date (included)
    :param datelist: List of strings of dates
    :param vallist: List of values, corresponding to the dates in datelist
    :param begin_date: String, encoding the date in the past until which the lists are extended backwards
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :param zero_padding: Boolean. If true: Values are extended with zeros. Otherwise, with the last
                        known value (zero-order hold)
    :return: Tuple of two lists: The extended list of dates (as strings) and the extended list of values:
    (dates, values)
    """
    # Use datetime (this also creates a local copy)
    datelist_dt = [analyzer.str2datetime(x) for x in datelist]
    begin_date_dt = analyzer.str2datetime(begin_date)
    stop_date_dt = datelist_dt[0]

    if begin_date_dt > datelist_dt[0]:
        raise RuntimeError("Begin-date is later than beginning of datelist. Cannot extrapolate into the past.")

    curdate = begin_date_dt
    auxdates = []
    auxvals = []
    # Create new lists, before the existing list. Then join the lists.
    while curdate < stop_date_dt:
        auxdates.append(curdate)
        if zero_padding is True:
            auxvals.append(0.0)
        else:
            auxvals.append(vallist[0])
        curdate += datetime.timedelta(days=1)
    datelist_dt = auxdates + datelist_dt
    vallist_extended = auxvals + vallist

    # Re-convert dates to strings:
    datelist_str = [analyzer.datetime2str(x) for x in datelist_dt]
    return datelist_str, vallist_extended


def extend_data_future(datelist, vallist, stop_date, analyzer, zero_padding):
    """Extends a list of dates and the corresponding list of values into the future, until a given date.
    Increment: 1-day steps
    :param datelist: List of strings encoding the given dates
    :param vallist: List of values, corresponding to the dates in datelist
    :param stop_date: String, encodes the desired end of the extended dates/values
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :param zero_padding: Boolean. If true: Values are extended with zeros. Otherwise, with the last
                        known value (zero-order hold)
    :return: Tuple of two lists: The extended list of dates (as strings) and the extended list of values:
    (dates, values)
    """
    # Sanity check:
    if len(datelist) != len(vallist):
        raise RuntimeError("List of dates and values must be of identical length.")

    # Use datetime (this also creates a local copy)
    datelist_dt = [analyzer.str2datetime(x) for x in datelist]
    stop_date_dt = analyzer.str2datetime(stop_date)

    if stop_date_dt <= datelist_dt[-1]:
        raise RuntimeError("Stop-date is not in the future of the given datelist.")

    # Create a local copy:
    vallist_extended = list(vallist)
    while datelist_dt[-1] < stop_date_dt:
        datelist_dt.append(datelist_dt[-1] + datetime.timedelta(days=1))  # Add a day
        if zero_padding is True:
            vallist_extended.append(0.0)
        else:
            vallist_extended.append(vallist_extended[-1])

    # Re-convert dates to strings:
    datelist_str = [analyzer.datetime2str(x) for x in datelist_dt]
    return datelist_str, vallist_extended


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
    else:
        # Strip the exact time of the day, such that only the desired date-format remains.
        today = stringoperations.datetime2str(today, dateformat)
        return stringoperations.str2datetime(today, dateformat)


def create_datelist(startdate, stopdate, dateformat):
    """Takes two dates (as strings) and creates a list of days (strings) between (including) these dates.
    Granularity: day (step size between dates)
    startdate must be before stopdate
    If the dates are identical, a one-element list is returned
    :param startdate: String of start date
    :param stopdate: String of stop date
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: List of strings, containing dates between start and stop, including the boundary dates
    """
    # Convert to datetime objects:
    start = stringoperations.str2datetime(startdate, dateformat)
    stop = stringoperations.str2datetime(stopdate, dateformat)

    if start > stop:
        raise RuntimeError("startdate is after stopdate")

    datelist = []
    curdate = start
    while curdate <= stop:
        datelist.append(stringoperations.datetime2str(curdate, dateformat))
        curdate += datetime.timedelta(days=1)

    return datelist


def check_date_order(datelist, analyzer, allow_ident_days):
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
    oldday = datelist_dt[0]
    for date in datelist_dt[1:]:
        if allow_ident_days is True:
            if date < oldday:
                return False
        else:
            if date <= oldday:
                return False
        oldday = date
    return True


def check_dates_consecutive(datelist, analyzer):
    """Checks if a list of dates contains consecutive dates (1-day increments)
    Returns false, if an empty list is supplied.
    :param datelist: List of strings of dates
    :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
    :return: True if the list of dates is consecutive. False otherwise.
    """
    if len(datelist) == 0:
        return False
    # Convert to datetime for handling:
    datelist = [analyzer.str2datetime(x) for x in datelist]
    for i, date in enumerate(datelist):
        nextday = date + datetime.timedelta(days=1)
        if i < len(datelist) - 1:
            if datelist[i + 1] != nextday:
                return False
    return True


def fuse_two_value_lists(datelist_full, dates_1_partial, vals_1_partial_groundtruth, dates_2_partial, vals_2_partial,
                         dateformat, analyzer, zero_padding_past, zero_padding_future):
    """Fuses two lists of values together, e.g., combines transactions-prices with market-prices.
    Applies extrapolation, too, to cover the full date-list.
    Note that zero-values are discarded!
    :param datelist_full: The full list of dates that the merged list will cover.
    :param dates_1_partial: Dates of first partial list
    :param vals_1_partial_groundtruth: Values of first partial list. If both lists have values at the same date,
    this value is taken.
    :param dates_2_partial: Dates of second partial list
    :param vals_2_partial: Values of second partial list
    :return: A single list with interpolated and extrapolated values that corresponds to datelist_full
    """
    output = []
    date_output = []
    for idx, date in enumerate(datelist_full):  # Todo speed this code up
        indexes_1 = [i for i, x in enumerate(dates_1_partial) if x == date]
        if len(indexes_1) > 1:
            # raise RuntimeError("There seem to be multiple dates. This seems wrong...") This is actually OK: Multiple
            # transactions can be recorded for the same day. Use the most recent value.
            pass
        elif len(indexes_1) >= 1:  # Match found: Use it, but find the non-zero value (mult. actions on the same day...)
            val_max = 0.0  # Simply use the largest value
            for i, idx in enumerate(indexes_1):
                if vals_1_partial_groundtruth[idx] > val_max:
                    val_max = vals_1_partial_groundtruth[idx]
            if val_max > 1e-6:  # The transactions-data also contains zero-values for price. Ignore those.
                output.append(val_max)
                date_output.append(date)
        else:  # No match found: Check the other list:
            indexes_2 = [i for i, x in enumerate(dates_2_partial) if x == date]
            if len(indexes_2) > 1:
                raise RuntimeError("There seem to be multiple dates. "
                                   "This seems wrong (this is the online market list)...")
            elif len(indexes_2) == 1 and vals_2_partial[indexes_2[0]] > 1e-6:
                output.append(vals_2_partial[indexes_2[0]])
                date_output.append(date)
            else:  # Also no match found ==> Needs to be extrapolated below.
                pass
    # Interpolate the given range to ensure there are no holes:
    date_out, out = interpolate_data(date_output, output, dateformat, analyzer)
    # Now, date_output and output need to be extrapolated (or cropped) to cover the range of datelist_full.
    _, values_final = format_datelist(date_out, out, datelist_full[0], datelist_full[-1], dateformat, analyzer,
                                      zero_padding_past=zero_padding_past, zero_padding_future=zero_padding_future)
    return values_final


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    # print(check_date_order(["01.01.2017", "01.01.2017", "02.03.2018"], "%d.%m.%Y", False))
    # print(create_datelist("01.01.2018", "10.01.2018", "%d.%m.%Y"))
    # print(check_dates_consecutive(["01.01.2019", "03.01.2017", "04.01.2017", "05.01.2017"], "%d.%m.%Y"))

    datelist = ["02.01.2010", "02.01.2010", "03.01.2010", "05.01.2010", "05.01.2010"]
    datelist_incompl = ["01.01.2010"]
    vallist_incompl = [3]
    vallist = [1, 2, 3, 4, 5]
    begin_date = "03.01.2009"
    stop_date = "03.01.2010"
    dateformat = "%d.%m.%Y"

    print(repr(check_date_order(datelist, dateformat, allow_ident_days=True)))

    # date, data = extend_data_future(datelist, vallist, stop_date, dateformat)

    # date, data = format_datelist(datelist, vallist, begin_date, stop_date, dateformat,
    #                             zero_padding_past = False, zero_padding_future = False)
    # print(date)
    # print(data)

    # filled = fill_data(datelist, datelist_incompl, vallist_incompl, dateformat)
    # print(filled)

    # print(get_date_today(dateformat))

    # crop_dates, crop_vals = interpolate_data(datelist_incompl, vallist_incompl, dateformat)

    # crop_dates, crop_vals = crop_datelist(datelist, vallist, begin_date, stop_date, dateformat)
    # print(crop_dates)
    # print(crop_vals)

    # dates_ext, vals_ext = extend_data_past(datelist, vallist, "28.3.2018", dateformat)
    # dates_ext, vals_ext = extend_data_today(datelist, vallist, dateformat)
    # print(datelist)
    # print(vallist)
    # print(dates_ext)
    # print(vals_ext)
