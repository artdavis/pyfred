#!/usr/bin/env python
"""
Collection of useful parsing utilities
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
"""
import yaml
import re

import glovars

# Regex to capture "space commas"
SPCOM=re.compile('\s+,')

def readyaml(fname):
    """
    Open and read in yaml formatted data structure and return the
    pythonic data structure.
    """
    with open(fname, 'r') as fid:
        return yaml.load(fid.read(), Loader=yaml.FullLoader)

def writefile(fname, txt):
    """
    Write out received text to fname file
    """
    with open(fname, 'w') as fid:
        fid.write(txt)

def readfile(fname):
    """
    Read in and return text in fname
    """
    with open(fname, 'r') as fid:
        return fid.read()

def fmt_docstr(docdict, indent="", ncols=60):
    """
    Nicely format and return the received docdict as a string that can
    be used as part of a function docstring.

    Parameters
    ----------
    docdict : dict
        The documentation dictionary
    indent: str, optional
        Per line indent prefix (Default: "")
    ncols: int, optional
        Number of columns before breaking the line (Default: 60)
    """
    docstr = ''
    for k, v in docdict.items():
        # Heading
        docstr += "\n{}{}:\n".format(indent, k)
        docstr += "{}{}\n".format(indent, "-" * (len(k) + 1))
        # Format the content
        leadin = '  ' # Additional indentation string
        # Strip out extraneous "space-commas"
        v = SPCOM.sub(',', v)
        conlines = v.split('\n')
        # Special handling for parameters heading
        paramset = {'param', 'member'}
        parambool = False
        for pstr in paramset:
            if k.lower().startswith(pstr):
                parambool = True
                for c in range(len(conlines)):
                    # Every other line has twice the indent
                    docstr += indent + leadin * (c%2+1) + conlines[c] + "\n"
        if not parambool:
            for c in range(len(conlines)):
                docstr += indent + leadin + conlines[c] + "\n"
    # Give it a once over to wrap any extra long lines
    newdocstr = ''
    for linestr in docstr.split("\n"):
        if len(linestr) > ncols:
            linestr = wrap_longlines(linestr, indent=indent, ncols=ncols)
        newdocstr += linestr + "\n"
    return newdocstr

def wrap_longlines(txt, indent="", ncols=60):
    """
    Nicely wrap long lines of text.

    Parameters
    ----------
    txt: str
        The text string for wrapping
    indent: str, optional
        Per line indent prefix (Default: "")
    ncols: int, optional
        Number of columns before breaking the line (Default: 60)
    """
    # Regex for wrapping paragraphs. Double curly braces indicate
    # a literal curly brace in a .formatted string
    parmat = re.compile('(.{{{}}}.+?)\s'.format(ncols - len(indent)))
    # Nicely wrap long text descriptions as needed
    parlist = parmat.split(txt)
    # Drop any empty strings
    while True:
        try:
            parlist.remove('')
        except ValueError:
            break
    return ("\n" + indent).join(parlist)

def vb2pytype(vbtype, rettype='type'):
    """
    Convert the supplied Visual Basic variable type to it's corresponding
    type in python.

    Parameters
    ----------
    vbtype: str
        Type of VisualBasic variable we want to get a python analog for
    rettype: {'type', 'repr', 'str'}
        Type of the return value. Accepts: 'type', 'repr', 'str'.
        (Default: 'type')
    :type rettype: str

    Returns
    -------
    type or str
        Depending on how rettype parameter is set, return either an actual
        type object (rettype='type'), the type name as a string (rettype='str')
        or the type string representation returned by repr() (rettype='repr').
    """
    if vbtype.startswith('T_'):
        return "<com_record '{}'>".format(vbtype)
    # Make sure vbtype is compatible with the proper capitalization for the
    # keys in TYPEMAP
    vbtype = vbtype.lower().capitalize()
    try:
        unknown_bool = glovars.TYPEMAP[vbtype] == 'unknown'
        if rettype == 'type':
            if unknown_bool:
                raise TypeError("{} does not have an analagous Python type".
                        format(vbtype))
            else:
                return glovars.TYPEMAP[vbtype]
        elif rettype == 'repr':
            if unknown_bool:
                return "<type 'unknown'>"
            else:
                return repr(glovars.TYPEMAP[vbtype])
        elif rettype == 'str':
            if unknown_bool:
                return "unknown"
            else:
                retstr = str(glovars.TYPEMAP[vbtype])
                typmat = re.compile("'(.+)'") # Capture text between single quotes
                matchobj = typmat.search(retstr)
                return matchobj.groups()[0]
        else:
            raise ValueError("Unsupported rettype: {}".format(rettype))
    except KeyError:
        return "unknown"
