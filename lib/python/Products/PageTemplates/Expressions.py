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

"""Page Template Expression Engine

Page Template-specific implementation of TALES, with handlers
for Python expressions, string literals, and paths.
"""

__version__='$Revision: 1.16 $'[11:-2]

import re, sys
from TALES import Engine, CompilerError, _valid_name, NAME_RE, \
     TALESError, Undefined, Default
from string import strip, split, join, replace, lstrip
from Acquisition import aq_base, aq_inner, aq_parent

_engine = None
def getEngine():
    global _engine
    if _engine is None:
        _engine = Engine()
        installHandlers(_engine)
    return _engine

def installHandlers(engine):
    reg = engine.registerType
    pe = PathExpr
    for pt in ('standard', 'path', 'exists'):
        reg(pt, pe)
    reg('string', StringExpr)
    reg('python', PythonExpr)
    reg('not', NotExpr)

if sys.modules.has_key('Zope'):
    import AccessControl
    from AccessControl import getSecurityManager
    if hasattr(AccessControl, 'full_read_guard'):
        from ZRPythonExpr import PythonExpr, _SecureModuleImporter, \
             call_with_ns
    else:
        from ZPythonExpr import PythonExpr, _SecureModuleImporter, \
             call_with_ns
else:
    from PythonExpr import getSecurityManager, PythonExpr
    def call_with_ns(f, ns, arg=1):
        if arg==2:
            return f(None, ns)
        else:
            return f(ns)
    
def render(ob, ns):
    """
    Calls the object, possibly a document template, or just returns it if
    not callable.  (From DT_Util.py)
    """
    if hasattr(ob, '__render_with_namespace__'):
        ob = call_with_ns(ob.__render_with_namespace__, ns)
    else:
        base = aq_base(ob)
        if callable(base):
            try:
                if getattr(base, 'isDocTemp', 0):
                    ob = call_with_ns(ob, ns, 2)
                else:
                    ob = ob()
            except AttributeError, n:
                if str(n) != '__call__':
                    raise
    return ob

class PathExpr:
    def __init__(self, name, expr, engine):
        self._s = expr
        self._name = name
        self._paths = map(self._prepPath, split(expr, '|'))

    def _prepPath(self, path):
        path = split(strip(path), '/')
        base = path.pop(0)
        if not _valid_name(base):
            raise CompilerError, 'Invalid variable name "%s"' % base
        # Parse path
        dp = []
        for i in range(len(path)):
            e = path[i]
            if e[:1] == '?' and _valid_name(e[1:]):
                dp.append((i, e[1:]))
        dp.reverse()
        return base, path, dp

    def _eval(self, (base, path, dp), econtext, securityManager,
              list=list, isinstance=isinstance, StringType=type('')):
        path = list(path) # Copy!
        contexts = econtext.contexts
        var = contexts['var']
        # Expand dynamic path parts from right to left.
        for i, varname in dp:
            val = var[varname]
            if isinstance(val, StringType):
                path[i] = val
            else:
                # If the value isn't a string, assume it's a sequence
                # of path names.
                path[i:i+1] = list(val)
        try:
            __traceback_info__ = base
            if base == 'CONTEXTS':
                ob = contexts
            else:
                has, ob = var.has_get(base)
                if not has:
                    ob = contexts[base]
            if path:
                return restrictedTraverse(ob, path, securityManager)
            else:
                return ob
        except (AttributeError, KeyError, TypeError, IndexError,
                'Unauthorized'), e:
            return Undefined(self._s, sys.exc_info())

    def __call__(self, econtext):
        securityManager = getSecurityManager()
        for pathinfo in self._paths:
            ob = self._eval(pathinfo, econtext, securityManager)
            exists = not isinstance(ob, Undefined)
            
            if exists:
                # We're done
                break
        if self._name == 'exists':
            # All we wanted to know is whether one of the paths exist.
            return exists
        # Return the rendered object
        return render(ob, econtext.contexts)

    def __str__(self):
        return '%s expression "%s"' % (self._name, self._s)

    def __repr__(self):
        return '<PathExpr %s:%s>' % (self._name, self._s)

            
_interp = re.compile(r'\$(%(n)s)|\${(%(n)s(?:/%(n)s)*)}' % {'n': NAME_RE})

class StringExpr:
    def __init__(self, name, expr, engine):
        self._s = expr
        if '%' in expr:
            expr = replace(expr, '%', '%%')
        self._vars = vars = []
        if '$' in expr:
            parts = []
            for exp in split(expr, '$$'):
                if parts: parts.append('$')
                m = _interp.search(exp)
                while m is not None:
                    parts.append(exp[:m.start()])
                    parts.append('%s')
                    vars.append(PathExpr('path', m.group(1) or m.group(2),
                                         engine))
                    exp = exp[m.end():]
                    m = _interp.search(exp)
                if '$' in exp:
                    raise CompilerError, (
                        '$ must be doubled or followed by a variable name '
                        'in string expression "%s"' % expr)
                parts.append(exp)
            expr = join(parts, '')
        self._expr = expr
        
    def __call__(self, econtext):
        vvals = []
        for var in self._vars:
            vvals.append(var(econtext))
        return self._expr % tuple(vvals)

    def __str__(self):
        return 'string expression %s' % `self._s`

    def __repr__(self):
        return '<StringExpr %s>' % `self._s`

class NotExpr:
    def __init__(self, name, expr, compiler):
        self._s = expr = lstrip(expr)
        self._c = compiler.compile(expr)
        
    def __call__(self, econtext):
        return not econtext.evaluateBoolean(self._c)

    def __repr__(self):
        return '<NotExpr %s>' % `self._s`


def restrictedTraverse(self, path, securityManager,
                       get=getattr, has=hasattr, N=None, M=[]):

    i = 0
    if not path[0]:
        # If the path starts with an empty string, go to the root first.
        self = self.getPhysicalRoot()
        if not securityManager.validateValue(self):
            raise 'Unauthorized', name
        i = 1

    plen = len(path)
    REQUEST={'TraversalRequestNameStack': path}
    validate = securityManager.validate
    object = self
    while i < plen:
        __traceback_info__ = (path, i)
        name = path[i]
        i = i + 1

        if name[0] == '_':
            # Never allowed in a URL.
            raise AttributeError, name

        if name=='..':
            o = get(object, 'aq_parent', M)
            if o is not M:
                if not validate(object, object, name, o):
                    raise 'Unauthorized', name
                object=o
                continue

        t=get(object, '__bobo_traverse__', N)
        if t is not N:
            o=t(REQUEST, name)
                    
            container = None
            if (has(get(object, 'aq_base', object), name)
                and get(object, name) is o):
                container = object
            if not validate(object, container, name, o):
                raise 'Unauthorized', name
        else:
            o=get(object, name, M)
            if o is not M:
                # Check security.
                if has(object, 'aq_acquire'):
                    object.aq_acquire(
                        name, validate2, validate)
                else:
                    if not validate(object, object, name, o):
                        raise 'Unauthorized', name
            else:
                try:
                    o=object[name]
                except (AttributeError, TypeError):
                    raise AttributeError, name
                if not validate(object, object, name, o):
                    raise 'Unauthorized', name
        object = o

    return object


def validate2(orig, inst, name, v, real_validate):
    if not real_validate(orig, inst, name, v):
        raise 'Unauthorized', name
    return 1
