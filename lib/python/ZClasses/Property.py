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
"""Provide management of common instance property sheets
"""

import OFS.PropertySheets, Globals, OFS.SimpleItem, OFS.PropertyManager
import Acquisition
from string import join, upper

class ClassCaretaker:
    def __init__(self, klass): self.__dict__['_k']=klass
    def __getattr__(self, name): return getattr(self._k, name)
    def __setattr__(self, name, v):
        klass=self._k
        setattr(klass, name, v)
        if not klass._p_changed:
            get_transaction().register(klass)
            klass._p_changed=1        
    def __delattr__(self, name):
        klass=self._k
        delattr(klass, name)
        if not klass._p_changed:
            get_transaction().register(klass)
            klass._p_changed=1 
       
class ZCommonSheet(OFS.PropertySheets.PropertySheet, OFS.SimpleItem.Item):
    "Property Sheet that has properties common to all instances"
    meta_type="Common Instance Property Sheet"
    _properties=()

    manage_options=(
        {'label':'Properties', 'action':'manage'},
        )
    
    def __init__(self, id, title):
        self.id=id
        self.title=title
        self._md={}

    def v_self(self):
        klass=self.aq_inner.aq_parent.aq_parent.aq_parent._zclass_
        return ClassCaretaker(klass)

    def p_self(self): return self

    def _view_widget_for_type(self, t, id):
        if t not in ('lines', 'tokens'):
            return '<!--#var %s-->' % id
        return """
        <!--#in %s-->
           <!--#var sequence-item-->
        <!--#in %s-->
        """ % (id, id)

    def manage_createView(self, id, title='', ps_view_type=None, REQUEST=None):
        """Create a view of a property sheet
        """
        if ps_view_type == 'Edit':
            return self.manage_createEditor(id, title, REQUEST)
            
        r=['<!--#var standard_html_header-->',
           '<table>']
        a=r.append
        for p in self.propertyMap():
            pid=p['id']
            pid=upper(pid[:1])+pid[1:]
            a('  <tr><th align=left valign=top>%s</th>' % pid)
            a('      <td align=left valign=top>%s</td>' %
              self._view_widget_for_type(p['type'], p['id'])
              )
            a('  </tr>')
        a('</table>')
        a('<!--#var standard_html_footer-->')
        r=join(r,'\n')
        self.aq_parent.aq_parent.methods.manage_addDTMLMethod(id, title, r)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL3']+'/methods/manage')

    def _edit_widget_for_type(self, t, id, p):
        if t in ('int', 'long', 'float', 'date', 'string'):
            if t=='string': q=' html_quote'
            else: q=''
            return ('''
            <input name="%s:%s" size="35"
                   value="<!--#var %s%s-->">'''
                    % (id, t, id, q)
                    )
        if t=='boolean':
            return ('''
            <input type="checkbox" name="%s:boolean" size="35"
                <!--#if %s-->CHECKED<!--#/if-->>'''
                    % (id, id)
                    )
                    
        if t=='tokens':
            return ('''
            <input type="text" name="%s:tokens" size="35"
               value="<!--#in %s--><!--#var sequence-item--> <!--#endin-->">'''
                    % (id, id)
                    )
                    
        if t=='text':
            return ('''
            <textarea name="%s:text" rows="6" cols="35"><!--#var %s
            --></textarea>'''
                    % (id, id)
                    )
                    
        if t=='lines':
            return ('''
            <textarea name="%s:lines" rows="6" cols="35"><!--#in %s
            --><!--#var sequence-item-->\n<!--#/in--></textarea>'''
                    % (id, id) 
                    )

                    
        if t=='selection':
            return ('''
            <!--#if "_.has_key('%(id)s')"-->
            <select name="%(id)s">
              <!--#in "_.string.split('%(select_variable)s')"-->
                <option
                  <!--#if "_['sequence-item']=='%(id)s'"-->
                  SELECTED<!--#/if-->
                  ><!--#var sequence-item--></option>
              <!--#/in-->
            </select>
            <!--#else-->
              No value for %(id)s
            <!--#/if-->'''            
                    % p
                    )

        return ''

    def _on_delete_object(self):
        for d in self._properties:
            self.delClassAttr(d['id'])

    def manage_createEditor(self, id, title='', REQUEST=None):
        """Create an edit interface for a property sheet
        """
        r=['<html><head><title><!--#var title_or_id--></title></head>',
           '<body bgcolor="#FFFFFF" link="#000099" vlink="#555555">',
           '<!--#var manage_tabs-->',
           '<form action="propertysheets/%s/manage_editProperties"><table>'
           % self.id]
        a=r.append
        for p in self.propertyMap():
            a('  <tr><th align=left valign=top>%s</th>' % p['id'])
            a('      <td align=left valign=top>%s</td>' %
              self._edit_widget_for_type(p['type'], p['id'], p)
              )
            a('  </tr>')
        a('  <tr><td colspan=2>')
        a('    <input type=submit value=" Change ">')
        a('    <input type=reset value=" Reset ">')
        a('  </td></tr>')
        a('</table></form>')
        a('</body></html>')
        r=join(r,'\n')
        self.aq_parent.aq_parent.methods.manage_addDTMLMethod(id, title, r)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL3']+'/methods/manage')

class ZInstanceSheet(OFS.PropertySheets.FixedSchema,
                     OFS.PropertySheets.View,
                    ):
    "Waaa this is too hard"

    def v_self(self):
        return self.aq_inner.aq_parent.aq_parent
    
def rclass(klass):
    if klass._p_changed==0:
        get_transaction().register(klass)
        klass._p_changed=1

class ZInstanceSheetsSheet(OFS.PropertySheets.View,
                           OFS.ObjectManager.ObjectManager):
    "Manage common property sheets"

    # Note that we need to make sure we add and remove
    # instance sheets.
    id='common'
    isPrincipiaFolderish=1
    icon="p_/Propertysheets_icon"

    def tpURL(self): return 'propertysheets/common'

    def _setOb(self, id, value):
        setattr(self, id, value)
        pc=self.aq_inner.aq_parent.aq_parent._zclass_propertysheets_class
        setattr(pc,id,ZInstanceSheet(id,value))
        pc.__propset_attrs__=tuple(map(lambda o: o['id'], self._objects))
        rclass(pc)
        

    def _delOb(self, id):
        delattr(self, id)
        pc=self.aq_inner.aq_parent.aq_parent._zclass_propertysheets_class
        delattr(pc,id)
        pc.__propset_attrs__=tuple(map(lambda o: o['id'], self._objects))
        rclass(pc)

    meta_types=(
        Globals.Dictionary(name=ZCommonSheet.meta_type,
                           action='manage_addCommonSheetForm'),
        )

    def all_meta_types(self): return self.meta_types

    manage=Globals.HTMLFile('OFS/main')
    manage_addCommonSheetForm=Globals.HTMLFile('addCommonSheet', globals())

    def manage_addCommonSheet(self, id, title, REQUEST=None):
        "Add a property sheet"
        o=ZCommonSheet(id, title)
        self._setObject(id, o)
        if REQUEST is not None: return self.manage_main(self, REQUEST)

def klass_sequence(klass,attr,result=None):
    if result is None: result={}
    if hasattr(klass,attr):
        for i in getattr(klass,attr): result[i]=1
        for klass in klass.__bases__:
            klass_sequence(klass, attr, result)
    return result

class ZInstanceSheets(OFS.PropertySheets.PropertySheets, Globals.Persistent):
    " "
    __propset_attrs__=()    

    def __propsets__(self):
        propsets=ZInstanceSheets.inheritedAttribute('__propsets__')(self)
        r=[]
        for id in klass_sequence(self.__class__,'__propset_attrs__').keys():
            r.append(getattr(self, id))
        return propsets+tuple(r)

  
