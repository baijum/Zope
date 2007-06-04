##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for Z3 -> Z2 bridge utilities.

$Id$
"""
import unittest
from zope.testing.doctest import DocFileSuite

def test_suite():
    return unittest.TestSuite([
        DocFileSuite('bridge.txt', package='Interface.tests'),
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
