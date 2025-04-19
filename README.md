# pyfred
Python wrapper for Photon Engineering's FRED software

> [!WARNING]
> pyfred is no longer under active development.
>
> The help file from new versions of FRED will not be correctly
> parsed for generating the required API to use pyfred.
> Although, it may still be possible to get pyfred to work by using
> the help file from an older FRED version (like FRED 16 or 17).

## Description
pyfred provides pythonic bindings into a FRED document and a consistent API
for using FRED through the win32 COM interface without having to worry about
the nuances and quirks associated with the raw win32 API.

Some advantages this provides are:

- Use of familiar Python idioms for scripting
- Availability of a vast amount of mature python libraries
- Interactive access to your model using the powerful IPython shell
- Use of the Jupyter Notebook for documentation, reporting and workflow

## Installation
pyfred is written and tested in Python 3.

pyfred has not yet been "packaged" so the installation process is
completely manual. The following instructions provide some helpful
guidelines but you will  need to be well versed in your own specific
python installation for troubleshooting purposes.

### Downloading
Currently pyfred is only available through GitHub. Grab the latest
version using
```bash
    $ git clone https://github.com/artdavis/pyfred
```
Alternatively, use a browser to navigate to
`https://github.com/artdavis/pyfred` and use the "Clone or download"
button to "download zip" and decompress into your folder of choice.

*IMPORTANT*: The cloned or unzipped package will have within it a
subdirectory named `pyfred`. You should see python files in there like
`core.py`, `script00_verify_libraries.py` and others. It is this
directory which must be located inside of python's search path.
For example, if you have a project directory in your PYTHONPATH called
`C:\Users\username\Documents\python` you could put the pyfred directory
there: `C:\Users\username\Documents\python\pyfred`. Test that it works:
```bash
    $ python -c 'import pyfred'
```
If there are no reported errors then the path is good. If you get
a `ModuleNotFoundError` then you need to troubleshoot getting pyfred
into python's search path.


### Required libraries
pyfred requires some standard library add-ons:
`numpy`, `IPython`, `win32com`, which will
typically be available if you've installed Python from a pre-packaged
distribution.

pyfred also requires `PyYAML` (http://pyyaml.org/wiki/PyYAML).

Preferably install missing packages using your primary package manager
assuming they're available there. Otherwise you may find and install
them via `pip`.

The availability of the necessary libraries can be tested by running
the included `script00_verify_libraries.py`. If this script runs with
no errors you are in good shape to move on to the next step.

### Building
pyfred must first build it's API from the FRED help file. It will look
in the most logical places, but if it can't find it, or you have a specific
version of a help file you want to use, you'll have to specify its location
manually (in `glovars.py` set `CHMAUTOLOCATE=False` and specify the location
of `Fred.chm` in `CHMPATH`).

Run the script0[1-4] files in order:

This first script decompiles the FRED help file for generating pyfred's API:
```bash
    $ python script01_winparse_chm.py
```

script02 creates the VBScript stub programs:
```bash
   $ python script02_stubgen.py
```

The third script wraps the FRED interface in python and creates pyfred's API:
```bash
    $ python script03_apiwrapgen.py
```

The fourth script will check that the API has been built and can be imported:
```bash
    $ python script04_confirm_import.py
```

## Usage
Have a look through the files in the `examples` subdirectory.

First thing to try is to run `examples\raw_create_doc.py`. This launches
FRED and creates a simple document with a plane element. This script only
uses the raw COM interface (pyfred is not used at all). If FRED does not launch
and create a document with a plane then python is not able to communicate
with FRED and you've got some troubleshooting to do.

If that's working, next try running `examples\core_pyfred_doc.py` which will
create a similar FRED document except it uses the pyfred API. It's also a good
example for demonstrating the intended usage of pyfred.

## Tutorial

There is a tutorial document that demonstrates various pyfred functionality in
`examples\jupyter_notebook_pyfred_tutorial`. Ideally you would open the
`.ipynb` version of the file in a Jupyter Notebook and interactively run
through cell by cell.  You may also read the non-interactive `.pdf` version of
the tutorial as well.

## License
pyfred is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

See LICENSE for details.

## Disclaimer
pyfred is not affiliated with Photon Engineering LLC.
