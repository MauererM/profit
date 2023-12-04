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
    Checks if a (float) number is (representing) an integer or not.
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


def accumulate_list(inlist): # Todo when done with plotting and analysis overhaul: Check which functions here are still needed in helper.py
    """Accumulates the values of a list
    :param inlist: List of values
    :return: List of identical lenght, with accumulated values
    """
    if len(inlist) <= 1:
        return inlist
    accu = [inlist[0]]
    for val in inlist[1:]:
        accu.append(accu[-1] + val) # Todo can this be done smarter, without appending?
    return accu


def sum_lists(lists): # Todo test what happens if a single list is supplied?
    """Sum the values of two lists piecewise
    :param lists: List of lists to be piecewise summed. All sublists need to be of identical length.
    :return: List of summed values
    """
    if not isinstance(lists, list) and not all(isinstance(sublist, list) for sublist in lists):
        raise RuntimeError("Did not receive a list of lists")
    if not are_sublists_same_length(lists):
        raise RuntimeError("Sublists are of varying length")
    return [sum(values) for values in zip(*lists)]

def are_sublists_same_length(lists): # Todo test what happens if a single list is supplied?
    """Checks if all sublists in a list of lists are of same length"""
    if not isinstance(lists, list) and not all(isinstance(sublist, list) for sublist in lists):
        raise RuntimeError("Did not receive a list of lists")
    lengths = [len(sublist) for sublist in lists]
    if len(set(lengths)) != 1:
        return False
    return True



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
    if not isinstance(string_list, list):
        raise RuntimeError("Expected a list")
    if len(string_list) == 0:
        return {}
    if not isinstance(string_list[0], str):
        raise RuntimeError("Expected a list of strings")
    d = {}
    for i, txt in enumerate(string_list):
        if txt not in d:
            d[txt] = i
        else:
            raise RuntimeError("Received duplicate date when trying to create date-dict. This is likely not OK.")
    return d


def find_duplicate_indices(list):
    """From a list, return (a list of) all indices at which duplicates (e.g., duplicate dates) have been found."""
    occurrences = {}

    for index, item in enumerate(list):
        if item in occurrences:
            occurrences[item]['count'] += 1
            occurrences[item]['indices'].append(index)
        else:
            occurrences[item] = {'count': 1, 'indices': [index]}

    duplicate_indices = []
    for item in occurrences.values():
        if item['count'] > 1:
            duplicate_indices.extend(item['indices'])

    return duplicate_indices


def extract_sequences(indices, distance=1):
    """Finds the blocks of subsequent indices in a sorted list of indices, and returns a list of lists of the blocks."""
    if not indices:
        return []

    sequences = []
    current_sequence = [indices[0]]

    for i in range(1, len(indices)):
        if indices[i] == indices[i - 1] + distance:
            # Continuation of the current sequence
            current_sequence.append(indices[i])
        else:
            # End of the current sequence, start a new one
            sequences.append(current_sequence)
            current_sequence = [indices[i]]

    # Add the last sequence
    sequences.append(current_sequence)
    return sequences
