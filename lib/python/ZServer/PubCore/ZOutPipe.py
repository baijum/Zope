##############################################################################
# 
# Zope Public License (ZPL) Version 0.9.6
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
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
# 3. Any use, including use of the Zope software to operate a website,
#    must either comply with the terms described below under
#    "Attribution" or alternatively secure a separate license from
#    Digital Creations.  Digital Creations will not unreasonably
#    deny such a separate license in the event that the request
#    explains in detail a valid reason for withholding attribution.
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
# Attribution
# 
#   Individuals or organizations using this software as a web
#   site ("the web site") must provide attribution by placing
#   the accompanying "button" on the website's main entry
#   point.  By default, the button links to a "credits page"
#   on the Digital Creations' web site. The "credits page" may
#   be copied to "the web site" in order to add other credits,
#   or keep users "on site". In that case, the "button" link
#   may be updated to point to the "on site" "credits page".
#   In cases where this placement of attribution is not
#   feasible, a separate arrangment must be concluded with
#   Digital Creations.  Those using the software for purposes
#   other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.  Where
#   attribution is not possible, or is considered to be
#   onerous for some other reason, a request should be made to
#   Digital Creations to waive this requirement in writing.
#   As stated above, for valid requests, Digital Creations
#   will not unreasonably deny such requests.
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""ZServer output pipe
"""

import thread
from ZEvent import Wakeup
from string import join
TupleType=type(())

class OutputPipe:
    """A pipe which can be written to and read from different threads.
    Also supports callbacks to notify readers when the pipe has been
    written to or has been closed."""

    def __init__(self,callback=None):
        "callback should be a tuple (function,(args,))"
        lock=thread.allocate_lock()
        self._r=lock.release
        self._a=lock.acquire
        self._buf=[]
        self._callback=callback

    def write(self, text):
        self._a()
        try:
            self._buf.append(text)
        finally: self._r()
        self.notify()

    def notify(self):
        if self._callback:
            fun=self._callback[0]
            args=self._callback[1]+(self,)
            Wakeup(lambda f=fun,a=args: apply(f,a))
        else:
            Wakeup()

    def close(self):
        self._a()
        try:
            b=self._buf
            if b: self._buf=tuple(b)
            else: self._buf=None
        finally: self._r()
        self.notify()

    def read(self):
        """Read data from the pipe

        Return None if the pipe is open but has no data.
        Return an empty string if the pipe is closed.
        """
        self._a()
        try:
            b=self._buf
            if b is None: return ''
            if not b: return None
            if type(b) is TupleType: self._buf=None
            else:                    self._buf=[]
            return join(b,'')
        finally: self._r()
        
    def ready(self):
        """Pipe status, medusa producer style.
        
        Return 1 if the pipe is open and has data.
        Return None if the pipe is open but has no data.
        Return 1 if the pipe is closed.
        """
        self._a()
        try:
            b=self._buf
            if b is None: return 1
            if not b: return None
            return 1
        finally: self._r()
