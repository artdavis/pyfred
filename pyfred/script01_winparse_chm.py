#!/usr/bin/env python
"""
Parse the FRED help file for command signatures
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
** When generating API run this script FIRST **

Predecessor program to this was parse_chm.py which uses pyCHM to parse the
FRED help file and build the signatures and documentation. pyCHM is difficult
to get working on Windows. But windows has it's own CHM decompiler which
can be used to get the HTML files out of the CHM file::

    hh.exe -decompile <destdir> <filename.chm>

Use subprocess to call this and then access the HTML files in the extraction
directory to build the API datastructures.

TODO: Implement pyparsing instead of regexes
"""

import os
import re # Regex module
from collections import OrderedDict as OD
import codecs
from html.parser import HTMLParser
import subprocess
import yaml
import keyword # keyword.kwlist contains reserved keywords

import glovars
import utils_parse as utils

DOCFILE = 'alldocs'
# Max length for a variable name.
# Current record holder: len('CountOfNonZeroAbsorbedFluxCells') == 31
MAXVARNLEN = 32 # Max length for a variable name

# This program will create and save data structure files based on the FRED help
# file which is copyrighted by Photon Engineering. If you have a license to the
# FRED software, you may generate and save these data files for your own usage,
# but you may not distribute them without express permission from Photon
# Engineering. Setting the DISTRIBUTABLE flag to True will create sanitized
# distributable data structure files, but they will be a lot less informative
# since all of the native FRED documentation will be missing.
DISTRIBUTABLE=False

# Regex for stripping extraneous CR/LF
CRLF=re.compile('[\r\n]\s*[\r\n]')
# Regex to capture carriage return and/or linefeed
COMMA=re.compile('[\r\n]\s*')
# Regex to capture "space commas"
SPCOM=re.compile('\s+,')
# Regex to match any space at all
SPMAT=re.compile('\s+')
# Regex to match space parens
SPAR=re.compile('\s+\)')
# Regex to match unicode word for word extraction
WORDMAT=re.compile('\w+')
# Regex to match ByVal/ByRef and surrounding whitespace
BYVALMAT=re.compile('\s*(byval|byref)\s*', re.IGNORECASE)
# Regex to match any case of " As "
# Increase sophistication by enforcing only matching when followed
# by a known VB data type
# Also include matching on type in parentheses without the As
tmat = "|".join(glovars.TYPEMAP.keys()) + "|T_"
ASMAT=re.compile('\s+(?:As|\()\s+(?=(?:{}))'.format(tmat), re.IGNORECASE)
# Regex to match html hash references at end of string
HASHMAT=re.compile('#.*$')
# Regex to match version number
VMAT = re.compile('(\d+)\.(\d+)\.(\d+)')
# Set of python reserved keywords
PYKWS = set(keyword.kwlist)

class FileNotFound(Exception):
    pass

def stripcrlf(s):
    """
    Strip extraneous carriage return/line feed out of s
    """
    return CRLF.sub('\n', s.lstrip('[\r\n]')).rstrip()

def cr2comma(s):
    """
    Replace a carriage return and or linefeed with ', '
    """
    return COMMA.sub(', ', s.rstrip())

def photonify(path):
    '''
    Append the Photon Engineering directory to the supplied path name
    '''
    return os.path.join(path, 'Photon Engineering')

def helpsearch(path):
    '''
    Return a list of paths we found to the help file if we find one or
    more. Otherwise return the empty list.
    '''
    matches = []
    for root, dirs, files in os.walk(path):
        # Match case insensitively
        lowerfiles = [_.lower() for _ in files]
        try:
            # Append match to matches list
            filename = files[lowerfiles.index(glovars.CHMFILE.lower())]
            matches.append(os.path.join(root, filename))
        except ValueError:
            # Not found, do nothing
            pass
    return matches

class LinksLocator(HTMLParser):
    """
    LinksLocator is a class for retrieving name and path (Name and Local)
    Code based on original reference here:
      https://code.activestate.com/recipes/
              502221-extracting-data-from-chm-microsoft-compiled-html/
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_obj = False
        self.nodes = []
        self.in_a = False
        self.links = []

    def handle_starttag(self, tag, attr):
        if tag == 'object':
            self.in_obj = True
            self.new_node = {}
        elif tag == 'param' and self.in_obj:
            attr = dict(attr)
            name = attr['name']
            if name in ('Name', 'Local'):
                self.new_node[name] = attr['value']
        elif tag == 'a':
            attr = dict(attr)
            self.in_a = True
            self.lnk = {'Local': attr.get('href')}
            self.data = ''

    def handle_endtag(self, tag):
        if tag == 'object':
            self.in_obj = False
            if self.new_node != {}:
                self.nodes.append(self.new_node)
        elif tag == 'a':
            self.in_a = False
            # if link has an adress
            if self.lnk.get('Local'):
                self.lnk['Name'] = self.data
                self.links.append(self.lnk)
    def handle_data(self, data):
        if self.in_a:
            self.data += data

class GrabDoc(HTMLParser):
    """
    Use for getting the relevant documentation info from html document
    """
    def __init__(self):
        # Inherit parent's init
        HTMLParser.__init__(self)
        #self.docdict = OD()
        self.docdict = dict()
        self._dockey = ''
        self._dockeybool = False
        self._valuebool = False
        self._valuestr = ''
        self.keepdoc = False # Flag to indicate we should keep this doc

    def handle_starttag(self, tag, attrs):
        # Class tags for dockeys
        dkeycls = {'ts14', 'ts7'}
        if tag == 'span':
            for attr in attrs:
                if attr[0] == 'class':
                    if attr[1] in dkeycls:
                        # The data here is a dockey
                        self._dockeybool = True
                        # Flag it for keeping
                        self.keepdoc = True
                        # If we've been filling up _valuestr, commit it now
                        if self._valuebool and self._dockey != '':
                            self._flush2dict()
                            # Purge _valuestr for the next section
                            self._valuestr = ''
                            self._valuebool = False
        # Add linebreaks for br tag
        # Useful for breaking out argument lists that are not divided
        # up with pargraph breaks
        if tag == 'br':
            self._valuestr += '\n'

    def handle_endtag(self, tag):
        if tag == 'body':
            # Document ended. Flush what's built up in _dockey and _valuestr
            self._flush2dict()

    def _flush2dict(self):
        '''
        Flush the _dockey and _valuestr to docdict
        '''
        valdata = stripcrlf(self._valuestr)
        if (self._dockey.lower().startswith("used as parameter") or
            self._dockey.lower().startswith("see also")):
            valdata = cr2comma(valdata)
        self.docdict[self._dockey] = valdata

    def handle_data(self, data):
        if self._dockeybool:
            self._dockey = data
            self._dockeybool = False
            self._valuebool = True
        elif self._valuebool:
            self._valuestr += data.lstrip('[ \t\f\v]').rstrip('[ \t\f\v]') + ' '

def hrdocsave(outname, keys, cmddict):
    '''
    Format and save supplied "keys" to a human readable document "outname"
    '''
    print("\nSaving human readable documentation to {}.".format(outname))
    with codecs.open(os.path.join(glovars.DATADIR, outname) + '.txt',
                    'w', 'utf-8') as fid:
        for cmdname in keys:
            print("... writing {}".format(cmdname))
            docstr = ''
            for k, v in cmddict[cmdname].items():
                # Heading
                docstr += "\n{}:\n".format(k)
                # Format the content
                leadin = '  ' # Indentation string
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
                            docstr += leadin * (c%2+1) + conlines[c] + "\n"
                if not parambool:
                    for c in range(len(conlines)):
                        docstr += leadin + conlines[c] + "\n"
            fid.write("\n" + "=" * 80 + "\n")
            topstr = "TOPIC: {}\n".format(cmdname)
            fid.write(topstr)
            fid.write("-"*len(topstr) + "\n")
            fid.write(docstr)

def main():
    """
    Encapsulate script procedural body here so it can be externally
    referenced as <filename>.main or automatically invoked from the
    if __name__ == "__main__"" statement when the script is run directly.
    """

    if glovars.CHMAUTOLOCATE:
        # Build up some directories we should search through to find the help
        # file.  The {} set will prevent duplicate paths and the sorted will
        # put paths not suffixed with x86 ahead of x86 suffixed paths.
        try:
            basepaths = sorted({os.environ['PROGRAMW6432'],
                                os.environ['PROGRAMFILES'],
                                os.environ['PROGRAMFILES(X86)']})
            basepaths = [photonify(pth) for pth in basepaths]
        except KeyError:
            # Probably not running on Windows. Check some local directories
            # to see if we can scrounge up the help file.
            basepaths = [glovars.CWD, glovars.DATADIR]

        # Try each of basepaths until we match
        for path in basepaths:
            matches = helpsearch(path)
            if matches != []:
                # If we found something, we're good to go.
                break
        else:
            raise FileNotFound("Could not locate file: {}".
                                format(glovars.CHMFILE))

        # To get the latest helpfile split out the version numbers
        versions = []
        for mstr in matches:
            vmat = VMAT.search(mstr)
            vtuple = tuple(int(_) for _ in vmat.group(1, 2, 3))
            versions.append(vtuple)
        # Sort versions and the last element is the newest version number
        ver_index = versions.index(sorted(versions)[-1])
        helpfile = matches[ver_index]
    else: # glovars.CHMAUTOLOCATE is False
        # Get the helpfile path information from glovars.CHMPATH
        helpfile = os.path.join(glovars.CHMPATH, glovars.CHMFILE)
    print("Will extract API information from:\n {}".format(helpfile))
    # Comment out for now to save time since we've already collected the html files
    # Use hh.exe to decompile the chm.
    print("\nDecompiling file:\n {}\nto HTML files in directory:\n {}".format(
            helpfile, glovars.HTMLDIR))
    if not os.path.exists(glovars.HTMLDIR):
        os.makedirs(glovars.HTMLDIR)
    # Make the current working directory the path where the helpfile is for
    # cases when referencing path on a different drive causes problems.
    os.chdir(os.path.dirname(helpfile))
    try:
        subprocess.check_call(['hh.exe', '-decompile',
                              glovars.HTMLDIR, glovars.CHMFILE])
    except OSError:
        print("WARNING: Unable to invoke help file decompiler.\n"
              " Will attempt to continue, but help files must be"
              " unpacked here:")
        print(glovars.HTMLDIR)

    # Go back to our working directory:
    os.chdir(glovars.CWD)

    # The table of contents should be in FREDHelp_02.hhc. It's possible the prefix
    # could change, so just pick up the first .hhc file we can find:
    allfiles = os.listdir(glovars.HTMLDIR)
    tocfile = next((i for i in allfiles if i.endswith('.hhc')))
    print("\nFound table of contents file: {}".format(tocfile))

    tocparser = LinksLocator()
    tocparser.feed(utils.readfile(os.path.join(glovars.HTMLDIR, tocfile)))
    tocstruct = tocparser.nodes
    # tocstruct is now a list of dictionaries. Each dict having a key's of
    # "Local" and "Name". The value of "Name" being the command name and the
    # value of "Local" being the filename.htm that contains the documentation.

    # Create a dictionary to index topic name to the appropriate html file:
    ktops = dict() # "Key Topics"
    for d in tocstruct:
        try:
            # Valid commands that we can build an API for do not have any
            # spaces in their name. If we match a space, skip to the next.
            if SPMAT.search(d['Name']) is not None:
                print("... bypassing {}".format(d['Name']))
                continue
            filepath = os.path.join(glovars.HTMLDIR, d['Local'])
            # Strip off any html hash referrers on the end if necessary
            filepath = HASHMAT.sub('', filepath)
            ktops[d['Name']] = filepath
        except KeyError:
            # Any dicts that don't have a 'Name' or 'Local' key may be passed over
            pass

    cmddict = {} # "Command dictionary"
    # Iterate over each topic and build up the api/documentation datastructures
    for docname in ktops.keys():
        print("... parsing {}".format(docname))
        html = utils.readfile(ktops[docname])
        # Parse the html for this topic with our custom GrabDoc class:
        docgrab = GrabDoc()
        docgrab.feed(html)
        if docgrab.keepdoc:
            cmddict[docname] = docgrab.docdict
        docgrab.close()

    sortcmds = sorted(cmddict.keys()) # "Sorted commands" list
    apidict = {} # "API dictionary" datastructure
    print("\nBuilding API Data structures...")
    # Iterate over every "Command name"
    for cmdname in sortcmds:
        print("... building {}".format(cmdname))
        # Clear "Returned list"
        retlist = []
        # Initialize "Signature dictionary" as an OrderedDict
        #sigitems = OD()
        #sigitems = dict()
        sigitems = list()
        # Parameter indicating whether we have a function or a subroutine
        if cmdname.startswith('T_'):
            cmdtype = 'datastruct'
        else:
            try:
                if cmddict[cmdname]['Syntax'].find("=") == -1:
                    cmdtype = 'subroutine'
                else:
                    cmdtype = 'function'
            except KeyError:
                cmdtype = 'unknown'

        # Capture Parameters
        try:
            if 'Parameters' in cmddict[cmdname]:
                parkey = 'Parameters'
            elif 'Definition' in cmddict[cmdname]:
                parkey = 'Definition'
            else:
                # Lacking a Parameters or Definition heading, some
                # documentation mistakenly calls it Syntax
                if 'Syntax' in cmddict[cmdname]:
                    parkey = 'Syntax'
                else:
                    raise ValueError('No signature detected')
            params = cmddict[cmdname][parkey].split('\n')
            # Strip out any extraneous "ByVal" decorators
            params = [BYVALMAT.sub('', s) for s in params]
            # If there's an "as <type>" change it to "As <type>"
            params = [ASMAT.sub(' As ', s) for s in params]
            # If this is cmdtype == 'function' the first line of params
            # should give us the return information. It could be formatted
            # as: 'var (Type)' or 'var As Type' and we need to handle both.
            if cmdtype == 'function':
                retlist = WORDMAT.findall(params[0])
                try:
                    retlist.remove('As')
                except ValueError:
                    pass
                # Handle case where we've caught more then a param/type pair
                if len(retlist) > 2:
                    retlist = [retlist[0], " ".join(retlist[1:])]
                cmddict[cmdname]['Returns'] = " As ".join(retlist)
                # Remove from params so we don't add it to the parameters sig
                params.remove(params[0])
            # ASMAT only splits on "As <type>" occurrences:
            for vartyp in [ASMAT.split(par) for par in params]:
                # Build up boolean condition list for confirming match on a
                # signature. Then evaluate list with python builtin all()
                # as the gate for whether to collect the signature.

                # Only bother if we split out a name, type pair
                pairbool = len(vartyp) == 2
                # Use MAXVARLEN because sometimes we might have matched
                # on an "As" in some descriptive text.
                lenbool = len(vartyp[0]) <= MAXVARNLEN
                # If there's a "." in there, it's descriptive text. Only
                # consider cases that did not match a period.
                nontxtbool = "".join(vartyp).find(".") == -1
                if all([pairbool, lenbool, nontxtbool]):
                    k, v = map(lambda x: x.strip(), vartyp)
                    # Add an "_" if the param name is python reserved
                    if k in PYKWS:
                        k += '_'
                    # Strip any space-parens
                    v = SPAR.sub('', v)
                    sigitems.append([k, v])
        except ValueError:
            # Catch ValueError if we don't find a signature
            pass

        # Leave out the Photon Engineering description field to exclude
        # content which is copyrighted by Photon Engineering:
        if DISTRIBUTABLE:
            descr = "Wrapper stub for {}".format(cmdname)
        else:
        # OK to use Photon copyrighted descriptions for ourself as long as
        # we don't distribute it:
            try:
                descr = cmddict[cmdname]['Description'].strip()
            except KeyError:
                descr = "No description found"
        apidict[cmdname] = {'descr': descr,
                            'sig': sigitems,
                            'returns': retlist,
                            'cmdtype': cmdtype}

    if DISTRIBUTABLE:
        # Purge copyrighted documentation
        print("\nPurging copyrighted material from datastructure...")
        for cmdname in cmddict.iterkeys():
            cmddict[cmdname] = {'Documentation': 'Not Available'}

    # Save out a non-overridden datastructure for inspection
    apitmp = glovars.APIFILE.rsplit('.', 1)
    apitmpfile = "{}_no-override.{}".format(*apitmp)
    print("\nSaving raw API datastructure to file:\n {}".
            format(apitmpfile))
    utils.writefile(os.path.join(glovars.DATADIR, apitmpfile),
                    yaml.dump(apidict))

    # Before we save the data out to the API file, apply any overrides
    with open(glovars.APIOVERRIDEPATH, 'r') as fid:
        odat = yaml.load(fid.read())
    for ocmd, odict in odat.items():
        for k, v in odict.items():
            apidict[ocmd][k] = v
    print("\nSaving API datastructure to file:\n {}".
            format( glovars.APIFILEPATH))
    utils.writefile(glovars.APIFILEPATH, yaml.dump(apidict))

    # Save out all of the collected documentation as a yaml datastructure
    utils.writefile(os.path.join(glovars.DATADIR, DOCFILE) + '.yaml', yaml.dump(cmddict))
    # Save out all of the collected documentation in human readable format
    hrdocsave('alldocs', sortcmds, cmddict)

    # Save out documentation specific to the cmdtype
    savinfo = {'function': 'allfuncts', 'subroutine': 'allsubs',
               'datastruct': 'allstructs', 'unknown': 'allunknowns'}
    for cmdtype, savname in savinfo.items():
        savkeys = [k for k in sortcmds if apidict[k]['cmdtype'] == cmdtype]
        hrdocsave(savname, savkeys, cmddict)

    print("Successfully wrote: {}".format(glovars.APIFILEPATH))

if __name__ == "__main__":
    # If this script is invoked directly (not imported), execute main()
    main()
