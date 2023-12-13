"""Functions for handling files, folders and paths

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import logging
from pathlib import Path
import re
from . import stringoperations


def filename_append_number(fpath, separator, num):
    """Adds a number to a filename. E.g., /test.pdf ==> /test_2.pdf
    :param fpath: Path of the file, or filename (Path-object)
    :param separator: String, encoding the desired character before the number is added, e.g., "_"
    :param num: Number added to the file-path
    :return: Path-object of the modified path
    """
    if not isinstance(fpath, Path):
        fpath = Path(fpath)
    stem = fpath.stem
    suffix = fpath.suffix
    newname = f"{stem}{separator}{int(num)}{suffix}"
    return fpath.with_name(newname)


def filename_append_string(fpath, separator, addstring):
    """Adds a string to a filename. E.g., /test.pdf ==> /test_group.pdf
    :param fpath: Path of the file, or filename (Path-object)
    :param separator: String, encoding the desired character before the number is added, e.g., "_"
    :param addstring: String to be added to the file-path
    :return: Path-object of the modified path
    """
    if not isinstance(fpath, Path):
        fpath = Path(fpath)
    stem = fpath.stem
    suffix = fpath.suffix
    newname = f"{stem}{separator}{addstring}{suffix}"
    return fpath.with_name(newname)


def filename_add_extension(fpath, extension):
    """Adds an extension to a file name.
    """
    if not isinstance(fpath, Path):
        fpath = Path(fpath)
    if isinstance(extension, str):
        if extension.startswith('.'):
            extension = extension[1:]
    else:
        raise RuntimeError("Extension must be a string")

    stem = fpath.stem
    newname = f"{stem}.{extension}"
    return fpath.with_name(newname)


def get_filename(fpath, keep_suffix=False):
    """Obtains the filename from paths that are separated with '/'
    :param fpath: Path of the file, or filename (Path-object)
    :param keep_suffix: If true, the file-extension is retained with the filename
    :return: Path-object of the file name
    """
    if not isinstance(fpath, Path):
        fpath = Path(fpath)
    if keep_suffix:
        return Path(fpath.name)
    return Path(fpath.stem)


def write_file_lines(filepath, lines, overwrite=False):
    """Writes lines of strings, supplied as list, into a file.
    :param filepath: Path of the file, as Path-object
    :param lines: List of strings to be written to file
    :param overwrite: Boolean, if True, it overwrites any existing file. If False, it appends the lines to an existing
    file.
    :return: Nothing.
    """
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    if overwrite is True:
        filepath.write_text('\n'.join(lines), encoding='utf8')
    else:
        with filepath.open('a', encoding='utf8') as f:
            for line in lines:
                f.write(f"{line}\n")


def clean_string(s):
    """Remove non-alphanumeric characters from a string such that it
    can be used for a filename. The dot (".") is allowed.
    """
    return re.sub(r'[^a-zA-Z0-9._]', '', s)


def get_file_lines(filepath):
    """Returns all lines of a file as a list of strings
    :param filepath: Path object of the file
    :return: List of strings
    """
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    # Read all lines in the file:
    with filepath.open(encoding='utf8') as file:
        lines = file.read().splitlines()
    return lines


def file_exists(filepath):
    """Returns true if a certain file exists, False if not.
    :param filepath: Pathlib object of the file
    :return: True, if file exists, otherwise False.
    """
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    return filepath.exists()


def check_create_folder(folderpath, create_if_missing=False):
    """Checks if a folder exists at the specified path (i.e., if the path points to a folder).
    :param folderpath: Path-object of the folder (or string, will be converted).
    :param create_if_missing: If False, we return False. If true, it will be created
    :return: True, if all went well, or if folder is already existing
    """
    if not isinstance(folderpath, Path):
        folderpath = Path(folderpath)
    if not folderpath.is_dir():
        if create_if_missing is True:
            folderpath.mkdir(parents=True, exist_ok=True)
            logging.warning(f"Created the folder {folderpath} as it was missing.")
            return True
        return False
    return True


def create_path(folderpath, filename):
    """Simply creates a path from a folder-name (which resides inside the project directory) and a file within.
    :param foldername: String or Path-object of folder-name
    :param filename: String or Path-object of file-name
    :return: Path-object of joined path
    """
    if not isinstance(folderpath, Path):
        folderpath = Path(folderpath)

    if isinstance(filename, str):
        filename = clean_string(filename)
        filename = Path(filename)
        return folderpath.joinpath(filename)
    if isinstance(filename, Path):
        return folderpath.joinpath(filename)

    raise RuntimeError("Filename must either be a string or a Path-object.")


def delete_file(path):
    """Deletes a file.
    :param path: String of the file's path, or a Path-object
    """
    if not isinstance(path, Path):
        path = Path(path)
    try:
        if path.exists():
            path.unlink()
        else:
            raise RuntimeError("File does not exist.")
    except PermissionError:
        logging.error("No permission to delete file.")
    except IsADirectoryError:
        logging.error("The path specified is a directory, not a file.")


def get_file_list(folderpath, extension):
    """Lists files of a given extension in a folder
    :param folderpath: Path of folder (Path-object)
    :param extension: String that encodes the extension of the files that are being collected.
    If this is None, all files are returned
    :return: List of Path-objects for the files discovered
    """
    if not isinstance(folderpath, Path):
        folderpath = Path(folderpath)
    if extension is not None:
        if extension.startswith('.'):
            extension = extension[1:]
        files = folderpath.glob(f'*.{extension}')
        return list(files)
    files = [item for item in folderpath.iterdir() if item.is_file()]
    return files


def get_filename_from_path(fname):
    """Strip the folder-path from a file name"""
    if not isinstance(fname, Path):
        fname = Path(fname)
    return fname.name


def append_transaction_line_to_file(fpath, strings, delimiter, eofstring, profit_cfg):
    """Appends a line of new transactions-data to a account- or investment-file.
    Reads the file, appends the line, writes it back to disk.
    White spaces are read from the previous line, to conserve the file's layout. # Todo This is not really working yet.
    # Todo The problem is that the files are mixed tab-space, and the editor is not always displaying a
    tab with 4 spaces...
    :param fpath: Path-object to the file to modify.
    :param strings: List of strings containing the transaction-data to write to the file.
    :param delimiter: String of the desired delimiter to separate the strings in the list of strings.
    :param eofstring: String that indicates the end-of-file, e.g., "EOF".
    """
    if not isinstance(fpath, Path):
        fpath = Path(fpath)
    if not file_exists(fpath):
        raise RuntimeError(f"File does not exist, can not append transactions-data. Path: {fpath}")
    lines = get_file_lines(fpath)
    if lines[-1] != eofstring:
        raise RuntimeError(f"Last line is not end-of-file string. Expected: '{eofstring}'. Received: '{lines[-1]}'")
    del lines[-1] # EOF string removed; will be re-added later.

    # Read the white space from the previous line (the last transactions-line):
    whitespaces = re.findall(r'[ \t]+', lines[-1])
    if len(whitespaces) < len(strings)-1: # Note: There can be additional white spaces in the "notes" section.
        raise RuntimeError(f"Did not receive sufficient strings, or the whitespace-readout did not work properly. "
                           f"len(whitespaces) = {len(whitespaces)}. len(strings) = {len(strings)}.")

    from .parsing import ParsingConfig # Needed here to avoid circular import
    transactions_startidx = None
    for idx, line in enumerate(lines):
        data, remainder = stringoperations.read_crop_string_delimited(line, delimiter)
        if data == ParsingConfig.STRING_TRANSACTIONS:
            transactions_startidx = idx + 1
            break
    if transactions_startidx is None:
        raise RuntimeError("Could not find start of transactions-block.")
    transactions_lines = lines[transactions_startidx:-1]
    column_widths = []
    for line in transactions_lines:
        col, remainder = stringoperations.read_crop_string_delimited(line, delimiter)
        idx = 0
        while col != remainder and idx < 8:
            if idx > 0:
                col, remainder = stringoperations.read_crop_string_delimited(remainder, delimiter)
            # Pull the leading white space, as it also contributes to the column width:
            whitespace, remainder = stringoperations.remove_leading_whitespace(remainder)
            whitespace_len = stringoperations.count_whitespace_length(whitespace, profit_cfg.TAB_LEN)
            colwidth = len(col) + 1 + whitespace_len # +1 for the delimiter
            if len(column_widths) <= idx:
                column_widths.append(colwidth)
            else:
                column_widths[idx] = max(column_widths[idx], colwidth)
            idx += 1

    # Delimit all strings, apart from the last one (the notes are not needed):
    strings_delimited = [f"{item}{delimiter}" for item in strings[0:-1]]
    strings_delimited_padded = []
    for idx, string in enumerate(strings_delimited):
        string_extended = string.ljust(column_widths[idx])
        strings_delimited_padded.append(string_extended)
    strings_delimited_padded.append(strings[-1]) # Add the (empty) notes-string at the end. No padding needed here.
    newstring = "".join(strings_delimited_padded)
    lines.append(newstring)
    lines.append(eofstring)
    write_file_lines(fpath, lines, overwrite=True)
