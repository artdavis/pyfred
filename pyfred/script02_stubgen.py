#!/usr/bin/env python
"""
Functions for creating FRED script library stubs
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
** When generating API, run this script SECOND. **

Creates the VBScript wrappers for library objects to be loaded using
CreateLib().

TODO: Add facility to generate our own custom defined stub files. In particular
so we can create a TextWindowPrint() command.
TODO: Switch to jinja2 templates instead of string format replacements.
"""
import os
import yaml
import re

import glovars

# Setup to use breakpt() for droppping into ipdb:
from IPython.core.debugger import Tracer
breakpt = Tracer()

# Regex for wrapping paragraphs...
# 60 columns then up to the next whitespace:
PARMAT = re.compile('(.{60}.+?)\s')
DOCSTRING = '''
    ' Wrapper stub for {filename} {cmdtypecaps}
    '
    ' {cmddoc}
    '
    ' Description:
    '   {descr}
    '
    ' Returns:
    '   {returndoc}
    '
    ' Useful in COM programming as:
    '     >>> lib = CreateLib(<path>/{filename})
    ' (where <path> is the path location for {filename})
    ' to yield an object that can be called as:
    '     >>> lib.libfunct()
    '
    ' WARNING: customizing this VBScript may override intended API function.
'''

DOCFUNCT = '''{filename} is implemented in FRED as a Function.
    ' A VBScript Function has a return value. The return value is the
    ' information of interest and so it is this value which this
    ' wrapper returns.'''

SUBFUNCT = '''{filename} is implemented in FRED as a Subroutine.
    ' {subargdoc}'''

SUBNOARGS = '''It does not take any parameters and only performs
    ' an application specific task. Nothing is returned.'''
SUB1ARG = '''This subroutine takes only one parameter and may or may
    ' not alter its value. It is therefore returned as a single value
    ' of the same data type as which it was supplied.'''
SUBARGS = '''This subroutine takes multiple parameters and may or may
    ' not alter any number of them. All of the supplied parameters
    ' are therefore returned in an Array() structure after the
    ' subroutine has operated on them'''

def main():
    """
    Encapsulate script procedural body here so it can be externally
    referenced as <filename>.main or automatically invoked from the
    if __name__ == "__main__"" statement when the script is run directly.
    """
    # Get the API Building data structure
    with open(glovars.APIFILEPATH, 'r') as fid:
        apidat = yaml.load(fid.read())
    # Make the stubs directory if necessary
    if not os.path.exists(glovars.STUBDIR):
        os.makedirs(glovars.STUBDIR)

    # Select and generate stubs for all of the functions:
    filenames = apidat.keys()
    # Small subset of functions for testing
    #filenames = [
    #    'SetTrimVolume', # 2 Sub args: Long, T_TRIMVOLUME
    #    'GetFirstRay', # 2 Funct args: Long, T_RAY; Ret Boolean
    #    'GetUnits', # 0 Funct args; Ret: String
    #    'FindFullName', # 1 Funct args: String; Ret: Long
    #    'EnergyDensity', # 4 Funct args: Long, Long, T_ANALYSIS, Double;
    #                     # Ret: Long
    #    'ARNDeleteAllNodes', # 0 Sub args: NONE
    #    'SetUnits', # 1 Sub arg: String
    #    'GetEntity', # 2 Sub args: Long, T_ENTITY
    #    'GetTextPosition', # 2 Sub args: Long, Long
    #    ]

    print("\n Generating VBScript stub files...")
    for filename in filenames:
        #if filename.startswith('SetTrimVolume'):
        #    breakpt()
        print("... generating {}".format(filename))
        # Description in the config file
        descr = apidat[filename]['descr']
        # List of [<parameter>, <type>] of function return value
        retlist = apidat[filename]['returns']
        # Signature parameters
        sigitems = apidat[filename]['sig']
        # Nicely wrap long text descriptions
        parlist = PARMAT.split(descr)
        # Drop any empty strings
        while True:
            try:
                parlist.remove('')
            except ValueError:
                break
        descr = "\n    '   ".join(parlist)
        cmdtype = apidat[filename]['cmdtype']
        cmdtypecaps = cmdtype.upper()
        returndoc = ""
        if cmdtype == 'function':
            cmddoc = DOCFUNCT.format(**locals())
        elif cmdtype == 'subroutine':
            if len(sigitems) > 1:
                subargdoc = SUBARGS
            elif len(sigitems) == 1:
                subargdoc = SUB1ARG
            else:
                subargdoc = SUBNOARGS
            cmddoc = SUBFUNCT.format(**locals())
        else:
            continue # Don't process. Start the next loop of the for
            #raise ValueError('Unknown cmdtype: {}'.format(
            #                        apidat[filename]['cmdtype']))
        # For an empty sig, use a dummy variable
        if len(sigitems) == 0:
            vstr = 'dummy As Variant'
        else:
            vstr = ", ".join(["{} As {}".format(k, v) for k, v in sigitems])
        filepath = os.path.join(glovars.STUBDIR, filename + '.frs')
        fid = open(filepath, 'w')
        if cmdtype == 'function':
            rettype = apidat[filename]['returns'][1]
            fid.write("Function libfunct ({}) As {}".format(vstr, rettype))
            retstr = " As ".join(apidat[filename]['returns'])
            returndoc = retstr
        elif cmdtype == 'subroutine' and 0 < len(retlist):
            # Handle a function we are treating as a subroutine
            fid.write("Function libfunct ({}) As Variant".format(vstr))
            returndoc = "Array of:\n    '   "
            returndoc += "{} As {}\n    '   ".format(*retlist)
            returndoc += "\n    '   ".join([" As ".join(li) for li in
                                            sigitems])
        else:
            if len(sigitems) > 1:
                rettype = 'Variant'
                fid.write("Function libfunct ({}) As {}".format(vstr, rettype))
                returndoc = "Array of:\n    '   "
            elif len(sigitems) == 1:
                try:
                    # If values came back array-like, get the first element
                    rettype = sigitems[0][1]
                except TypeError:
                    # Otherwise just return the value
                    rettype = sigitems[1]
                fid.write("Function libfunct ({}) As {}".format(vstr, rettype))
            else:
                # There are no supplied parameters
                fid.write("Function libfunct ({})".format(vstr))
                returndoc = "Does not have a return value."
            returndoc += "\n    '   ".join([" As ".join(li) for li in
                                            sigitems])
        fid.write(DOCSTRING.format(**locals()))
        # No need to declare explicit dimensions line by line as that is
        # already done in the arguments of the function definition
        sigvars = [_[0] for _ in sigitems]
        params = ", ".join(sigvars)
        # Returned params should never have parenthesis (array types)
        params = re.sub("[\(\)]", '', params)
        if cmdtype == 'function':
            fid.write("    libfunct = {} ({})\n".format(filename, params))
        elif cmdtype == 'subroutine':
            # Sometimes we override what FRED considers a function and
            # call it a subroutine. We do this in instances where we
            # want access to the side effects the subroutine has had on
            # the variables we passed in. So if we have a subroutine
            # with a non-empty 'returns' value, get that first and
            # put it at the front of the returned list followed by the
            # rest of the signature parameters
            if 0 == len(retlist):
                # Run as a usual subroutine
                fid.write("    {} {}\n".format(filename, params))
            else:
                fid.write("    Dim {} As {}\n".format(*retlist))
                fid.write("    {} = {}({})\n".format(retlist[0], filename, params))
                # Prepend the returned function value to the params
                params = "{}, {}".format(retlist[0], params)
            if len(sigvars) > 1:
                # Return an array of parameters if there are multiple
                fid.write("    libfunct = Array({})\n".format(params))
            elif len(sigvars) == 1:
                # Return singleton for just one parameter
                fid.write("    libfunct = {}\n".format(params))
            else:
                # No parameters, nothing to return
                pass
        fid.write("End Function")
        fid.close()

if __name__ == "__main__":
    # If this script is invoked directly (not imported), execute main()
    main()
