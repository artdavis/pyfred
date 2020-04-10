#!/usr/bin/env python
"""
Confirm availability of libraries required to run pyfred
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
"""

print("Checking if pyfred can be imported...")
try:
    import pyfred
    print("PASS: pyfred module location is good")
except ModuleNotFoundError:
    print("FAIL: pyfred could not be found")
    print("Try moving the pyfred module directory somewhere python can")
    print("find it or update your PYTHONPATH environment variable to")
    print("include the parent directory of pyfred.")
print("*"*60)
