import csv
import re
from distutils.util import strtobool

def write_csv(filepath, data):
    headers = list(data.keys())
    with open(filepath, 'a') as f:
        w = csv.DictWriter(f, headers)
        if f.tell() == 0:
            w.writeheader()
        w.writerow(data)

def get_valid_filename(name):
    """
    modified from: https://github.com/django/django/blob/main/django/utils/text.py

    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        print("Could not derive file name from '%s'" % name)
        return None
    return s

def str_to_bool(value, default):
    try:
        result = bool(strtobool(value))
    except (ValueError, AttributeError):
        result = default
    return result