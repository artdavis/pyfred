#! /usr/bin/env python
"""
Module wide global variables
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
"""
import os
# For Python 2/3 compatibility get str() to replace py2 unicode()
from builtins import str as text

# Use absolute paths or relative paths
# Note absolute paths are necessary for CreateLib to be able to find
# the stub files
RELPATHS = False
if RELPATHS:
    joiner = lambda *x: os.path.relpath(os.path.join(*x))
else:
    joiner = os.path.join

CWD = os.path.dirname(os.path.abspath(__file__))
DATADIR = joiner(CWD, 'data')
STUBDIR = joiner(DATADIR, 'stubs')
CUSTOMSTUBDIR = joiner(DATADIR, 'customstubs')
HTMLDIR = joiner(DATADIR, 'html')
APIFILE = 'api_build.yaml'
APIFILEPATH = joiner(DATADIR, APIFILE)
APIOVERRIDE = 'api_overrides.yaml'
APIOVERRIDEPATH = joiner(DATADIR, APIOVERRIDE)
DOCFILE = 'alldocs.yaml'
DOCFILEPATH = joiner(DATADIR, DOCFILE)
CHMFILE = 'Fred.chm'
# If CHMAUTOLOCATE is True, search the expected FRED install locations for the
# latest help file. Otherwise, use the CHMPATH variable as the path location
# for finding it.
CHMAUTOLOCATE = True
CHMPATH = '' # Only used if CHMAUTOLOCATE == False
#CHMAUTOLOCATE = False
#CHMPATH = os.path.join("F:\\","src","FRED","Resources","Hlp")
PYAPIFILE = 'apicmds.py'
PYAPIPATH = os.path.join(CWD, PYAPIFILE)
# Typemap for translating from VB variable types to python types
TYPEMAP = {
        'Boolean' : bool,
        'Byte' : int,
        'Huge_' : int, # Caution will promote to long if > sys.maxint
        'Double' : float,
        'Long': int,
        'Integer': int,
        'Single': float,
        'String' : text,
        'Variant' : 'unknown',
        'Object' : 'unknown',
        }
