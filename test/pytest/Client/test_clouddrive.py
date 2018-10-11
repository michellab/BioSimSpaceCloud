
import os
import sys

from Acquire.Client import expand_source_destination

def test_expand_files():
    basedir = os.path.dirname(os.path.abspath(__file__))

    (a, b) = expand_source_destination("*", "")

    assert(len(a) == len(b))
