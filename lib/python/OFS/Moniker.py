##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""Object monikers

   An object moniker is an intelligent reference to a
   persistent object. A moniker can be turned back into
   a real object that retains its correct version context
   and aquisition relationships via a simple interface.

"""
__version__='$Revision: 1.15 $'[11:-2]


import Globals

class Moniker:
    """An object moniker is an intelligent reference to a
    persistent object. A moniker can be turned back into
    a real object that retains its correct version context
    and acquisition relationships via a simple interface."""
    
    def __init__(self, ob=None):
        if ob is None: return
        self.idpath = ob.getPhysicalPath()

    def bind(self, app):
        "Returns the real object named by this moniker"
        ob = app.unrestrictedTraverse(self.idpath)
        return ob

    def dump(self):
        '''Returns an object which can be reconstituted by
        loadMoniker().  Result must be compatible with marshal.dump().
        '''
        return self.idpath


def loadMoniker(data):
    '''Re-creates a Moniker object from the given data which had been
    generated by Moniker.dump().'''
    m = Moniker()
    m.idpath = data
    return m

def absattr(attr):
    if callable(attr): return attr()
    return attr
