"""Contains various auxiliary functions

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import math


def isclose(a, b, rel_tol=1e-9, abs_tol=0.0):
    """For comparing float-numbers: Returns true, if the two numbers are within the specified absolute and/or
    relative tolerances.
    :param a: float input a
    :param b: float iniput b
    :param rel_tol: relative tolerance
    :param abs_tol: absolute tolerance
    :return: True, if the numbers are "sufficiently equal"
    """
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def isinteger(a, rel_tol=1e-9, abs_tol=0.0):
    """
    Checks if a (float) number is an integer or not.
    :param a: The float to be checked
    :param rel_tol: See isclose() above
    :param abs_tol: See isclose() above
    :return: True, if the number is "sufficiently" an integer
    """
    lower = math.floor(a)
    upper = math.ceil(a)
    return isclose(lower, a, rel_tol, abs_tol) or isclose(upper, a, rel_tol, abs_tol)


def within_tol(a, b, tol):
    """For checking if two numbers don't deviate too much from each other
    :param a: First number
    :param b: Second number
    :param tol: Relative tolerance
    :return: True, if the numbers are within tolerance
    """
    if b > 1e-9:
        return abs((a / b) - 1.0) <= tol
    if a > 1e-9:
        return abs((b / a) - 1.0) <= tol
    return True


def list_all_zero(vallist):
    """Checks if all elements of a list are smaller than 1e-9"""
    return all(-1e-9 < x < 1e-9 for x in vallist)


def accumulate_list(inlist):
    """Accumulates the values of a list
    :param inlist: List of values
    :return: List of identical lenght, with accumulated values
    """
    if len(inlist) <= 1:
        return inlist
    accu = [inlist[0]]
    for val in inlist[1:]:
        accu.append(accu[-1] + val)
    return accu


def sum_lists(lista, listb):
    """Sum the values of two lists piecewise
    :param lista:
    :param listb:
    :return: List of summed values
    """
    if len(lista) != len(listb):
        raise RuntimeError("The two lists must be of identical length for summation.")
    return [x + y for x, y in zip(lista, listb)]


def diff_lists(lista, listb):
    """Differece of the values of two lists, piecewise lista - listb
    :param lista:
    :param listb:
    :return: List of summed values
    """
    if len(lista) != len(listb):
        raise RuntimeError("The two lists must be of identical length for summation.")
    return [x - y for x, y in zip(lista, listb)]


def create_dict_from_list(string_list):
    """Creates and returns a dictionary from a list of strings, where the values are the list indices.
    Note: If there are duplicate entries in the string_list, the previous entries will be overwritten by the latter ones
    :param string_list: List of strings
    :return: Dict with the strings as keys and values as list indices"""
    # Todo: Sanitize input? Check for strings? Check if no duplicates?
    d = {}
    for i, txt in enumerate(string_list):
        if txt not in d:
            d[txt] = i
        else:
            raise RuntimeError("Received duplicate date when trying to create date-dict. This is likely not OK.")
    return d

"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    print(isinteger(1.99999999999))
