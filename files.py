"""Functions for handling files, folders and paths

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import os


def write_file_lines(filepath, lines, overwrite=False):
    """Writes lines of strings, supplied as list, into a file.
    :param filepath: Path of the file, as string
    :param lines: List of strings to be written to file
    :param overwrite: Boolean, if True, it overwrites any existing file. If False, it appends the lines to an existing
    file.
    :return: Nothing.
    """
    if overwrite is True:
        with open(filepath, 'w') as f:
            for line in lines:
                string = line + '\n'
                f.write(string)
    else:
        with open(filepath, 'a') as f:
            for line in lines:
                string = line + '\n'
                f.write(string)


def get_file_lines(filepath):
    """Returns all lines of a file as a list of strings
    :param filepath: String of the file's path
    :return: List of strings
    """
    # Read all lines in the file:
    with open(filepath) as f:
        lines = f.readlines()
    return lines


def file_exists(filepath):
    """Returns true if a certain file exists, False if not.
    :param filepath: String of the file's path
    :return: True, if file exists, otherwise False.
    """
    return os.path.isfile(filepath)


def create_path(foldername, filename):
    """Simply creates a path from a folder-name (which resides inside the project directory) and a file within.
    :param foldername: String of folder-name
    :param filename: String of file-name
    :return: String of joined path
    """
    return os.path.join(foldername, filename)  # Get path of file, including its folder


def delete_file(path):
    """Deletes a file.
    :param path: String of the file's path
    """
    os.remove(path)


def get_file_list(folderpath, extension):
    """Lists files of a given extension in a folder
    :param folderpath: Path of folder (string)
    :param extension: String that encodes the extension of the files that are being collected.
    If this is None, all files are returned
    :return: List of strings containing the file names, including extension
    """
    if extension is not None:
        return [f for f in os.listdir(folderpath) if (os.path.isfile(os.path.join(folderpath, f))
                                                      and f.endswith(extension) is True)]
    else:
        return [f for f in os.listdir(folderpath) if (os.path.isfile(os.path.join(folderpath, f)))]


"""
    Stand-alone execution for testing:
"""
if __name__ == '__main__':
    filepath = "investments_test/testfile.txt"
    print(file_exists(filepath))

    # test = get_file_lines(filepath)
    # print("Done")

    write_file_lines(filepath, ["First line", "Second Line"], overwrite=True)

    test = 3.4452
    test2 = str(test)
    pass
