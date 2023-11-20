"""Package for handling the file-based marketdata-repository

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import re
import stringoperations
import dateoperations
import files
import helper
from marketdata.forex.forex import ForexData
from marketdata.stock.stock import StockData
from marketdata.index.index import IndexData

# Layout/Todo:
"""
Fundamental principles: 
1) Ony consecutive dates allowed to be stored in marketdata-files. 
2) Some amount of interpolation is allowed. Defined on per-file basis via its header. 
3) Marketdata-files have precedent/are ground truth. 
4) Stock splits can optionally be given in header of stock-files. Read data will be adjusted accordingly (but no stored data is overwritten). Reason: Some data providers do not reflect splits; This allows to correct this. 
5) # Todo: Flag in header to allow overwrite of stored data from data provider? Reason: Change of provider? More flexibility?

 
Header-content: 
Stocks: Splits, Allowed interpolation
If splits are given, then the data, when further processed, is automatically adjusted according to the splits. # Todo document this in the docs, also the fact how the headers should look. 

Good input sanitization

# Todo: Continue here: 
# Data-retrieval of marketdata-objects: Enforce same behavior via ABC? How to match/find the range? String-search? What if the range is not available? Provide as much as possible, and provide missing dates?!
# Do this via a single function in marketdata, or in the sub-packages? Might make sense to do this in marketdata, as it is the same for all...

# Data-insertion: Append data at beginning or end. Prepare, though, for the option to overwrite data that is not matching, on a per-file basis!
"""


class MarketDataMain:
    """
    The content-format for forex- and stockmarket-index-files is as follows:
    Header;
    MAX_INTERPOLATION_DAYS; <N>
    Data;
    08.03.2020;1.434
    ...

    The content-format for stock price-files is as follows:
    Header;
    MAX_INTERPOLATION_DAYS; <N>
    Split;<date>;<float>
    Data;
    03.02.2020;134.30
    ...
    Note: The split-lines are optional. The split-value can be float. With this, reverse splits are also possible
    Normal splits have a split-factor >1. Reverse splits are <1.

    """
    DELIMITER = ";"
    EXTENSION = "csv"
    HEADER_STRING = "Header"
    DATA_STRING = "Data"
    SPLIT_STRING = "Split"
    INTERPOLATION_HEADER_STRING = "MAX_INTERPOLATION_DAYS"
    # forex + Symbol A + Symbol B:
    FORMAT_FOREX = r'^forex_[a-zA-Z0-9]{1,5}_[a-zA-Z0-9]{1,5}\.csv$'
    # stock + Symbol + Exchange + Currency:
    FORMAT_STOCK = r'^stock_[a-zA-Z0-9.]{1,10}_[a-zA-Z0-9.]{1,10}_[a-zA-Z0-9]{1,5}\.csv$'
    # index + Symbol:
    FORMAT_INDEX = r'^index_[a-zA-Z0-9.]{1,10}\.csv$'

    def __init__(self, path_to_storage_folder, dateformat, analyzer):
        self.storage_folder_path = path_to_storage_folder
        self.dateformat = dateformat
        self.analyzer = analyzer
        self.filesdict = {"stock": [], "index": [], "forex": []}
        self.forexobjects = []
        self.stockobjects = []
        self.indexobjects = []
        self.dataobjects = []

        print("Verifying all files in the marketstorage path")
        self.verify_and_read_storage()  # Reads _all_ stored files in the folder. For regular data-integrity checks.
        self.dataobjects = self.forexobjects + self.stockobjects + self.indexobjects

    def __is_string_valid_format(self, s, pattern):
        return bool(re.match(pattern, s))

    def __check_filenames(self, flist):
        for f in flist:
            if f[0:5] == "forex":
                if self.__is_string_valid_format(f, self.FORMAT_FOREX) is False:
                    raise RuntimeError("Misformatted string for " + f)
                self.filesdict["forex"].append(files.create_path(self.storage_folder_path, f))
            elif f[0:5] == "stock":
                if self.__is_string_valid_format(f, self.FORMAT_STOCK) is False:
                    raise RuntimeError("Misformatted string for " + f)
                self.filesdict["stock"].append(files.create_path(self.storage_folder_path, f))
            elif f[0:5] == "index":
                if self.__is_string_valid_format(f, self.FORMAT_INDEX) is False:
                    raise RuntimeError("Misformatted string for " + f)
                self.filesdict["index"].append(files.create_path(self.storage_folder_path, f))
            else:
                raise RuntimeError("Detected faulty file name in marketdata storage: " + f +
                                   ". File names must start with forex, stock or index")

    def __parse_forex_index_file(self, fname, is_index=False):
        lines = files.get_file_lines(fname)

        # Read the header:
        d_interp = None
        dates = []
        vals = []
        for line_nr, line in enumerate(lines):
            stripline = stringoperations.strip_whitespaces(line)
            if line_nr == 0:
                txt, _ = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.HEADER_STRING:
                    raise RuntimeError("File must start with Header-string. File: " + fname)
            elif line_nr == 1:
                txt, val = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.INTERPOLATION_HEADER_STRING:
                    raise RuntimeError("After Header, the value for max. "
                                       "interpolation days must follow. File: " + fname)
                try:
                    d_interp = int(val)
                except:
                    raise RuntimeError("Could not convert interpolation-days string to integer.")
            elif line_nr == 2:
                txt, _ = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.DATA_STRING:
                    raise RuntimeError("After max. interpolation days must follow data-string. File: " + fname)
            else:
                d, v = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if dateoperations.is_date_valid(d, self.dateformat) is True:
                    dates.append(d)
                    vals.append(float(v))
                else:
                    raise RuntimeError("Invalid date found! File: " + fname + ". Date: " + d)
        if len(dates) != len(vals):
            raise RuntimeError("Dates and values must have same length. File: " + fname)
        if dateoperations.check_dates_consecutive(dates, self.analyzer) is False:
            raise RuntimeError("The dates in a forex-storage file must be consecutive! There are dates missing.")
        if is_index is False:
            f = ForexData(fname, d_interp, (dates, vals))
        else:
            f = IndexData(fname, d_interp, (dates, vals))
        return f

    def __parse_stock_file(self, fname):
        lines = files.get_file_lines(fname)

        # Read the header:
        d_interp = None
        splits = []
        dates = []
        vals = []
        data_reached = False
        for line_nr, line in enumerate(lines):
            stripline = stringoperations.strip_whitespaces(line)
            if line_nr == 0:
                txt, _ = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.HEADER_STRING:
                    raise RuntimeError("File must start with Header-string. File: " + fname)
            elif line_nr == 1:
                txt, val = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.INTERPOLATION_HEADER_STRING:
                    raise RuntimeError("After Header, the value for max. "
                                       "interpolation days must follow. File: " + fname)
                try:
                    d_interp = int(val)
                except:
                    raise RuntimeError("Could not convert interpolation-days string to integer.")
            elif line_nr >= 2 and data_reached is False:  # Can be "SPLIT" or "Data"
                begin, rest = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if begin == self.SPLIT_STRING:
                    split_date, split_value = stringoperations.read_crop_string_delimited(rest, self.DELIMITER)
                    if dateoperations.is_date_valid(split_date, self.dateformat) is True:
                        splits.append((split_date, float(split_value)))
                    else:
                        raise RuntimeError("Invalid date found! File: " + fname + ". Date: " + split_date)
                elif begin == self.DATA_STRING:
                    data_reached = True
                else:
                    raise RuntimeError("After max. interpolation days must follow data- or split-string. "
                                       "File: " + fname)
            elif data_reached is True:
                d, v = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if dateoperations.is_date_valid(d, self.dateformat) is True:
                    dates.append(d)
                    vals.append(float(v))
                else:
                    raise RuntimeError("Invalid date found! File: " + fname + ". Date: " + d)
        if len(dates) != len(vals):
            raise RuntimeError("Dates and values must have same length. File: " + fname)
        if dateoperations.check_dates_consecutive(dates, self.analyzer) is False:
            raise RuntimeError("The dates in a stock-storage file must be consecutive! There are dates missing "
                               "or out of order. File: " + fname)
        f = StockData(fname, d_interp, (dates, vals), splits)
        return f

    def verify_and_read_storage(self):
        """ Check _all_ files in the storage folder for validity. Do this regularly to make sure the database
        is not getting corrupted.
        """
        f = files.get_file_list(self.storage_folder_path, self.EXTENSION)
        self.__check_filenames(f)  # This also fills the dictionary according to what they represent

        for file in self.filesdict["stock"]:
            self.stockobjects.append(self.__parse_stock_file(file))

        for file in self.filesdict["forex"]:
            self.forexobjects.append(self.__parse_forex_index_file(file, is_index=False))

        for file in self.filesdict["index"]:
            self.indexobjects.append(self.__parse_forex_index_file(file, is_index=True))

    def __get_marketdata_object(self, fname):
        """Checks if a marketdata file is available for a given file name, and returns the related object if available.
        Returns none, if the file/related data is not available.
        It searches for file-names, not path-names.
        """
        for obj in self.dataobjects:
            if obj.get_filename() == fname:
                return obj
        return None

    def __build_stock_filename(self, symbol, exchange, currency):
        return "stock_" + symbol + "_" + exchange + "_" + currency + ".csv"

    def __build_forex_filename(self, symbol_a, symbol_b):
        return "forex_" + symbol_a + "_" + symbol_b + ".csv"

    def __build_index_filename(self, indexname):
        return "index_" + indexname + ".csv"

    def get_marketdata_object(self, obj_type, symbols):
        if obj_type == "stock":
            symbol = symbols[0]
            exchange = symbols[1]
            currency = symbols[2]
            return self.__get_marketdata_object(self.__build_stock_filename(symbol, exchange, currency))
        elif obj_type == "forex":
            symbol_a = symbols[0]
            symbol_b = symbols[1]
            return self.__get_marketdata_object(self.__build_forex_filename(symbol_a, symbol_b))
        elif obj_type == "index":
            indexname = symbols[0]
            return self.get_marketdata_object(self.__build_index_filename(indexname))
        else:
            return RuntimeError("Object type not known. Must be stock, forex or index")


def update_check_marketdata_in_file(filepath, dateformat_marketdata, dateformat, marketdata_delimiter,
                                    newdates, newvals, analyzer):
    """Imports data into a potentially available marketdata-file and if possible, cross-checks it with the dates in
    newdates, newvals.
    If the marketdata-file does not exist, it is created and populated with newdates, newvals. These values are
    then also returned.
    NEVER provide extrapolated data here, the market-files should only contain real data.
    If newdates, newvals contains new dates and values that do not yet exist in the existing marketdata-file,
    an updated version of the file is written. The values of the updated file are returned as tuple.
    The last second entries of the marketdata (the two most recent dates) are ignored when checking for matching data,
    since the daily data is end-of-day and might be extrapolated one day forward, which changes it...
    It is assumed that the data in the marketdata-file is always correct and hence, this data is used. A warning is
    issued if mismatches are detected.
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
    newdates_dt = [analyzer.str2datetime(x) for x in newdates]
    newdates = [analyzer.datetime2str(x) for x in newdates_dt]

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
                                                                    marketdata_delimiter, analyzer)

        # Crop the last entry out of the list; it might change after a day, due to end-of-day data and/or
        # potential extrapolation. It will be re-added anyways further below by the data-source. But: Only do this if
        # there is sufficient data in the file (the dataprovider sometimes only provides data of a single day).
        if len(mketdates_cur) > 1:
            mketdates_cur = mketdates_cur[0:-1]
            mketprices_cur = mketprices_cur[0:-1]

        # Create a dictionary of the newdates to enable faster lookup. Note: Should newdates contain duplicates,
        # it will only store the most recent/latest value in the dict.
        newdates_dict = {}
        for i, date in enumerate(newdates):
            newdates_dict[date] = i

        # Iterate over all lines of the marketdata-file and
        # check if stored values match with newdates,newvals (if possible)
        # If not, a list of non-matching strings is output afterwards.
        discrepancy_entries = []
        for idx, date_cur in enumerate(mketdates_cur):
            # Check, if the currently selected date is available in newdates. Check if they match.
            if date_cur in newdates_dict:
                idx_new = newdates_dict[date_cur]
                price_cur = mketprices_cur[idx]
                price_new = newvals[idx_new]
                # The values should match within 2% at least.
                if helper.within_tol(price_cur, price_new, 2.0 / 100.0) is False:
                    # It is assumed that the marketdata-file is always correct:
                    newvals[idx_new] = price_cur
                    # Record a string for later output:
                    discrepancy_str = repr(date_cur) + ";\t" + repr(price_cur) + ";\t" + repr(
                        price_new)
                    discrepancy_entries.append(discrepancy_str)

        # Output the mismatching entries of the market data file:
        numentry = min(len(discrepancy_entries), 20)
        if len(discrepancy_entries) > 0:
            print(
                f"WARNING: {len(discrepancy_entries)} obtained market data entries do not match the recorded values (tolerance: 2%).")
            print("File: " + filepath + f". Entries (listing only first {numentry} elements):")
            print("Date;\t\tRecorded Price;\t\tObtained Price")
            for i in range(numentry):
                print(discrepancy_entries[i])

        # The obtained new values now match the existing values (if there are double entries), which is good.
        # In the following: the new values are sorted into the existing market-data, and the file is updated
        # These copies will be updated:
        mketdates_update_dt = [analyzer.str2datetime(x) for x in mketdates_cur]
        mketprices_update = list(mketprices_cur)

        mketdates_cur_dict = {}
        for i, date in enumerate(mketdates_cur):
            mketdates_cur_dict[date] = i

        for idx, newdate in enumerate(newdates):
            if newdate not in mketdates_cur_dict:
                # The current new date is not in the market-data-list: it can be inserted there!
                newdate_dt = analyzer.str2datetime(newdate)
                # Find the index, where it has to go:
                inserted = False
                for idxup, date_update in enumerate(mketdates_update_dt):  # Todo Is there a way to make this faster?
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
        mketdates_update = [analyzer.datetime2str(x) for x in mketdates_update_dt]
        if dateoperations.check_date_order(mketdates_update, analyzer, allow_ident_days=False) is False:
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


def import_marketdata_from_file(filepath, dateformat_marketdata, dateformat, marketdata_delimiter, analyzer):
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
    if dateoperations.check_date_order(datelist, analyzer, allow_ident_days=False) is False:
        raise RuntimeError("The imported dates from the marketdata-file are not in order. They must be consecutive "
                           "and may not contain duplicates. Paht: " + filepath)

    return datelist, vallist


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    storage_path = "../marketdata_storage"
    dateformat = "%d.%m.%Y"
    dtconverter = stringoperations.DateTimeConversion()
    import analysis

    analyzer = analysis.AnalysisRange("01.01.2020", "01.01.2023", dateformat, dtconverter)
    obj = MarketDataMain(storage_path, dateformat, analyzer)
