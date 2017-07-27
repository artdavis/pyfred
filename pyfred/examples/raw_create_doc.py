#!/usr/bin/env python
"""
Create a FRED test document using just the raw COM interface
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
Demonstrate usage of the pure win32com interface without using pyfred
"""
import os

import win32com.client as w32

DOCNAME = 'fredtestdoc'

app = w32.Dispatch("FRED.Application")
app.Visible = True
dobj = app.SysNew(DOCNAME)
geomid = dobj.FindFullName("Geometry")

# Add Custom Element
ent = w32.Record('T_ENTITY', dobj)
ent.parent = geomid
ent.name = "Custom Element"
ent.traceable = True
elem1_id, elem1_ent = dobj.AddCustomElement(ent)

# Add a plane as a child to the Custom Element
ent.parent = elem1_id
ent.name = "Custom Plane"
plane_id, plane_ent = dobj.AddPlane(ent)

# Update the live document
dobj.Update()

# When done, you can close everything out using:
#app.CloseFred()
# Or close just this document without saving:
# (theoretically, but it doesn't work, TODO: debug)
#app.SysCloseNoSave(DOCNAME)
