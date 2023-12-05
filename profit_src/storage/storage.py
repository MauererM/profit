"""Package for handling the file-based marketdata-repository

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import re
import logging
import bisect
from pathlib import Path
from .. import stringoperations
from .. import dateoperations
from .. import files
from .. import helper
from ..storage.forex.forex import ForexData
from ..storage.stock.stock import StockData
from ..storage.index.index import IndexData


class MarketDataMain:
    """
    Fundamental principles:
    1) The data stored must not necessarily be contiguous (but in order). There can be "holes" in the data. However,
    whenever a hole is detected, the timedomain-class(es) will pull the full range from the provider,
    as it can not yet pull data granularly. Todo: Implement this at some point as well, if it is desired to pull
    less data from the provider(s).
    2) Marketdata-files have precedent/are ground truth, but they have a header-setting that allows to override this.
    3) Stock splits can optionally be given in header of stock-files. If this is done, then only data pulled from the
    provider will be modified accordingly (and stored data is not modified). Hence, the header in the storage file
    indicates that the related provider-data needs adjustment.
    Reason: Some data providers do not reflect splits; This allows to correct this.
    If a split is present in the storage-header, then the corresponding _provider_ data will be adjusted (and not the
    stored csv-data!).

    Note: The split-lines are optional. The split-value can be float. With this, reverse splits are also possible
    Normal splits have a split-factor >1. Reverse splits are <1.
    CAREFUL: Once the split-data is given in the header, any data from the corresponding provider will be modified and
    written to the file (where it then becomes ground-truth).
    NOTE: If you introduce or modify a new split in a storage-csv-file, you MUST delete all content fo the file (but keep
    the header!). This forces profit to re-pull all data from the provider, and apply the split.
    Alternatively, one can set the Overwrite_storage flag to "True", which overwrites data in the csv file with the new
    (and split-adjusted) provider data).
    You also might have to play with the day of the split in the storge-header by +/- 1 day to match the
    recorded transactions.

    The content-format for forex- and stockmarket-index-files is as follows:
    Header;
    Id;<Name>
    Overwrite_storage;<True/False>
    Data;
    08.03.2020;1.434
    ...

    The content-format for stock price-files is as follows:
    Header;
    Id;<Name>
    Overwrite_storage;<True/False>
    Split;<date>;<float>
    Data;
    03.02.2020;134.30
    ...
    """
    DELIMITER = ";"
    EXTENSION = "csv"
    HEADER_STRING = "Header"
    DATA_STRING = "Data"
    OVERWRITE_STRING = "Overwrite_storage"
    OVERWRITE_TRUE = "True"
    OVERWRITE_FALSE = "False"
    SPLIT_STRING = "Split"
    ID_STRING = "Id"
    # File names:
    # forex + Symbol A + Symbol B:
    FORMAT_FOREX = r'^forex_[a-zA-Z0-9]{1,5}_[a-zA-Z0-9]{1,5}\.csv$'
    # stock + Symbol + Exchange + Currency:
    FORMAT_STOCK = r'^stock_[a-zA-Z0-9.]{1,15}_[a-zA-Z0-9.]{1,15}_[a-zA-Z0-9]{1,5}\.csv$'
    # index + Symbol:
    FORMAT_INDEX = r'^index_[a-zA-Z0-9.\^]{1,10}\.csv$'

    def __init__(self, path_to_storage_folder, dateformat, analyzer):
        if not isinstance(path_to_storage_folder, Path):
            path_to_storage_folder = Path(path_to_storage_folder)
        self.storage_folder_path = path_to_storage_folder
        self.dateformat = dateformat
        self.analyzer = analyzer
        self.filesdict = {"stock": [], "index": [], "forex": []}
        self.dataobjects = []

        print("Verifying all files in the marketstorage path")
        self.verify_and_read_storage()  # Reads _all_ stored files in the folder. For regular data-integrity checks.

    def __is_string_valid_format(self, s, pattern):
        return bool(re.match(pattern, s))

    def __check_filenames(self, flist):
        if isinstance(flist, list) is False:  # Allows passing single strings
            flist = [flist]
        fnames = [x.name for x in flist]  # Convert to strings
        for f in fnames:
            if f[0:5] == "forex":
                if self.__is_string_valid_format(f, self.FORMAT_FOREX) is False:
                    raise RuntimeError(f"Misformatted string for {f}")
                self.filesdict["forex"].append(self.storage_folder_path.joinpath(f))
            elif f[0:5] == "stock":
                if self.__is_string_valid_format(f, self.FORMAT_STOCK) is False:
                    raise RuntimeError(f"Misformatted string for {f}")
                self.filesdict["stock"].append(self.storage_folder_path.joinpath(f))
            elif f[0:5] == "index":
                if self.__is_string_valid_format(f, self.FORMAT_INDEX) is False:
                    raise RuntimeError(f"Misformatted string for {f}")
                self.filesdict["index"].append(self.storage_folder_path.joinpath(f))
            else:
                raise RuntimeError(f"Detected faulty file name in marketdata storage: {f}."
                                   f"File names must start with forex, stock or index.")

    def __parse_forex_index_file(self, fname, is_index=False):
        lines = files.get_file_lines(fname)
        # Read the header:
        id_ = None
        overwrite_flag = None
        dates = []
        vals = []
        for line_nr, line in enumerate(lines):
            stripline = stringoperations.strip_whitespaces(line)
            if line_nr == 0:
                txt, _ = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.HEADER_STRING:
                    raise RuntimeError(f"File must start with Header-string. File: {fname}")
            elif line_nr == 1:
                txt, val = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.ID_STRING:
                    raise RuntimeError(f"After the Header-string, the Id-string must follow. File: {fname}")
                id_ = val
            elif line_nr == 2:
                txt, val = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.OVERWRITE_STRING:
                    raise RuntimeError(f"After the Id-string must follow the Overwrite-flag string. File: {fname}")
                if val == self.OVERWRITE_TRUE:
                    overwrite_flag = True
                elif val == self.OVERWRITE_FALSE:
                    overwrite_flag = False
                else:
                    raise RuntimeError(f"The overwrite-storage flag must be '{self.OVERWRITE_TRUE}' or "
                                       f"'{self.OVERWRITE_FALSE}'")
            elif line_nr == 3:
                txt, _ = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.DATA_STRING:
                    raise RuntimeError(f"After the Overwrite-flag string must follow the data-string. File: {fname}")

            else:
                ret = self.__read_data_line_from_storage_file(stripline)
                if ret is None:
                    raise RuntimeError(f"Invalid date found! File: {fname}. Date: {d}")
                d, v = ret
                dates.append(d)
                vals.append(v)

        if len(dates) != len(vals):
            raise RuntimeError(f"Dates and values must have same length. File: {fname}")
        if dateoperations.check_date_order(dates, self.analyzer, allow_ident_days=False) is False and len(
                dates) > 0:
            raise RuntimeError(f"The dates in a stock-storage file must be in order! File: {fname}. Data corrupted?")
        holes = dateoperations.find_holes_in_dates(dates, self.analyzer)
        if is_index is False:
            f = ForexData(fname, id_, (dates, vals), holes, overwrite_flag)
        else:
            f = IndexData(fname, id_, (dates, vals), holes, overwrite_flag)
        return f

    def __parse_stock_file(self, fname):
        lines = files.get_file_lines(fname)
        # Read the header:
        id_ = None
        splits = []
        dates = []
        vals = []
        overwrite_flag = None
        data_reached = False
        for line_nr, line in enumerate(lines):
            stripline = stringoperations.strip_whitespaces(line)
            if line_nr == 0:
                txt, _ = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.HEADER_STRING:
                    raise RuntimeError(f"File must start with Header-string. File: {fname}")
            elif line_nr == 1:
                txt, val = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.ID_STRING:
                    raise RuntimeError(f"After Header, the Id-string must follow. File: {fname}")
                id_ = val
            elif line_nr == 2:
                txt, val = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if txt != self.OVERWRITE_STRING:
                    raise RuntimeError(f"After the Id-string must follow the Overwrite-flag string. File: {fname}")
                if val == self.OVERWRITE_TRUE:
                    overwrite_flag = True
                elif val == self.OVERWRITE_FALSE:
                    overwrite_flag = False
                else:
                    raise RuntimeError(f"The overwrite-storage flag must be '{self.OVERWRITE_TRUE}' or "
                                       f"'{self.OVERWRITE_FALSE}'")
            elif line_nr >= 3 and data_reached is False:  # Can be "SPLIT" or "Data"
                begin, rest = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
                if begin == self.SPLIT_STRING:
                    split_date, split_value = stringoperations.read_crop_string_delimited(rest, self.DELIMITER)
                    if dateoperations.is_date_valid(split_date, self.dateformat) is True:
                        splits.append((split_date, float(split_value)))
                    else:
                        raise RuntimeError(f"Invalid date found! File: {fname}. Date: {split_date}")
                elif begin == self.DATA_STRING:
                    data_reached = True
                else:
                    raise RuntimeError(f"After the Overwrite-flag string must follow data- or split-string(s). "
                                       f"File: {fname}")
            elif data_reached is True:
                ret = self.__read_data_line_from_storage_file(stripline)
                if ret is None:
                    raise RuntimeError(f"Invalid date found! File: {fname}. Date: {d}")
                d, v = ret
                dates.append(d)
                vals.append(v)

        if len(dates) != len(vals):
            raise RuntimeError(f"Dates and values must have same length. File: {fname}")
        if dateoperations.check_date_order(dates, self.analyzer, allow_ident_days=False) is False and len(dates) > 0:
            raise RuntimeError(f"The dates in a stock-storage file must be in order! File: {fname}. Data corrupted?")
        if id_ is None:
            raise RuntimeError(f"The Id should have been read. File: {fname}")
        holes = dateoperations.find_holes_in_dates(dates, self.analyzer)
        f = StockData(fname, id_, (dates, vals), splits, holes, overwrite_flag)
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
            self.dataobjects.append(self.__parse_stock_file(file))

        for file in self.filesdict["forex"]:
            self.dataobjects.append(self.__parse_forex_index_file(file, is_index=False))

        for file in self.filesdict["index"]:
            self.dataobjects.append(self.__parse_forex_index_file(file, is_index=True))

    def __build_stock_filename(self, symbol, exchange, currency):
        p = f"stock_{symbol}_{exchange}_{currency}.csv"
        return Path(p)

    def __build_forex_filename(self, symbol_a, symbol_b):
        p = f"forex_{symbol_a}_{symbol_b}.csv"
        return Path(p)

    def __build_index_filename(self, indexname):
        p = f"index_{indexname}.csv"
        return Path(p)

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
        """Returns None if the storage object does not (yet) contain data. """
        return (storage_obj.get_startdate(), storage_obj.get_stopdate())

    def is_storage_data_existing(self, obj_type, symbols):
        """Checks, if a market-data storage file/object is existing. If yes, it returns it. Else: None.
        Existence is checked via the ID-string within the files.
        :param obj_type: String of the desired object-type. stock, forex or index
        :param symbols: List of object-dependent strings to characterize it
        :return storage-object if existing, else, None"""
        if obj_type == "stock":
            id_ = symbols[0]
        elif obj_type == "forex":
            symbol_a = symbols[0]
            symbol_b = symbols[1]
            id_ = f"{symbol_a}_{symbol_b}"
        elif obj_type == "index":
            id_ = symbols
        else:
            return RuntimeError("Object type not known. Must be stock, forex or index")

        for obj in self.dataobjects:
            if obj.get_id() == id_:
                return obj
        return None

    def __create_storage_file_header(self, obj_type, symbols):
        """Create the appropriate file header. Populate with default values. Returns the filename, too."""
        if obj_type == "stock":
            id_ = symbols[0]
            symbol_clean = files.clean_string(id_)
            exchange = symbols[1]
            currency = symbols[2]
            fn = self.__build_stock_filename(symbol_clean, exchange, currency)
        elif obj_type == "forex":
            symbol_a = symbols[0]
            symbol_b = symbols[1]
            id_ = f"{symbol_a}_{symbol_b}"
            fn = self.__build_forex_filename(symbol_a, symbol_b)
        elif obj_type == "index":
            id_ = symbols
            indexname = files.clean_string(id_)
            fn = self.__build_index_filename(indexname)
        else:
            return RuntimeError("Object type not known. Must be stock, forex or index")
        lines = []
        lines.append(f"{self.HEADER_STRING}{self.DELIMITER}")
        lines.append(f"{self.ID_STRING}{self.DELIMITER}{id_}")
        lines.append(f"{self.OVERWRITE_STRING}{self.DELIMITER}{self.OVERWRITE_FALSE}")
        lines.append(f"{self.DATA_STRING}{self.DELIMITER}")
        return fn, lines

    def create_new_storage_file(self, obj_type, symbols):
        fn, lines = self.__create_storage_file_header(obj_type, symbols)
        fp = self.storage_folder_path.joinpath(fn)
        if files.file_exists(fp) is True:
            raise RuntimeError(f"File already exists! This should not happen at this point. Path: {fp}. Note: "
                               f"filenames are derived from the symbols, but stripped of special characters. Could"
                               f"this lead to the creation of identical filenames from assets with differing IDs?")
        try:
            files.write_file_lines(fp, lines, overwrite=True)
        except Exception:
            raise RuntimeError(f"Could not create/write new marketdata-file. Path: {fp}. Is the folder existing?")

        self.__check_filenames(fn)  # adds it also to the dict. Don't pass the path
        if obj_type == "stock":
            obj = self.__parse_stock_file(fp)
        elif obj_type == "forex":
            obj = self.__parse_forex_index_file(fp, is_index=False)
        elif obj_type == "index":
            obj = self.__parse_forex_index_file(fp, is_index=True)
        else:
            return RuntimeError("Object type not known. Must be stock, forex or index")
        self.dataobjects.append(obj)
        return obj

    def fuse_storage_and_provider_data(self, storage_obj, new_data, tolerance_percent=3.0):
        """Take data from the provider. Merge/match it with the available data from storage. Return the fused
        data for further processing.
        """
        # If overwrite_storage is True, then storage is not ground truth anymore
        storage_is_groundtruth = not storage_obj.get_overwrite_flag()

        new_dates, new_values = new_data
        csv_dates = storage_obj.get_dates_list()
        csv_values = storage_obj.get_values()
        if len(new_dates) != len(new_values):
            raise RuntimeError("Dates and values must be of identical length.")

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
                if not helper.within_tol(price_csv, price_new, tolerance_percent / 100.0):
                    if storage_is_groundtruth is True:
                        new_values[idx_new] = price_csv  # Adjust provider data to existing data
                        logging.debug("Found a mismatch between provider- and market data. "
                                        "Will prioritize market-data (this behavior is configurable via the header in "
                                        "the storage csv file).")
                        logging.debug(f"Date: {date_cur}\tStorage Value: {price_csv:.2f}\t"
                                     f"Provider Value: {price_new:.2f}")
                    else:
                        values_merged[idx] = price_new  # Take the new/provider-data to write back to file
                        logging.debug("Found a mismatch between provider- and market data. "
                                        "Will prioritize provider-data (this behavior is configurable via the "
                                        "header in the storage csv file)")
                        logging.debug(f"Date: {date_cur}\tStorage Value: {price_csv:.2f}\t"
                                     f"Provider Value: {price_new:.2f}")
                    # Record a string for later output:
                    discrepancy_entries.append(f"{date_cur};\t{price_csv:.3f};\t{price_new:.3f}")

        # Output the mismatching entries of the market data file:
        numentry = min(len(discrepancy_entries), 20)
        if len(discrepancy_entries) > 0:
            logging.warning(f"{len(discrepancy_entries):d} obtained storage data entries do not match the "
                            f"recorded values (tolerance is set to: {tolerance_percent:.1f}%).")
            logging.info(f"Storage overwrite flag is set to: '{not storage_is_groundtruth}' "
                         f"(configurable via header in storage csv files)")
            logging.info(f"File: {storage_obj.get_filename()}. Entries (listing only first {numentry} elements):")
            logging.info("Date;\tRecorded Price;\tObtained Price")
            for i in range(numentry):
                logging.info(discrepancy_entries[i])

        # In the following: the new values are sorted into the existing storage-data
        dates_merged_dt = [self.analyzer.str2datetime(x) for x in dates_merged]
        csv_dates_dict = storage_obj.get_dates_dict()

        # Iterate over all new provider-data and sort it into the merged list:
        for new_date_idx, newdate in enumerate(new_dates):
            if newdate not in csv_dates_dict:  # The current new date is not in the market-data-list: it can be inserted!
                newdate_dt = self.analyzer.str2datetime(newdate)
                # Find the index, where it has to go, and insert it:
                insert_idx = bisect.bisect_left(dates_merged_dt, newdate_dt)
                dates_merged_dt.insert(insert_idx, newdate_dt)
                values_merged.insert(insert_idx, new_values[new_date_idx])

        # Convert back to string-representation and check the consistency, to be sure nothing went wrong:
        dates_merged = [self.analyzer.datetime2str(x) for x in dates_merged_dt]
        if dateoperations.check_date_order(dates_merged, self.analyzer, allow_ident_days=False) is False:
            raise RuntimeError(f"Something went wrong when fusing the data. Path: {storage_obj.get_filename()}")
        return dates_merged, values_merged

    def apply_splits(self, splits, provider_data):
        """Applies splits to provider-data  (and _not_ to storage-data, as it otherwise will be written to file).
        Used, if provider does not apply splits.
        The split-data used here originates from the header-section of stock-files in the storage-folder/CSVs
        :param splits: List of tuples of splits
        :param provider_data: Tuple of two lists (dates, values) of the provider
        :return: Tuple of two lists (dates, values), where the splits have been applied.
        """
        if len(splits) == 0:
            return provider_data
        split_dates = [x[0] for x in splits]
        split_ratios = [x[1] for x in splits]
        split_factor = 1.0
        dates, values = provider_data
        if len(values) != len(dates):
            raise RuntimeError("Data must be of equal length")
        split_cnt = 0
        for idx in range(len(dates) - 1, -1, -1):
            d = dates[idx]
            index = next((i for i, item in enumerate(split_dates) if item == d), None)
            if index is not None:
                split_factor = split_factor * split_ratios[index]
                split_cnt = split_cnt + 1
            values[idx] = values[idx] / split_factor
        if len(values) != len(dates):
            raise RuntimeError("Something went wrong in the split-calculation.")
        return dates, values

    def write_data_to_storage(self, storage_obj, data):
        """New (and existing) data is written to storage, i.e., the data is extended with the new data that was
        obtained by the data provider."""

        if files.file_exists(storage_obj.get_pathname()) is False:
            raise RuntimeError("File must already exist!")

        # Read the existing file's header into memory.
        lines_to_write = []
        lines_csv = files.get_file_lines(storage_obj.get_pathname())
        # Copy the header. The header stops at self.DATA_STRING
        for line in lines_csv:
            stripline = stringoperations.strip_whitespaces(line)
            txt, _ = stringoperations.read_crop_string_delimited(stripline, self.DELIMITER)
            if txt == self.DATA_STRING:
                lines_to_write.append(stripline)
                break
            lines_to_write.append(stripline)

        dates, values = data
        if len(dates) != len(values):
            raise RuntimeError("Data and values must be of equal length")

        if not dateoperations.check_date_order(dates, self.analyzer, allow_ident_days=False):
            raise RuntimeError("Data to be written to storage must be in order without duplicates")

        for idx, date in enumerate(dates):
            if dateoperations.is_date_valid(date, self.dateformat) is False:
                raise RuntimeError("Can not write faulty-formatted string to file")
            lines_to_write.append(f"{date}{self.DELIMITER}{values[idx]:.3f}")

        # Write the file:
        try:
            files.write_file_lines(storage_obj.get_pathname(), lines_to_write, overwrite=True)
        except:
            raise RuntimeError(f"Could not overwrite storage-file. Path: {storage_obj.get_pathname()}")
