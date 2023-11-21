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
from storage.forex.forex import ForexData
from storage.stock.stock import StockData
from storage.index.index import IndexData

# Layout/Todo:
"""
Fundamental principles: 
1) It is OK for "holes" to be stored in the market data, i.e., data must not be consecutive. 
2) Some amount of interpolation is allowed. Defined on per-file basis via its header. # Todo: Is this already implemented? Where would this come into play? 
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
    MAX_INTERPOLATION_DAYS;<N>
    Data;
    08.03.2020;1.434
    ...

    The content-format for stock price-files is as follows:
    Header;
    MAX_INTERPOLATION_DAYS;<N>
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
    DEFAULT_INTERPOLATION_DAYS = 5
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
        self.forexobjects = []  # Todo are these needed, or is dataobjects sufficient?
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
                ret = self.__read_data_line_from_storage_file(stripline)
                if ret is None:
                    raise RuntimeError(f"Invalid date found! File: {fname}. Date: {d}")
                d, v = ret
                dates.append(d)
                vals.append(v)

        if len(dates) != len(vals):
            raise RuntimeError("Dates and values must have same length. File: " + fname)
        if dateoperations.check_dates_order(dates, self.analyzer, allow_ident_days=False) is False and len(dates) > 0:
            raise RuntimeError(f"The dates in a forex-storage file must be in order! File: {fname}")
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
                ret = self.__read_data_line_from_storage_file(stripline)
                if ret is None:
                    raise RuntimeError(f"Invalid date found! File: {fname}. Date: {d}")
                d, v = ret
                dates.append(d)
                vals.append(v)

        if len(dates) != len(vals):
            raise RuntimeError("Dates and values must have same length. File: " + fname)
        if dateoperations.check_dates_order(dates, self.analyzer, allow_ident_days=False) is False and len(dates) > 0:
            raise RuntimeError(f"The dates in a stock-storage file must be in order! File: {fname}")
        f = StockData(fname, d_interp, (dates, vals), splits)
        return f

    def __read_data_line_from_storage_file(self, line):
        """Read a single data-line from the stored csv and run some checks.
        Return date and value for the given line."""
        # Read the identifier, and also retain the value encoded after the delimiter:
        date, val = stringoperations.read_crop_string_delimited(line, self.DELIMITER)
        # Sanity-check the date:
        try:
            date_dt = self.analyzer.str2datetime(date)
            date = self.analyzer.datetime2str(date_dt)
            val = float(val)
        except:
            return None
        if dateoperations.is_date_valid(date, self.dateformat) is False:
            return None
        return date, val

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

    def get_stored_data(self, storage_obj, interval):
        """Obtains stored data. The interval (tuple of start/stop date strings) must be within the data-range
        that is stored
        :param interval: Tuple of startdate-stopdate strings
        :return: List of values that correspond to the desired interval"""
        startdate, stopdate = interval
        dates_dict = storage_obj.get_dates_dict()
        dates_list = storage_obj.get_dates_list()
        values = storage_obj.get_values()

        try:
            startidx = dates_dict[startdate]
            stopidx = dates_dict[stopdate]
        except KeyError:
            return None

        if stopidx < startidx:
            return None

        return (dates_list[startidx:stopidx + 1], values[startidx:stopidx + 1])

    def get_start_stopdate(self, storage_obj):
        return (storage_obj.get_startdate, storage_obj.get_stopdate)

    def is_storage_data_existing(self, obj_type, symbols):
        """Checks, if a market-data storage file/object is existing. If yes, it returns it. Else: None.
        :param obj_type: String of the desired object-type. stock, forex or index
        :param symbols: List of object-dependent strings to characterize it
        :return storage-object if existing, else, None"""
        if obj_type == "stock":
            symbol = symbols[0]
            exchange = symbols[1]
            currency = symbols[2]
            fn = self.__build_stock_filename(symbol, exchange, currency)
        elif obj_type == "forex":
            symbol_a = symbols[0]
            symbol_b = symbols[1]
            fn = self.__build_forex_filename(symbol_a, symbol_b)
        elif obj_type == "index":
            indexname = symbols[0]
            fn = self.__build_index_filename(indexname)
        else:
            return RuntimeError("Object type not known. Must be stock, forex or index")

        for obj in self.dataobjects:
            if obj.get_filename() == fn:
                return obj
        return None

    def __create_storage_file_header(self, obj_type, symbols):
        """Create the appropriate file header. Populate with default values. Returns the filename, too."""
        if obj_type == "stock":
            symbol = symbols[0]
            exchange = symbols[1]
            currency = symbols[2]
            fn = self.__build_stock_filename(symbol, exchange, currency)
        elif obj_type == "forex":
            symbol_a = symbols[0]
            symbol_b = symbols[1]
            fn = self.__build_forex_filename(symbol_a, symbol_b)
        elif obj_type == "index":
            indexname = symbols[0]
            fn = self.__build_index_filename(indexname)
        else:
            return RuntimeError("Object type not known. Must be stock, forex or index")
        lines = []
        lines.append(f"{self.HEADER_STRING}{self.DELIMITER}")
        lines.append(f"{self.INTERPOLATION_HEADER_STRING}{self.DELIMITER}{self.DEFAULT_INTERPOLATION_DAYS:d}")
        lines.append(f"{self.DATA_STRING}")
        return fn, lines

    def create_new_storage_file(self, obj_type, symbols):
        fn, lines = self.__create_storage_file_header(obj_type, symbols)
        fp = files.create_path(self.storage_folder_path, fn)
        if files.file_exists(fp) is True:
            raise RuntimeError("File already exists! This should not happen at this point.")
        try:
            files.write_file_lines(fp, lines, overwrite=True)
        except Exception:
            raise RuntimeError(f"Could not create/write new marketdata-file. Path: {fp}")

    def fuse_storage_and_provider_data(self, storage_obj, new_data, tolerance_percent=3.0, storage_is_groundtruth=True):
        """Take data from the provider. Merge/match it with the available data from storage. Return the fused
        data for further processing.
        """
        new_dates, new_values = new_data
        csv_dates = storage_obj.get_dates_list()
        csv_values = storage_obj.get_values()
        if len(new_dates) != len(new_values):
            raise RuntimeError("Dates and values must be of identical length.")
        # Todo: What happens if we have empty lists? Is it robust?

        # Create a dictionary of the new dates to enable faster lookup. Note: Should the new dates contain duplicates,
        # it will only store the most recent/latest value in the dict. This is fine.
        new_dates_dict = helper.create_dict_from_list(new_dates)

        # Create a copy, merge new_data into these lists further below.
        dates_merged = list(csv_dates)
        values_merged = list(csv_values)
        # Iterate over all entries of the storage and check if stored values match with the new ones.
        # If not, a list of non-matching strings is output afterwards.
        discrepancy_entries = []
        for idx, date_cur in enumerate(csv_dates):
            # Check, if the currently selected date is available in new_dates. Check if they match.
            if date_cur in new_dates_dict:
                idx_new = new_dates_dict[date_cur]
                price_csv = csv_values[idx]
                price_new = new_values[idx_new]
                # The values should match within the given tolerance.
                if helper.within_tol(price_csv, price_new, tolerance_percent / 100.0) is False:
                    if storage_is_groundtruth is True:
                        new_values[idx_new] = price_csv  # Adjust provider data to existing data
                    else:
                        values_merged[idx] = price_new # Take the new/provider-data
                    # Record a string for later output:
                    discrepancy_entries.append(f"{date_cur};\t{price_cur:.3f};\t{price_new:.3f}")

        # Output the mismatching entries of the market data file:
        numentry = min(len(discrepancy_entries), 20)
        if len(discrepancy_entries) > 0:
            print(f"WARNING: {len(discrepancy_entries)} obtained storage data entries do not match the recorded values "
                  f"(tolerance is set to: {tolerance_percent:.1f}%).")
            print(f"Storage data is ground truth is set to: {storage_is_groundtruth}")
            print(f"File: {storage_obj.get_filename()}. Entries (listing only first {numentry} elements):")
            print(f"Date;\tRecorded Price;\tObtained Price")
            for i in range(numentry):
                print(discrepancy_entries[i])

        # In the following: the new values are sorted into the existing storage-data
        dates_merged_dt = [self.analyzer.str2datetime(x) for x in dates_merged]
        csv_dates_dict = storage_obj.get_dates_dict()

        # Iterate over all new provider-data and sort it into the merged list:
        for idx, newdate in enumerate(new_dates):
            if newdate not in csv_dates_dict: # The current new date is not in the market-data-list: it can be inserted!
                newdate_dt = self.analyzer.str2datetime(newdate)
                # Find the index, where it has to go:
                inserted = False
                for idxup, date_update in enumerate(dates_merged_dt):  # Todo Is there a way to make this faster?
                    # Insert it according to the date:
                    if newdate_dt < date_update:
                        dates_merged_dt.insert(idxup, newdate_dt)
                        values_merged.insert(idxup, new_values[idx])
                        inserted = True
                        break
                # At end of for-loop, it must be inserted, as it has the newest date:
                if inserted is False:
                    lastidx = len(dates_merged_dt)
                    dates_merged_dt.insert(lastidx, newdate_dt)
                    values_merged.insert(lastidx, new_values[idx])

        # Convert back to string-representation and check the consistency, to be sure nothing went wrong:
        dates_merged = [self.analyzer.datetime2str(x) for x in dates_merged_dt]
        if dateoperations.check_date_order(dates_merged, self.analyzer, allow_ident_days=False) is False:
            raise RuntimeError(f"Something went wrong when fusing the data. Path: {storage_obj.get_filename()}")
        return dates_merged, values_merged


    def write_data_to_storage(self, storage_obj, data):
        """New (and existing) data is written to storage, i.e., the data is extended with the new data that was
        obtained by the data provider."""

        if files.file_exists(storage_obj.get_pathname()) is False:
            raise RuntimeError("File must already exist!")

        # Read the existing file's header into memory.
        lines_to_write = []
        lines_csv = files.get_file_lines(storage_obj.get_pathname())
        # Copy the header. The header stops at self.DATA_STRING
        for line_nr, line in enumerate(lines_csv):
            stripline = stringoperations.strip_whitespaces(line)
            txt, _ = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
            if txt == self.DATA_STRING:
                lines_to_write.append(stripline)
                break
            lines_to_write.append(stripline) # Todo: Check if this works

        dates, values = data
        if len(dates) != len(values):
            raise RuntimeError("Data and values must be of equal length")

        for idx, date in enumerate(dates):
            if dateoperations.is_date_valid(date, self.dateformat) is False:
                raise RuntimeError("Can not write faulty-formatted string to file")
            lines_to_write.append(f"{date}{self.DELIMITER}{values[idx]:.3f}")

        # Write the file:
        try:
            files.write_file_lines(storage_obj.get_pathname(), lines_to_write, overwrite=True)
        except:
            raise RuntimeError(f"Could not overwrite storage-file. Path: {storage_obj.get_pathname()}")
