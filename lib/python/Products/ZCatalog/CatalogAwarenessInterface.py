from Zope.Interfaces.Interface import Interface

class CatalogAware:
    """
    Description of the Item interface
    """

    def creator(self):
        """

        Return a sequence of user names who have the local Owner role
        on an object. The name creator is used for this method to
        conform to Dublin Core.

        """

    def summary(self, num=200):
        """

        Returns the summary of the text contents of the object (if
        text content is present).  Summary length is 'num'.

        """

    def index_object(self):
        """

        This object will try and catalog itself when this method is
        called.

        """

    def unindex_object(self):
        """

        This object will try and uncatalog itself when this method is
        called.

        """

    def reindex_all(self, obj=None):
        """

        This method will cause this object to get reindexed.  Of this
        object is a container, then all child objects will try to be
        recursivly reindexed.  'obj' can be passed as an alternative
        object to try and reindex.

        """
            

CatalogAwareInterface=Interface(CatalogAware) # create the interface object







