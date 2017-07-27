#!/usr/bin/env python
"""
Confirm availability of libraries required to run pyfred
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
"""

import importlib

required = ['numpy', 'scipy', 'matplotlib', 'IPython', 'html',
            'win32com', 'yaml']
missing = []

print("*"*60)
for r in required:
    try:
        importlib.import_module(r)
        print("PASS: '{}' is available".format(r))
    except ModuleNotFoundError:
        print("FAIL: '{}' is NOT available".format(r))
        missing.append(r)

print("-"*60)
if 0 < len(missing):
    print("Test failed. Please install the following packages and")
    print("re-run this script to confirm their availability:")
    for i in missing: print("    {}".format(i))
else:
    print("Test passed. pyfred has the necessary libraries to run.")
    
print("*"*60)

# Only run next test if previous test passed
if 0 == len(missing):
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
