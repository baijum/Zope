##############################################################################
#
# Copyright (c) 1996-1998, Digital Creations, Fredericksburg, VA, USA.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   o Redistributions of source code must retain the above copyright
#     notice, this list of conditions, and the disclaimer that follows.
# 
#   o Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions, and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#   o All advertising materials mentioning features or use of this
#     software must display the following acknowledgement:
# 
#       This product includes software developed by Digital Creations
#       and its contributors.
# 
#   o Neither the name of Digital Creations nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS IS*
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
# CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
# 
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
#
##############################################################################

'''Raising exceptions

   Errors can be raised from DTML using the 'raise' tag.

   For example::

    <!--#if expr="condition_that_tests_input"-->
       <!--#raise type="Input Error"-->
           The value you entered is not valid
       <!--#/raise-->
    <!--#/if-->

''' 
__rcs_id__='$Id: DT_Raise.py,v 1.9 1998/09/14 22:03:32 jim Exp $'
__version__='$Revision: 1.9 $'[11:-2]

from DT_Util import parse_params, name_param, render_blocks, str

class Raise:
    blockContinuations=()
    name='raise'
    expr=''

    def __init__(self, blocks):

        tname, args, section = blocks[0]
        self.section=section.blocks
        args=parse_params(args, type='', expr='')
        self.__name__, self.expr = name_param(args, 'raise', 1, attr='type')

    def render(self,md):
        expr=self.expr
        if expr is None:
                t=self.__name__
                if t[-5:]=='Error' and __builtins__.has_key(t):
                    t=__builtins__[t]
        else:
            try: t=expr.eval(md)
            except: t='Invalid Error Type Expression'

        try: v=render_blocks(self.section,md)
        except: v='Invalid Error Value'

        raise t, v

    __call__=render
