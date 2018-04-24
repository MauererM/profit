"""Contains various auxiliary functions

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""


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


def within_tol(a, b, tol):
    """For checking if two numbers don't deviate too much from each other
    :param a: First number
    :param b: Second number
    :param tol: Relative tolerance
    :return: True, if the numbers are within tolerance
    """
    return abs((a / b) - 1.0) <= tol


def list_all_zero(vallist):
    """Checks if all elements of a list are smaller than 1e-9"""
    return all([x < 1e-9 for x in vallist])


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
