"""Functions for handling the file-based marketdata-repository. Used by prices and forex

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import stringoperations
import dateoperations
import files
import helper


def update_check_marketdata_in_file(filepath, dateformat_marketdata, dateformat, marketdata_delimiter,
                                    newdates, newvals):
    """Imports data into a potentially available marketdata-file and if possible, cross-checks it with the dates in
    newdates, newvals.
    If the marketdata-file does not exist, it is created and populated with newdates, newvals. These values are
    then also returned.
    NEVER provide extrapolated data here, the market-files should only contain real data.
    If newdates, newvals contains new dates and values that do not yet exist in the existing marketdata-file,
    an updated version of the file is written. The values of the updated file are returned as tuple.
    The last second entries of the marketdata (the two most recent dates) are ignored when checking for matching data,
    since the daily data is end-of-day and might be extrapolated one day forward, which changes it...
    :param filepath: String of the path of the marketdata-file
    :param dateformat_marketdata: String of the dateformat used in the marketdata-file
    :param dateformat: String of the dateformat as used by the rest of the functions
    :param marketdata_delimiter: String of the delimiter used to separate dates, values in the marketdata-file
    :param newdates: New dates (strings) (with format dateformat) that are used to compare/update the file
    :param newvals: New values (floats) that are used to compare/update the file
    :return: The contents of the updated / newly created marketdata-file, as tuple: (dates, values); dates are
    Strings with the datetime-format.
    """
    # Sanity checks:
    if len(newdates) != len(newvals):
        raise RuntimeError("Length of date- and value-lists must be identical. Cannot update market-data. Path: "
                           + filepath)
    # Convert the newdates to datetime-objects and back, to be sure they are of the correct format:
    newdates_dt = [stringoperations.str2datetime(x, dateformat) for x in newdates]
    newdates = [stringoperations.datetime2str(x, dateformat) for x in newdates_dt]

    # Files does not yet exist: Create it and add the available data to it:
    if files.file_exists(filepath) is False:
        lines = []
        for idx, date in enumerate(newdates):
            # Assemble the line, comprising the date, delimiter and value
            string = date + marketdata_delimiter + repr(newvals[idx])
            lines.append(string)
        # Write the lines to the file. It will be newly created.
        try:
            files.write_file_lines(filepath, lines, overwrite=True)
        except:
            raise RuntimeError("Could not create/write new marketdata-file. Path: " + filepath)
        return newdates, newvals

    # There is already an existing marketdata-file:
    else:
        # Import the currently stored data from the marketdata-file:
        # The dates are already formatted in dateformat.
        mketdates_cur, mketprices_cur = import_marketdata_from_file(filepath, dateformat_marketdata, dateformat,
                                                                    marketdata_delimiter)

        # Crop the last two entries out of the list; it might change after a day, due to end-of-day data and/or
        # potential extrapolation. It will be re-added anyways further below.
        mketdates_cur = mketdates_cur[0:-3]
        mketprices_cur = mketprices_cur[0:-3]

        # Iterate over all lines of the marketdata-file and
        # check if stored values match with newdates,newvals (if possible)
        for idx, date_cur in enumerate(mketdates_cur):
            # Check, if the currently selected date is available in the newdates, too:
            indexes = [i for i, x in enumerate(newdates) if x == date_cur]
            # If it is available, check if it matches reasonably well with the stored value:
            if len(indexes) > 1:
                raise RuntimeError("The supplied list of new dates contains multiple identical dates. "
                                   "This is not allowed.")
            # The currently selected date is available in the new list (once, which is good): Check, if it matches:
            elif len(indexes) == 1:
                price_cur = mketprices_cur[idx]
                price_new = newvals[indexes[0]]
                # The values should match within 0.5% at least.
                if helper.within_tol(price_cur, price_new, 2.0 / 100.0) is False:
                    print("WARNING: The obtained market-price does not match with the recorded value. Path: " +
                          filepath + ". Line-Nr: " + repr(idx) + ". Recorded Value=" + repr(price_cur) +
                          ". New Value=" + repr(price_new) + ". Date: " + date_cur)

        # The obtained new values now match the existing values (if there are double entries), which is good.
        # In the following: the new values are sorted into the existing market-data, and the file is updated
        # These copies will be updated:
        mketdates_update_dt = [stringoperations.str2datetime(x, dateformat) for x in mketdates_cur]
        mketprices_update = list(mketprices_cur)
        for idx, newdate in enumerate(newdates):
            # Check, if the current new date exists somewhere in the market-data:
            indexes = [i for i, x in enumerate(mketdates_cur) if x == newdate]
            if len(indexes) > 1:
                raise RuntimeError("The supplied list of new dates contains multiple identical dates. "
                                   "This is not allowed.")
            # The current new date is not in the market-data-list: it can be inserted there!
            elif len(indexes) == 0:
                newdate_dt = stringoperations.str2datetime(newdate, dateformat)
                # Find the index, where it has to go:
                inserted = False
                for idxup, date_update in enumerate(mketdates_update_dt):
                    # Insert it according to the date:
                    if newdate_dt < date_update:
                        mketdates_update_dt.insert(idxup, newdate_dt)
                        mketprices_update.insert(idxup, newvals[idx])
                        inserted = True
                        break
                # At end of for-loop, it must be inserted, it then has the newest date:
                if inserted is False:
                    lastidx = len(mketdates_update_dt)  # It's relly the length, no -1 needed...
                    mketdates_update_dt.insert(lastidx, newdate_dt)
                    mketprices_update.insert(lastidx, newvals[idx])

        # Convert back to string-representation and check the consistency, to be sure nothing went wrong:
        mketdates_update = [stringoperations.datetime2str(x, dateformat) for x in mketdates_update_dt]
        if dateoperations.check_date_order(mketdates_update, dateformat, allow_ident_days=False) is False:
            raise RuntimeError("Something went wrong when updating the market-data. Path: " + filepath)

        # Write the updated data back into the file:
        lines = []
        for idx, date in enumerate(mketdates_update):
            # Assemble the line, comprising the date, delimiter and value
            string = date + marketdata_delimiter + repr(mketprices_update[idx])
            lines.append(string)
        # Write the lines to the file. It will be newly created.
        try:
            files.write_file_lines(filepath, lines, overwrite=True)
        except:
            raise RuntimeError("Could not overwrite existing marketdata-file. Path: " + filepath +
                               ". Maybe data has now been lost...?")
        # Return the updated full lists of all stored market data:
        return mketdates_update, mketprices_update


def import_marketdata_from_file(filepath, dateformat_marketdata, dateformat, marketdata_delimiter):
    """Imports recorded market-data from the specified file
    The dates are converted from dateformat_marketdata to dateformat, and returned as strings in the latter format
    :param filepath: String of the path of the file, where data is potentially available
    :param dateformat_marketdata: String of the dateformat of the marketdata
    :param dateformat: String of the dateformat as used by the rest of the scripts
    :param marketdata_delimiter: Delimiter used in the marketdata-files
    :return: Tuple of two lists: (dates, values) as imported from the specified files. Dates are strings in the
    dateformat. Values are floats.
    """
    if files.file_exists(filepath) is False:
        raise RuntimeError("Cannot import data, file not existing. Path: " + filepath)

    # Get all lines (as list) from the file:
    try:
        lines = files.get_file_lines(filepath)
    except:
        raise RuntimeError("Could not obtain lines from marketdata-file. Path: " + filepath)
    # Accumulate the dates and the values:
    datelist = []
    vallist = []
    for line in lines:
        # Get rid of all whitespaces in a line:
        stripline = stringoperations.strip_whitespaces(line)
        # Read the identifier, and also retain the value encoded after the delimiter:
        date, val = stringoperations.read_crop_string_delimited(stripline, marketdata_delimiter)
        # Convert the format of the dates:
        date_dt = stringoperations.str2datetime(date, dateformat_marketdata)
        date = stringoperations.datetime2str(date_dt, dateformat)
        val = float(val)
        datelist.append(date)
        vallist.append(val)

    # Sanity checks:
    if dateoperations.check_date_order(datelist, dateformat, allow_ident_days=False) is False:
        raise RuntimeError("The imported dates from the marketdata-file are not in order. They must be consecutive "
                           "and may not contain duplicates. Paht: " + filepath)

    return datelist, vallist


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    test = list(reversed(list(range(3))))
    print(test)

    # lis = [1, 2, 3, 4]
    # lis.insert(4, 8)
    # print(lis)
