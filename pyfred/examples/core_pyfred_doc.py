#!/usr/bin/env python
"""
Create a FRED test document using pyfred.core
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
Use pyfred core library to create a FRED test document without directly
using the win32com interface.
"""
import os

from pyfred import core as pyfred
from pyfred import apicmds

# Global variables to hold data structures
FDOC = pyfred.DocInit('testdoc')
DOBJ = FDOC.dobj # Provides raw access to the COM interface
ENT = FDOC.struct('T_ENTITY')
ENT.traceable = True

# The python wrapped version of FRED's API will be available in api:
api = apicmds.Wrap(DOBJ)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Create a Custom Element Entity
# --------------------------------
geomid = DOBJ.FindFullName("Geometry")
ENT.parent = geomid
namestr = 'Custom Element'
ENT.name = namestr
# AddCustomElement returns a tuple of id, entity
elem_id, elem_ent = DOBJ.AddCustomElement(ENT)

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Add a plane as a child to the Custom Element
# --------------------------------------------
namestr = 'Custom Plane'
ENT.name = namestr
ENT.parent = elem_id
# AddPlane returns a tuple of id, entity
plane_id, plane_ent = DOBJ.AddPlane(ENT)

# Bring the live document up to date with our shenanigans:
DOBJ.Update()

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Access the raw COM interface through DOBJ.
# Using the raw Getter functions does not
# properly retrieve objects out of the active document.
# We just get back the prototype that we used.
# --------------------------------------------
namestr = 'Bogus entity name' # Bogus name to give the ENT prototype
ENT.name = namestr
ent_gotten = DOBJ.GetEntity(elem_id, ENT)
# If that had worked, ent_gotten should no longer be 'Bogus entity name'
print("\nUsing raw COM interface:")
try:
    assert(ent_gotten.name != namestr)
    print("PASS! The COM interface has been fixed!")
except AssertionError:
    print("Got entity name of: {}".format(ent_gotten.name))
    print("Expected entity name of: {}".format(elem_ent.name))

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# The python wrapped version of the getters DOES work to retrieve object
# information out of the active document. Also the returned value is as
# per the documentation yielding a tuple of (node_id, T_ENTITY) whereas
# through the COM interface you may or may not get the same data structure
# as per the documentation.
# --------------------------------------------
ENT.name = namestr
id_gotten, ent_gotten = api.GetEntity(elem_id, ENT)
print("\nUsing pyfred interface:")
assert(id_gotten == elem_id)
assert(ent_gotten.name != namestr)
assert(ent_gotten.name == elem_ent.name)
print("Got entity name of: {}".format(ent_gotten.name))
print("Expected entity name of: {}".format(elem_ent.name))
