#Todo add header of file

import re
import files

class IndexData:
    """Represents data from a marketdata-csv.
    Index files have this format:
    index + Symbol:
    "index_[a-zA-Z0-9.]{1,10}\.csv"
    """

    FORMAT_FNAME_GROUPS = r'index_([a-zA-Z0-9.]{1,10})\.csv'

    def __init__(self, pathname, interpol_days, data):
        self.pname = pathname
        self.interpol_days = interpol_days
        self.dates = data[0]
        self.values = data[1]

        # From the pathname, extract the name of the file and its constituents.
        self.fname = files.get_filename_from_path(self.pname)
        match = re.match(self.FORMAT_FNAME_GROUPS, self.fname)
        groups = match.groups()
        self.index = groups[0]