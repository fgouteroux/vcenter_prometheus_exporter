# coding: utf8
"""
Main hasks of this file came from six module
    https://github.com/benjaminp/six/blob/master/six.py
    six is under license MIT

"""
import sys

PY2 = sys.version_info[0] == 2

# pylint: disable=invalid-name,redefined-builtin

if PY2:
    text_type = unicode
    bytes = str
    string_types = (str, unicode)
    int_types = (int, long)

    range_type = xrange

    iterkeys = lambda x: x.iterkeys()
    itervalues = lambda x: x.itervalues()
    iteritems = lambda x: x.iteritems()

    class TimeoutError(Exception):
        """python3 built-in exception
        https://docs.python.org/3/library/exceptions.html#TimeoutError
        """
        pass

else:
    text_type = str
    string_types = (str,)
    int_types = (int,)

    range_type = range

    iterkeys = lambda x: iter(x.keys())
    itervalues = lambda x: iter(x.values())
    iteritems = lambda x: iter(x.items())

    TimeoutError = TimeoutError
