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

import common.PluggableIndex as PluggableIndex
import common.ResultList     as ResultList
import common.UnIndex        as UnIndex

import PathIndex.PathIndex
import TextIndex.TextIndex
import FieldIndex.FieldIndex
import KeywordIndex.KeywordIndex
import TopicIndex.TopicIndex
import DateIndex.DateIndex
import DateRangeIndex.DateRangeIndex

_indexes =  ('TextIndex',
             'KeywordIndex',
             'FieldIndex',
             'PathIndex',
             'TopicIndex',
             'DateIndex',
             'DateRangeIndex',
            )

def initialize(context):

    for idx in _indexes:

        s = "context.registerClass( \
            %s.%s.%s,\
            permission='Add Pluggable Index', \
            constructors=(manage_add%sForm,\
                          manage_add%s),\
            icon='www/index.gif',\
            visibility=None\
         )" % (idx,idx,idx,idx,idx)

        exec(s)


for idx in _indexes:

    exec("manage_add%sForm = %s.%s.manage_add%sForm" % (idx,idx,idx,idx))
    exec("manage_add%s     = %s.%s.manage_add%s" % (idx,idx,idx,idx))
