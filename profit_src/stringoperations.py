"""Implements various functions for handling and manipulating strings

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import re
import datetime as dt

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
    if not isinstance(string, str) or not isinstance(delim, str):
        raise RuntimeError("Received a non-string object to crop, or non-string delimiter.")
    delim_idx = string.find(delim)
    if delim_idx > 0:
        # Read the string until the first delimiter:
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
