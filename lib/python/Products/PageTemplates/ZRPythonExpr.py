##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""Zope-specific Python Expression Handler

Handler for Python expressions that uses the RestrictedPython package.
"""

__version__='$Revision: 1.5 $'[11:-2]

from AccessControl import full_read_guard, full_write_guard, \
     safe_builtins, getSecurityManager
from AccessControl.ZopeGuards import guarded_getattr, guarded_getitem
from RestrictedPython import compile_restricted_eval
from TALES import CompilerError
from string import strip, split, join, replace, lstrip

from PythonExpr import PythonExpr

class PythonExpr(PythonExpr):
    _globals = {'__debug__': __debug__,
                '__builtins__': safe_builtins,
                '_getattr_': guarded_getattr,
                '_getitem_': guarded_getitem,}
    def __init__(self, name, expr, engine):
        self.expr = expr = replace(strip(expr), '\n', ' ')
        code, err, warn, use = compile_restricted_eval(expr, str(self))
        if err:
            raise CompilerError, ('Python expression error:\n%s' %
                                  join(err, '\n') )
        self._f_varnames = use.keys()
        self._code = code
        
    def __call__(self, econtext):
        __traceback_info__ = self.expr
        code = self._code
        g = self._bind_used_names(econtext)
        g.update(self._globals)        
        return eval(code, g, {})

class _SecureModuleImporter:
    __allow_access_to_unprotected_subobjects__ = 1
    def __getitem__(self, module):
        mod = safe_builtins['__import__'](module)
        path = split(module, '.')
        for name in path[1:]:
            mod = getattr(mod, name)
        return mod

from DocumentTemplate.DT_Util import TemplateDict, InstanceDict
def call_with_ns(f, ns, arg=1):
    td = TemplateDict()
    td.this = None
    td._push(ns['request'])
    td._push(InstanceDict(ns['here'], td, guarded_getattr))
    td._push(ns)
    try:
        if arg==2:
            return f(None, td)
        else:
            return f(td)
    finally:
        td._pop(3)
