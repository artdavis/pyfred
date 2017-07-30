#!/usr/bin/env python
"""
pyfred utilities
===============================================================================
Copyright 2017, Arthur Davis
Email: art.davis@gmail.com
This file is part of pyfred. See LICENSE and README.md for details.
----------
"""
import numpy as np
import math

pi = math.pi # Pi
degrees = math.degrees # Convert radians to degrees function
radians = math.radians # Convert degrees to radians function
r2d = degrees(1.) # Multiply radian angle by this to convert to degrees
d2r = radians(1.) # Multiply degree angle by this to convert to radians
sqrt = math.sqrt # Square root function
sin = math.sin # Sine of radian angle function
sindg = lambda x: sin(radians(x)) # Sine of degree angle function
cos = math.cos # Cosine of radian angle function
cosdg = lambda x: cos(radians(x)) # Cosine of degree angle function
tan = math.tan # Tangent of radian angle function
tandg = lambda x: tan(radians(x)) # Tangent of degree angle function
asin = math.asin # Return arc cosine in radians function
asindg = lambda x: degrees(asin(x)) # Return arcsin in degrees function
acos = math.acos # Return arc sine in radians function
acosdg = lambda x: degrees(acos(x)) # Return arccos in degrees function
atan = math.atan # Return arc tangent in radians function
atan2 = math.atan2 # Returns arc tangent of y, x using correct sign
atandg = lambda x: degrees(atan(x)) # Return arctan in degrees function
atan2dg = lambda y, x: degrees(atan2(y, x)) # atan2 in degrees

def norm(vect):
    """
    Normalize the supplied vector and return the normalized vector
    """
    return np.asarray(vect) / np.linalg.norm(vect)

def normvect(v1, v2):
    """
    Return the unit normal vector between the two supplied vectors
    """
    return norm(np.cross(v1, v2))

def magnitude(vect):
    """
    Return the scalar magnitude of the supplied vector
    """
    return np.linalg.norm(vect)

def negate_vect(v):
    """
    Negate the supplied vector
    """
    return -np.asarray(v)

def vectangle(v1, v2):
    '''
    Calculate the angle in degrees between the two supplied vectors v1 and v2
    '''
    return acosdg(np.dot(v1, v2) / (magnitude(v1) * magnitude(v2)))

def yz_tilt(v, polar=np.array([0.,0.,1.])):
    # Tilt angle from polar axis in YZ plane (X-component = 0)
    # Default polar vector: Z-axis [0, 0, 1]
    return vectangle((0, v[1], v[2]), polar)

def xz_tilt(v, polar=np.array([0.,0.,1.])):
    # Tilt angle from polar axis in XZ plane (Y-component = 0)
    # Default polar vector: Z-axis [0, 0, 1]
    return vectangle((v[0], 0, v[2]), polar)

def xy_tilt(v, polar=np.array([0.,1.,1.])):
    # Tilt angle from polar axis in XY plane (Z-component = 0)
    # Default polar vector: Y-axis [0, 1, 0]
    return vectangle((v[0], v[1], 0), polar)

def move_x(FDOC, nid, dist):
    '''
    Move the supplied nodeid in x by the supplied dist
    '''
    op = FDOC.struct('T_OPERATION')
    op.type = 'ShiftX'
    op.val1 = dist
    FDOC.dobj.AddOperation(nid, op)
    FDOC.dobj.Update()

def move_y(FDOC, nid, dist):
    '''
    Move the supplied nodeid in y by the supplied dist
    '''
    op = FDOC.struct('T_OPERATION')
    op.type = 'ShiftY'
    op.val1 = dist
    FDOC.dobj.AddOperation(nid, op)
    FDOC.dobj.Update()

def move_z(FDOC, nid, dist):
    '''
    Move the supplied nodeid in z by the supplied dist
    '''
    op = FDOC.struct('T_OPERATION')
    op.type = 'ShiftZ'
    op.val1 = dist
    FDOC.dobj.AddOperation(nid, op)
    FDOC.dobj.Update()
