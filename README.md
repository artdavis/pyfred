# pyfred
Python wrapper for Photon Engineering's FRED software

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
pyfred must first build it's API from the FRED help file. It will look
in the most logical places, but if it can't find it, or you have a specific
version of a help file you want to use, you'll have to specify its location
manually.

To install pyfred, run:
```bash
    $ pip install pyfred
```

Or, if you don't have pip:

```bash
    $ easy_install pyfred
```

Also if you already have the source downloaded:

```bash
    $ python setup.by install
```

There are several post-installation scripts that need to run before pyfred
will be fully installed. These scripts are called up and run automatically
during the setup.py install process. You may also run them after the fact
from the `pyfred/scripts` directory or from your local site scripts directory.
The scripts should show up as executables in your scripts directory as
program files with the prefix "pyfred_". They should be run in the following
order:

- `$ python script01_winparse_chm.py`
  - Decompiles the FRED help file for generating pyfred's API
- `$ python script02_stubgen.py`
  - Creates the VBScript stub programs
- `$ python script03_apiwrapgen.py`
  - Create pyfred's the API which wraps the FRED interface in python

## License

pyfred is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

See LICENSE for details.

## Disclaimer

pyfred is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

pyfred is not affiliated with Photon Engineering LLC.
