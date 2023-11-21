"""Implements various functions for handling and manipulating strings

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import re
import datetime as dt


def filename_append_number(pathstr, separator, num):
    """Adds a number to a filename. E.g., /test.pdf ==> /test_2.pdf
    :param pathstr: Path of the file, or filename (string)
    :param separator: String, encoding the desired character before the number is added, e.g., "_"
    :param num: Number added to the file-path
    :return: String of the modified path
    """
    filename = pathstr.split('.')
    filename[-2] = filename[-2] + separator + repr(num)
    filename = '.'.join(filename)
    return filename


def filename_append_string(pathstr, separator, addstring):
    """Adds a string to a filename. E.g., /test.pdf ==> /test_group.pdf
    :param pathstr: Path of the file, or filename (string)
    :param separator: String, encoding the desired character before the number is added, e.g., "_"
    :param addstring: String to be added to the file-path
    :return: String of the modified path
    """
    filename = pathstr.split('.')
    filename[-2] = filename[-2] + separator + addstring
    filename = '.'.join(filename)
    return filename


def get_filename(pathstr, keep_type=False):
    """Obtains the filename from paths that are separated with '/'
    :param pathstr: String of the path
    :param keep_type: If true, the file-extension is retained with the filename
    :return: String of the desired filename
    """
    filename = pathstr.split('/')[-1]
    if keep_type is True:
        return filename
    filename = filename.split('.')[-2]
    return filename


def check_allowed_strings(strlist, reflist):
    """Checks, if a list only contains allowed strings.
    :param strlist: List of strings to test
    :param reflist: List of allowed strings
    :return: False, if string not in allowed list. Else: True
    """
    for _, inpt in enumerate(strlist):
        if inpt not in reflist:
            return False
    return True


def strip_whitespaces(string):
    """Strips all whitespace-characters from a line (i.e., a string)
    :param string: Input string
    :return: String without whitespace characters
    """
    return re.sub(r'\s+', '', string)


def read_crop_string_delimited(string, delim):
    """Reads characters from a string until a certain delimiter is reached.
    The input string is shortened by the contents (and including) up to the delimiter
    If there is no delimiter, the original input-string is returned twice.
    For example, if this is the input: "01.02.2010; 134.3443", ";" then the output would be ("01.02.2010", "134.3443")
    :param string: string to be read
    :param delim: string, defines until where the string is read
    :return: tuple, of the result, which is the string that contains the beginning of the input string until
    the delimiter, and the remainder of the string
    """
    delim_idx = string.find(delim)
    if delim_idx > 0:
        # Read the string until the first semicolon:
        result = string[0:delim_idx]
        string = string[delim_idx + 1:]  # Crop the remainder of the string
        return result, string
    # Delimiter not found:
    return string, string


class DateTimeConversion:
    """A small class that provides caching for the frequently used datetime-conversion functions
    """

    def __init__(self):
        self.datetime2str_cache = {}
        self.str2datetime_cache = {}

    def str2datetimecached(self, string, fmt):
        """Converts a string to a datetime object
        :param string: Date-string
        :param fmt: String of the format of the date encoded in the string
        :return: datetime object
        """
        if string not in self.str2datetime_cache:
            self.str2datetime_cache[string] = dt.datetime.strptime(string, fmt)
        return self.str2datetime_cache[string]

    def datetime2strcached(self, datetimeobj, fmt):
        """Converts a datetime object to a string
        :param datetimeobj: datetime-object to be converted
        :param fmt: String encoding the desired format of the output string
        :return: datetime object
        """
        if datetimeobj not in self.datetime2str_cache:
            self.datetime2str_cache[datetimeobj] = datetimeobj.strftime(fmt)
        return self.datetime2str_cache[datetimeobj]


def str2datetime(string, fmt):
    """Converts a string to a datetime object
    :param string: Date-string
    :param fmt: String of the format of the date encoded in the string
    :return: datetime object
    """
    return dt.datetime.strptime(string, fmt)


def datetime2str(datetimeobj, fmt):
    """Converts a datetime object to a string
    :param datetimeobj: datetime-object to be converted
    :param fmt: String encoding the desired format of the output string
    :return: datetime object
    """
    return datetimeobj.strftime(fmt)


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    # pathstr = "/test_folder/file.pdf"
    # separator = "_"
    # num = 3
    # print(filename_append_number(pathstr, separator, num))

    date, val = read_crop_string_delimited("01.02.2010; 134.3443", ";")
    print(date)
    print(val)

    test = float("131.34235")
    print("asdf")

    # pathstr = "/this_is/a/test_path/filename.txt"
    # pathstr_2 = "adsf"
    # print(get_filename(pathstr, keep_type=True))
