#!/usr/bin/env python
"""
Core pyfred module
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
"""
import os
import numpy as np
import math

import win32com.client as w32
from . import apicmds as api
from . import utils as u

CWD=os.path.dirname(os.path.abspath(__file__))
MODNAME = os.path.splitext(os.path.basename(__file__))[0]
SCRIPTPATH = 'cmdscripts' # Directory holding scriptlib command scripts

class ScriptLib(object):
    """
    Provide a function based on compiling a script using dobj.CreateLib()

    The <command>.frs must exist in the path SCRIPTPATH and the VBScript there
    must define a function named "libfunct"

    Parameters
    ----------
    dobj: FRED document object
    command: str
        Command name to create a function for
    """
    def __init__(self, dobj, command):
        stubpath = os.path.join(CWD, SCRIPTPATH,
                                "{}.frs".format(command))
        self._libfunct = dobj.CreateLib(stubpath).libfunct

    def __call__(self, *args):
        # An instantiated object is a functor and may be called
        if 0 == len(args):
            return self._libfunct(None)
        else:
            return self._libfunct(*args)

class ComLib(object):
    """
    Provide a function by directly using the COM interface

    Parameters
    ----------
    dobj: FRED document object
    command: str
        Command name to create a function for
    """
    def __init__(self, dobj, command):
        self._libfunct = getattr(dobj, command)

    def __call__(self, *args):
        # An instantiated object is a functor and may be called
        return self._libfunct(*args)

class FunctGetter(object):
    """
    Use to abstract away the complexities of creating a working FRED function
    through the COM interface. If the command name exists as a script then
    create a functor using ScriptLib. Otherwise create using ComLib.

    Parameters
    ----------
    dobj: FRED document object
    command: str
        Command name to create a function for
    """
    def __init__(self, dobj, command):
        self._dobj = dobj
        self._command = command

    def __call__(self, *args):
        # Check whether command exists in SCRIPTPATH
        if os.path.isfile(os.path.join(CWD, SCRIPTPATH,
                                       self._command + '.frs')):
            # Use ScriptLib to make the function
            return ScriptLib(self._dobj, self._command)(*args)
        else:
            # Use ComLib to make the function
            return ComLib(self._dobj, self._command)(*args)

class DocCollection(object):
    """
    Superclass that provides the methods used for collection type instances.
    """
    def __init__(self, dobj):
        self._dobj = dobj
        # Define self._dstruct in accordance with the datastructure that
        # the collection type uses
        self._dstruct = None
        # Be sure to define a meaningful self._methodmap in the child class
        # which keys the method name to the VBScript command that it needs.
        self._methodmap = {'count': None,
                           'getter': None,
                           }

    def getter(self, n):
        """
        Return collection item datastructure of index 'n'.

        Parameters:
        -----------
        n : int
            Index of the collection item to retrieve
        """
        fgetter = FunctGetter(self._dobj, self._methodmap['getter'])
        gotten = fgetter(n, self._dstruct)
        # Handle idiosyncracy of sometimes getting a tuple back
        if type(gotten) is tuple:
            return gotten[1]
        else:
            return gotten

    @property
    def count(self):
        """
        Count of the number of items in the active document
        """
        return FunctGetter(self._dobj, self._methodmap['count'])()

    @property
    def names(self):
        """
        List of the names for this collection in the active document.  The
        references are not "live"; modifying them does not propagate back to
        the active document.  The index number in the list corresponds to the
        node number in the active document
        """
        return [self.getter(_).name for _ in range(self.count)]

    @property
    def descriptions(self):
        """
        List of the descriptions for this collection in the active document.
        The references are not "live"; modifying them does not propagate back
        to the active document.  The index number in the list corresponds to
        the node number in the active document
        """
        return [self.getter(_).description for _ in range(self.count)]

class Entities(DocCollection):
    """
    Class for holding all of the entities in the active document as
    a useful datastructure instance with convenience methods.
    """
    def __init__(self, dobj, *args, **kwargs):
        # Inheret parent class' __init__:
        #super(Entities, self).__init__()
        self._dobj = dobj
        self._dstruct = w32.Record('T_ENTITY', dobj)
        self._methodmap = {'count': 'GetEntityCount',
                           'getter': 'GetEntity'}
        # Methods we want: count, names, descriptions, getter, parents,
        #                  entities, collections

    @property
    def names(self):
        """
        List of the names for this collection in the active document.  The
        references are not "live"; modifying them does not propagate back to
        the active document.  The index number in the list corresponds to the
        node number in the active document
        """
        return [self.getter(_).name for _ in range(self.count)]

    @property
    def entities(self):
        """
        List of the entity indices in the active document. The references are
        not "live"; modifying them does not propagate back to the active
        document.  The index number in the list corresponds to the entity node
        number in the active document
        """
        return [self.getter(_) for _ in range(self.count)]

    @property
    def parents(self):
        """
        List of the entity parents in the active document. The references are
        not "live"; modifying them does not propagate back to the active
        document.  The index number in the list corresponds to the entity node
        number in the active document
        """

        return [self.entities[_].parent for _ in range(self.count)]

class DocBase(object):
    """
    Class for instantiating access to a FRED document with COM interface
    and useful data structures. Work purely with a pre-existing
    document object (dobj) instance that needs to have been created
    elsewhere.
    :param dobj: Document object instance of the FRED active document
    :type visbool: instance

    TODO: This should probably be a singleton with a class attribute that
    can detect if it's been instantiated and prevent instantiation of another
    one.
    """
    def __init__(self, dobj=None):
        # Document object:
        self._dobj = dobj
        # Closure for printing to the output window
        oprintfile = 'OutputWindowPrint.frs'
        self._oprint = dobj.CreateLib(
                os.path.join(CWD, SCRIPTPATH, oprintfile)).libfunct
        # Provide various collections as attributes (TODO)
        #self.materials = Materials(self._dobj)
        #self.coatings = Coatings(self._dobj)
        #self.embeddedscripts = EmbeddedScripts(self._dobj)
        #self.groups = Groups(self._dobj)
        #self.scattermodels = ScatterModels(self._dobj)

    @property
    def entities(self):
        """
        Instantiate an Entities instance for convenient access to the
        entities in the active document.
        """
        return Entities(self._dobj)

    @property
    def dobj(self):
        """
        Attribute property for the FRED COM Interface document object
        """
        return self._dobj

    @property
    def units(self):
        """
        Attribute property holding the FRED document units. Actively retrieves
        the units using dobj.GetUnits() so should always represent the current
        units state of the document (even if it is changed outside the scope
        of pyfred).

        Also includes a setter so:

        >>> dobj.units = "unit-string"

        will work.
        """
        self.__units = self._dobj.GetUnits()
        return self.__units
    @units.setter
    def units(self, units):
        """
        Setter for the units attribute

        :param units: Units to set the FRED document to
        :type units: str
        """
        self._dobj.SetUnits(units)
        self.__units = units

    @property
    def comment(self):
        """
        Attribute property holding the FRED document comment. Actively
        retrieves the comment using dobj.GetComment() so should always
        represent the current state of the document comment (even if it is
        changed outside the scope of pyfred).

        Also includes a setter so:

        >>> dobj.comment = "comment-string"

        will work.
        """
        self.__comment = self._dobj.GetComment()
        return self.__comment
    @comment.setter
    def comment(self, comment):
        """
        Setter for the comment attribute

        :param comment: Comment to set for the FRED document
        :type units: str
        """
        self._dobj.SetComment(comment)
        self.__comment = comment

    def coprint(self, outstr):
        """
        Method for printing to the output window and to the console python
        is running from at the same time.

        Parameters
        ----------
        outstr: str
            String to print
        """
        print(outstr)
        self._oprint(outstr)

    def oprint(self, outstr):
        """
        Method for printing to the output window

        Parameters
        ----------
        outstr: str
            String to print
        """
        self._oprint(outstr)


    def struct(self, structname):
        """
        Method for returning the requested FRED data structure

        Parameters
        ----------
        structname: str
            Name of the requisite FRED data structure

        Returns
        -------
        FRED dstruct
            COM data structure for the requested FRED data structure type
        """
        return w32.Record(structname, self._dobj)

class DocInit(DocBase):
    """
    Class for initializing a FRED document with COM interface
    and useful data structures.
    """
    def __init__(self, docname='pyfred',
                       reset=False,
                       existing=False,
                       visbool=True):
        """
        Parameters
        ----------
        docname : str, default: 'pyfred'
            Name of the FRED document to initialize
        reset : boolean, default: False
            Flag to reset an open document if one with docname is already open
            (True) or to open a new version of docname regardless if one with
            that name is already open (False) - Default is False since running
            SysNewOrReset when multiple windows are open pops up a dialog in
            FRED requesting manual intervention to pick the document regardless
            if one with the requested name is already open.
        existing : boolean, default: False
            Flag to indicate we should open an existing file with SysOpen
            instead of creating a new file with SysNew
        visbool : boolean, default: True
            Flag for whether document is visible or not
        """
        # Application object:
        self._app = w32.Dispatch("FRED.Application")
        # Set it's visibility:
        self._app.Visible = visbool
        # Create the document object
        if reset:
            dobj = self._app.SysNewOrReset(docname)
        else:
            if existing:
                dobj = self._app.SysOpen(docname)
            else:
                dobj = self._app.SysNew(docname)
        # Inheret our parent class init with the document object
        # we just created
        super(DocInit, self).__init__(dobj)

    @property
    def app(self):
        """
        Attribute property for the FRED COM Interface application object
        """
        return self._app

class DocProperties(object):
    """
    Base class to provide a bunch of useful properties for accessing
    the FRED API: _FDOC, _DOBJ, _API, _DSTRUCT, _GEOMID
    """
    def __init__(self, fdoc):
        self._fdoc = fdoc

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

class Camera(DocProperties):
    """
    Class for manipulating the camera in the 3D View
    """
    def __init__(self, fdoc=None):
        super(Camera, self).__init__(fdoc)
        self._getcam()
        self._keys = ['xLoc', 'yLoc', 'zLoc',
                      'xAim', 'yAim', 'zAim',
                      'xUp', 'yUp', 'zUp']
        # Using actual zero for camera aiming has bugs
        self._z = 1e-6

    def _update(self):
        # Update the FRED document with the _CAMERA settings
        # Make sure the upvector is not colinear with the viewing vector
        # as that will cause FRED to chuck an error: TODO
        if np.isclose(u.vectangle(self._cam_upvect, self._cam_pointvect), 0):
            # Colinear upvector and pointvect is bad. Find a perpendicluar
            # vector using z axis as a reference
            self._xup, self._yup, self._zup = np.cross(
                    self._cam_upvect, [0, 0, 1])
        self._API.SetCamera(self._CAMERA)
        self._DOBJ.Update()

    def _getcam(self):
        # Get the latest CAMERA settings from the FRED document
        self._CAMERA = self._API.GetCamera(self._DSTRUCT('T_CAMERA'))


    # We can get ourself into trouble setting individual vector components
    # and updating them in the FRED document individualy. Only allow
    # setting them as a triplet. Also be sure to update the camera before
    # getting and after setting the triplet outside of the individual
    # getter/setter properties
    @property
    def _xloc(self):
        return self._CAMERA.xLoc
    @_xloc.setter
    def _xloc(self, val):
        self._CAMERA.xLoc = val
    @property
    def _yloc(self):
        return self._CAMERA.yLoc
    @_yloc.setter
    def _yloc(self, val):
        self._CAMERA.yLoc = val
    @property
    def _zloc(self):
        return self._CAMERA.zLoc
    @_zloc.setter
    def _zloc(self, val):
        self._CAMERA.zLoc = val

    @property
    def _xaim(self):
        return self._CAMERA.xAim
    @_xaim.setter
    def _xaim(self, val):
        self._CAMERA.xAim = val
    @property
    def _yaim(self):
        return self._CAMERA.yAim
    @_yaim.setter
    def _yaim(self, val):
        self._CAMERA.yAim = val
    @property
    def _zaim(self):
        return self._CAMERA.zAim
    @_zaim.setter
    def _zaim(self, val):
        self._CAMERA.zAim = val

    @property
    def _xup(self):
        return self._CAMERA.xUp
    @_xup.setter
    def _xup(self, val):
        self._CAMERA.xUp = val
    @property
    def _yup(self):
        return self._CAMERA.yUp
    @_yup.setter
    def _yup(self, val):
        self._CAMERA.yUp = val
    @property
    def _zup(self):
        return self._CAMERA.zUp
    @_zup.setter
    def _zup(self, val):
        self._CAMERA.zUp = val

    @property
    def _cam_location(self):
        return (self._xloc, self._yloc, self._zloc)
    @property
    def location(self):
        self._getcam()
        return self._cam_location
    @location.setter
    def location(self, vect):
        """
        Set the x,y,z properties from the supplied 3-vector
        """
        self._xloc = vect[0]
        self._yloc = vect[1]
        self._zloc = vect[2]
        self._update()

    @property
    def _cam_aim(self):
        return (self._xaim, self._yaim, self._zaim)
    @property
    def aim(self):
        self._getcam()
        return self._cam_aim
    @aim.setter
    def aim(self, vect):
        """
        Set the x,y,z properties from the supplied 3-vector
        """
        self._xaim = vect[0]
        self._yaim = vect[1]
        self._zaim = vect[2]
        self._update()

    @property
    def _cam_upvect(self):
        return (self._xup, self._yup, self._zup)
    @property
    def upvect(self):
        self._getcam()
        return self._cam_upvect
    @upvect.setter
    def upvect(self, vect):
        """
        Set the x,y,z properties from the supplied 3-vector
        """
        self._xup = vect[0]
        self._yup = vect[1]
        self._zup = vect[2]
        self._update()

    @property
    def aim_origin(self):
        """
        Aim the camera at the origin
        """
        self.aim = (0, 0, 0)

    @property
    def dist(self):
        """
        Return the camera distance from where it is to where it's pointing
        """
        loc = np.asarray(self.location)
        avect = np.asarray(self.aim)
        dvect = loc - avect
        return np.sqrt(np.sum(dvect**2))

    @property
    def _cam_pointvect(self):
        """
        Return the vector direction of the un-updated _CAMERA attribute
        """
        loc = np.asarray(self._cam_location)
        aim = np.asarray(self._cam_aim)
        return loc - aim
    @property
    def pointvect(self):
        """
        Return the vector direction of the camera pointing in the FRED document
        """
        loc = np.asarray(self.location)
        aim = np.asarray(self.aim)
        return loc - aim

    def _view(self, loc=None, upvect=(0,1,0)):
        """
        Change the view according to supplied parameters
        """
        self.aim_origin
        self.upvect = upvect
        self.location = loc

    @property
    def view_yup(self):
        """
        Set the up vector to the y-axis (0, 1, 0)
        """
        self.upvect = (0, 1, 0)

    @property
    def view_front(self):
        """
        Change the view to the front: +Z perpendicular to the X-Y plane
        """
        self._view(loc=(self._z, self._z, self.dist))

    @property
    def view_back(self):
        """
        Change the view to the back: -Z perpendicular to the X-Y plane
        """
        self._view(loc=(self._z, self._z, -self.dist))

    @property
    def view_right(self):
        """
        Change the view to the right side: +X perpendicular to the Y-Z plane
        """
        self._view(loc=(self.dist, self._z, self._z))

    @property
    def view_left(self):
        """
        Change the view to the left side: -X perpendicular to the Y-Z plane
        """
        self._view(loc=(-self.dist, self._z, self._z))

    @property
    def view_top(self):
        """
        Change the view to the top side: +Y perpendicular to the X-Z plane
        """
        self._view(loc=(self._z, self.dist, self._z), upvect=(0, 0, -1))

    @property
    def view_bottom(self):
        """
        Change the view to the bottom side: -Y perpendicular to the X-Z plane
        """
        self._view(loc=(self._z, -self.dist, self._z), upvect=(0, 0, 1))

    @property
    def iso_dist(self):
        """
        Calculate the coordinate distance component of an iso view
        """
        return self.dist / math.sqrt(3.)

    def view_iso(self, sector=1):
        """
        Iso view

        Parameters
        ----------
        sector: {1,2,3,4,5,6,7,8}
            Sector to place the camera in for the iso view (default: 1)
        """
        views = {1: (1,1,1), 2:(1,1,-1), 3:(-1,1,-1), 4:(-1,1,1),
                 5: (1,-1,1), 6:(1,-1,-1), 7:(-1,-1,-1), 8:(-1,-1,1)}
        d = self.iso_dist
        s = views[sector]
        self._view(loc=(d*s[0], d*s[1], d*s[2]))

    def view_sph(self, zen=20., az=45.):
        """
        Set the view in spherical coordinates
        using zenithal angle from z and azimuth around y
        """
        l = self.dist
        a = l * u.cosdg(zen) * u.sindg(az)
        b = l * u.sindg(zen)
        c = l * u.cosdg(zen) * u.cosdg(az)
        self._view(loc=(a, b, c))

    @property
    def _parameters(self):
        return {k: getattr(self._CAMERA, k) for k in self._keys}

    def __repr__(self):
        self._getcam()
        return repr(self._CAMERA)

    def __str__(self):
        self._getcam()
        p = self._parameters
        return "\n".join(["{}: {}".format(k, p[k]) for k in self._keys])

