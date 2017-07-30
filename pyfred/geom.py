#!/usr/bin/env python
"""
Geometry creation convenience class/functions for pyfred
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
"""

from collections import MutableSequence as MS
from . import apicmds as api
from . import webcolors as wc

class ListProp(MS):
    """
    Custom list collection class to propagate changes to it's list
    elements into the FRED document
    """
    def __init__(self, parent, countcmd, getcmd, setcmd, addcmd, delcmd,
            dstruct, rix=2):
        """
        Parameters
        ----------
        parent: self namespace of the parent
        getcmd: str
            FRED command string to get element (e.g. "GetOperation")
        setcmd: str
            FRED command string to set element (e.g. "SetOperation")
        addcmd: str
            FRED command string to add element (e.g. "AddOperation")
        getcmd: str
            FRED command string to delete element (e.g. "DeleteOperation")
        rix: int
            Index of the return operation that contains the datastructure
            of interest (default: 2).
        """
        self._parent = parent
        self._objid = self._parent.objid
        self._countcmd = countcmd
        self._counter = getattr(self._parent._API, self._countcmd)
        self._getcmd = getcmd
        self._getter = getattr(self._parent._API, self._getcmd)
        self._setcmd = setcmd
        self._setter = getattr(self._parent._API, self._setcmd)
        self._addcmd = addcmd
        self._adder = getattr(self._parent._API, self._addcmd)
        self._delcmd = delcmd
        self._deleter = getattr(self._parent._API, self._delcmd)
        self._dstruct = self._parent._DSTRUCT(dstruct)
        self._rix = rix

    def __repr__(self):
        # Represent by the element list
        elist = [repr(x) for x in self.elements]
        return "[" + ",\n".join(elist) + "]"

    @property
    def elements(self):
        self._elements = list()
        # Actively parse out the elements from the FRED doc
        for i in range(self.__len__()):
            # Tuple index self._rix return contains the data struct
            self._elements.append(self.__getitem__(i))
        return self._elements

    @property
    def count(self):
        return len(self)

    def __len__(self):
        # Query the FRED doc directly for length
        return self._counter(self._objid)

    def __getitem__(self, idx):
        # Query the FRED doc directly for the item
        return self._getter(self._objid, idx, self._dstruct)[self._rix]

    def __setitem__(self, idx, value):
        # Set the item directly in the FRED doc
        self._setter(self._objid, idx, value)
        self._parent._DOBJ.Update()

    def __delitem__(self, idx):
        # Delete the item directly in the FRED doc
        self._deleter(self._objid, idx)
        self._parent._DOBJ.Update()

    def insert(self, idx, value):
        # Get the list from the document
        elems = self.elements
        pelems = list()
        # Pop items back to idx
        for i in range(self.__len__()-1, idx-1, -1):
            pelems.append(elems.pop())
            self.__delitem__(i)
        # Add the new value
        self._adder(self._objid, value)
        # Put popped items back on
        for i in range(len(pelems)):
            self._adder(self._objid, pelems.pop())
        self._parent._DOBJ.Update()

class OpCollection(ListProp):
    """
    Data structure to hold list of T_OPERATION data structures
    and provide methods for querying/updating

    Instantiate inside a Geom class so self should already
    have self._fdoc and self._OP attributes
    """
    def __init__(self, parent):
        # Use ListProp class' __init__ with appropriate parameters for
        # T_OPERATION
        super(OpCollection, self).__init__(
                parent,
                countcmd='GetOperationCount',
                getcmd='GetOperation',
                setcmd='SetOperation',
                addcmd='AddOperation',
                delcmd='DeleteOperation',
                dstruct='T_OPERATION',
                rix=2)

class Geom(object):
    """
    Base class for geometry classes to be used for inheriting

    Parameters
    ----------
    fdoc: FRED document object
    """
    def __init__(self, fdoc, color='darkblue'):
        self._color = color
        self._fdoc = fdoc
        self._ENT = self._DSTRUCT('T_ENTITY')
        self._TRIM = self._DSTRUCT('T_TRIMVOLUME')
        self._OP = self._DSTRUCT('T_OPERATION')
        self._OPDIR = self._DSTRUCT('T_OPERATION')
        self._OPDIR.Type = 'RotateToDirection'
        self._OPDIR.val3 = 1.0
        self._VIS = self._API.InitSurfVisualize(
                self._DSTRUCT('T_SURFVISUALIZE'))
        self._opacity = self._VIS.opacity
        self._tess = None
        # Be sure child class sets a self.objid object identifier for the FRED
        # object to operate on
        self.objid = None

    @property
    def _FDOC(self):
        return self._fdoc

    @property
    def _DOBJ(self):
        return self._fdoc.dobj

    @property
    def _API(self):
        return api.Wrap(self._DOBJ)

    @property
    def _DSTRUCT(self):
        return self._FDOC.struct

    @property
    def _GEOMID(self):
        return self._DOBJ.FindFullName('Geometry')

    @property
    def ENTITY(self):
        """
        Attribute property holding the plane entity. Actively
        queries the FRED document so should always represent the
        current state.
        """
        return self._API.GetEntity(self.objid, self._ENT)[1]
    @ENTITY.setter
    def ENTITY(self, dstruct):
        """
        Actively set and update the document with supplied entity
        FRED data structure
        """
        self._ENT = self._API.SetEntity(self.objid, dstruct)[1]
        self._DOBJ.Update()

    @property
    def TRIM(self):
        """
        Attribute property holding the TRIMVOLUME data. Actively
        queries the FRED document so should always represent the
        current state.
        """
        return self._API.GetTrimVolume(self.objid, self._TRIM)[1]
    @TRIM.setter
    def TRIM(self, dstruct):
        """
        Actively set and update the trimming volume
        FRED data structure
        """
        self._TRIM = self._API.SetTrimVolume(self.objid, dstruct)[1]
        self._DOBJ.Update()

    @property
    def VIS(self):
        """
        Attribute property holding the SURFVISUALIZE data. Actively
        queries the FRED document so should always represent the
        current state.
        """
        return self._API.GetSurfVisualize(self.objid, self._VIS)[1]
    @VIS.setter
    def VIS(self, dstruct):
        """
        Actively set and update the surface visualization
        FRED data structure
        """
        self._VIS = self._API.SetSurfVisualize(self.objid, dstruct)[1]
        self._DOBJ.Update()

    @property
    def opacity(self):
        return self._opacity
    @opacity.setter
    def opacity(self, opacity):
        self._VIS.opacity = opacity
        self.VIS = self._VIS

    @property
    def color(self):
        return self._color
    @color.setter
    def color(self, color):
        self._R, self._G, self._B = wc.name_to_rgb(color)
        self._VIS.AmbientR = self._R // 2
        self._VIS.AmbientG = self._G // 2
        self._VIS.AmbientB = self._B // 2
        self._VIS.DiffuseR = self._R
        self._VIS.DiffuseG = self._G
        self._VIS.DiffuseB = self._B
        self._VIS.tesselateScaleX = 0.5
        self._VIS.tesselateScaleY = 0.5
        self._VIS.tesselateScaleZ = 0.5
        self.VIS = self._VIS

    @property
    def tess(self):
        """
        Geometry tesselation for 3D View plot
        """
        return self._tess
    @tess.setter
    def tess(self, tscale):
        self._tess = tscale
        set_tess(self, tscale)

    @property
    def fullname(self):
        return self._API.GetFullName(self.objid)

def set_tess(instance, tscale):
    """
    Set the XYZ tesselation for the supplied instance to the
    provided value of tscale
    """
    instance._VIS.tesselateScaleX = tscale
    instance._VIS.tesselateScaleY = tscale
    instance._VIS.tesselateScaleZ = tscale
    instance.VIS = instance._VIS

class SimplePlane(Geom):
    """
    Simple plane geometry class

    Parameters
    ----------
    fdoc: FRED document object
    width: float
        Plane width (default: 1.0)
    height: float
        Plane height (default: 1.0)
    parent: int, optional
        Index of the parent geometry id (default: top-level "Geometry")
    name: str, optional
        Name to give the plane entity (default: "Simple Plane")
    description: str, optional
        Description to give the plane entity
        (default: "A simple rectangular plane")
    traceable: bool, optional
        Flag to indicate whether surface is traceable (default: True)
    never_traceable: bool, optional
        Flag to indicate whether surface is never traceable regardless of
        the state of the traceable flag (default: False)
    color: str, optional
        A webcolors (CSS3) recognized color string (default: 'CornflowerBlue')
    """

    def __init__(self, fdoc, width=1.0, height=1.0,
            parent=None,
            name="Simple Plane",
            description="A simple rectangular plane",
            traceable = True,
            never_traceable = False,
            color = 'CornflowerBlue'):
        # Inherit our parent class init with the document object
        super(SimplePlane, self).__init__(fdoc, color=color)
        # Provides _fdoc, ENT, TRIM, VIS data structures
        self._width = width
        self._height = height
        if parent is None:
            self._ENT.parent = self._GEOMID
        else:
            self._ENT.parent = parent
        self._ENT.name = name
        self._ENT.traceable = traceable
        self._ENT.neverTraceable = never_traceable
        self._ENT.description = description
        self.objid = self._API.AddPlane(self._ENT)
        # OpCollection needs the objid to be already set
        self.OPS = OpCollection(self)

        self._trimid, self._TRIM = self._API.GetTrimVolume(
                self.objid, self._TRIM)
        self._TRIM.box = True
        self._TRIM.xSemiApe = self._width / 2.
        self._TRIM.ySemiApe = self._height / 2.
        self.TRIM = self._TRIM

        self._VIS.axesNegLengthX = self._width
        self._VIS.axesPosLengthX = self._width
        self._VIS.axesNegLengthY = self._height
        self._VIS.axesPosLengthY = self._height
        self.VIS = self._VIS
        self.color = self._color

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, val):
        self._width = val
        self._TRIM.xSemiApe = self._width / 2.
        self.TRIM = self._TRIM
        self._VIS.axesNegLengthX = self._width
        self._VIS.axesPosLengthX = self._width
        self.VIS = self._VIS

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, val):
        self._height = val
        self._TRIM.ySemiApe = self._height / 2.
        self.TRIM = self._TRIM
        self._VIS.axesNegLengthY = self._height
        self._VIS.axesPosLengthY = self._height
        self.VIS = self._VIS

    def __repr__(self):
        return repr(self.ENTITY)

    def __str__(self):
        outstr = ""
        s = "{}={}"
        keys = [k for k in dir(self.ENTITY) if not k.startswith('_')]
        keyvals = [s.format(k, getattr(self.ENTITY, k)) for k in keys]
        return "{}({})".format(self.__class__.__name__, ", ".join(keyvals))

