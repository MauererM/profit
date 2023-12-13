"""Contains various auxiliary functions

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import itertools
import re


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
    :return: List of identical length, with accumulated values
    """
    if not isinstance(inlist, list):
        raise RuntimeError("Must receive a list")
    return list(itertools.accumulate(inlist))


def sum_lists(lists):
    """Sum the values of the given list of lists piecewise
    :param lists: List of lists to be piecewise summed. All sublists need to be of identical length.
    :return: List of summed values
    """
    if not isinstance(lists, list):
        lists = [lists]
    if not all(isinstance(sublist, list) for sublist in lists):
        raise RuntimeError("Did not receive a list of lists")
    if not are_sublists_same_length(lists):
        raise RuntimeError("Sublists are of varying length")
    return [sum(values) for values in zip(*lists)]


def are_sublists_same_length(lists):
    """Checks if all sublists in a list of lists are of same length"""
    if not isinstance(lists, list):
        lists = [lists]
    if not all(isinstance(sublist, list) for sublist in lists):
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


def find_duplicate_indices(inlist):
    """From a list, return (a list of) all indices at which duplicates (e.g., duplicate dates) have been found."""
    occurrences = {}

    for index, item in enumerate(inlist):
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


def partition_list(inlist, blocksize):
    """Partitions a list into several lists, of blocksize each (or smaller)
    :param inlist: Input list
    :param blocksize: Size of desired blocks, integer
    :return: List of partitioned lists, each sub-list of length blocksize
    """
    blocksize = int(blocksize)
    return [inlist[i:i + blocksize] for i in range(0, len(inlist), blocksize)]


def contains_zeroes(inlist, trim_trailing_zeroes=True, trim_leading_zeroes=True, tol=1e-9):
    """Checks if a list of floats contains (near-) zero elements.
    Trailing or leading zeroes can be omitted/not considered.
    """
    if not isinstance(inlist, list):
        raise RuntimeError("Need to receive a list.")

    def is_near_zero(val, t):
        return -1.0 * t < val < t

    trimmed = list(inlist)  # Modify the copy!
    if trim_leading_zeroes is True:
        while trimmed and is_near_zero(trimmed[0], tol):
            del trimmed[0]

    if trim_trailing_zeroes is True:
        while trimmed and is_near_zero(trimmed[-1], tol):
            del trimmed[-1]

    return any(is_near_zero(val, tol) for val in trimmed)

def is_valid_float(input_str):
    """Checks if a string is a valid floating point number, or not"""
    return re.match(r'^[+-]?(\d+(\.\d*)?|\.\d+)$', input_str) is not None

