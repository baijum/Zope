#!/usr/bin/env python

# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.1.4.1 $
# Date: $Date: 2004/10/29 19:08:27 $
# Copyright: This module has been placed in the public domain.

"""
A minimal front end to the Docutils Publisher, producing pseudo-XML.
"""

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline, default_description


description = ('Generates pseudo-XML from standalone reStructuredText '
               'sources (for testing purposes).  ' + default_description)

publish_cmdline(description=description)
