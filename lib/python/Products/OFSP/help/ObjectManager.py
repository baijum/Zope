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

class ObjectManager:
    """
    An ObjectManager contains other Zope objects. The contained
    objects are Object Manager Items.

    To create an object inside an object manager use 'manage_addProduct'::

      self.manage_addProduct['OFSP'].manage_addFolder(id, title)

    In DTML this would be::

        <dtml-call "manage_addProduct['OFSP'].manage_addFolder(id, title)">

    These examples create a new Folder inside the current
    ObjectManager.

    'manage_addProduct' is a mapping that provides access to product
    constructor methods. It is indexed by product id.

    Constructor methods are registered during product initialization
    and should be documented in the API docs for each addable
    object.
    """

    def objectIds(type=None):
        """
        This method returns a list of the ids of the contained
        objects.
        
        Optionally, you can pass an argument specifying what object
        meta_type(es) to restrict the results to. This argument can be
        a string specifying one meta_type, or it can be a list of
        strings to specify many.

        Example::

          <dtml-in objectIds>
            <dtml-var sequence-item>
          <dtml-else>
            There are no sub-objects.
          </dtml-in>

        This DTML code will display all the ids of the objects
        contained in the current Object Manager.

        Permission -- 'Access contents information'
        """

    def objectValues(type=None):
        """
        This method returns a sequence of contained objects.
        
        Like objectItems and objectIds, it accepts one argument,
        either a string or a list to restrict the results to objects
        of a given meta_type or set of meta_types.

        Example::

          <dtml-in expr="objectValues('Folder')">
            <dtml-var icon>
            This is the icon for the: <dtml-var id> Folder<br>.
          <dtml-else>
            There are no Folders.
          </dtml-in>

        The results were restricted to Folders by passing a 
        meta_type to 'objectValues' method.
        
        Permission -- 'Access contents information'
        """

    def objectItems(type=None):
        """
        This method returns a sequence of (id, object) tuples.
        
        Like objectValues and objectIds, it accepts one argument,
        either a string or a list to restrict the results to objects
        of a given meta_type or set of meta_types.

        Each tuple's first element is the id of an object contained in
        the Object Manager, and the second element is the object
        itself.
        
        Example::

          <dtml-in objectItems>
           id: <dtml-var sequence-key>,
           type: <dtml-var meta_type>
          <dtml-else>
            There are no sub-objects.
          </dtml-in>
          
        Permission -- 'Access contents information'
        """

    def superValues(type):
        """
        This method returns a list of objects of a given meta_type(es)
        contained in the Object Manager and all its parent Object
        Managers.
        
        The type argument specifies the meta_type(es). It can be a string
        specifying one meta_type, or it can be a list of strings to
        specify many.
        
        Permission -- Python only
        """




