##############################################################################
#
# Copyright (c) 1998, Digital Creations, Fredericksburg, VA, USA.
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

__doc__='''Machinery to support through-the-web editing

$Id: DT_UI.py,v 1.5 1998/09/02 14:35:54 jim Exp $''' 
__version__='$Revision: 1.5 $'[11:-2]

from DT_HTML import HTML

FactoryDefaultString="Factory Default"

HTML.document_template_edit_header='<h2>Edit Document</h2>'
HTML.document_template_form_header=''
HTML.document_template_edit_footer=(
    """<FONT SIZE="-1">
    <I><A HREF="http://www.digicool.com/products/copyright.html">
    &copy; 1997 Digital Creations, L.L.C.</A></I></FONT>""")

HTML.document_template_edit_width=58

HTML._manage_editForm = HTML(
    """<HTML>
    <HEAD>
    <TITLE>HTML Template Editor</TITLE>
    </HEAD>
    <BODY bgcolor="#FFFFFF">
    <!--#var document_template_edit_header-->
    
    <FORM name="editform" ACTION="<!--#var PARENT_URL-->/manage_edit" METHOD="POST">
    <!--#var document_template_form_header-->
    Document template source:
    <center>
    <br>
    <TEXTAREA NAME="data:text" cols="<!--#var document_template_edit_width-->" 
                    rows="20"><!--#var __str__--></TEXTAREA>

    <br>
      <INPUT NAME=SUBMIT TYPE="SUBMIT" VALUE="Change">
      <INPUT NAME=SUBMIT TYPE="RESET"  VALUE="Reset">
      <INPUT NAME="dt_edit_name" TYPE="HIDDEN"
             VALUE="<!--#var URL1-->">
      <!--#if FactoryDefaultString-->
        <INPUT NAME=SUBMIT TYPE="SUBMIT" 
         VALUE="<!--#var FactoryDefaultString-->">
      <!--#/if FactoryDefaultString-->
      <INPUT NAME=SUBMIT TYPE="SUBMIT" VALUE="Cancel">
      <!--#if HTTP_REFERER-->
    	 <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN" 
    		VALUE="<!--#var HTTP_REFERER-->">
      <!--#else HTTP_REFERER-->
         <!--#if PARENT_URL-->
    	   <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"
    		  VALUE="<!--#var PARENT_URL-->">
         <!--#/if PARENT_URL-->
      <!--#/if HTTP_REFERER-->
    </center>
    </FORM>
    
    <BR CLEAR="ALL">
    <!--#var document_template_edit_footer-->
    
    </BODY>
    </HTML>""",)

HTML.editConfirmation=HTML(
    """<html><head><title>Change Successful</title></head><body>
    <!--#if CANCEL_ACTION-->
      <form action="<!--#var CANCEL_ACTION-->" method="POST">
    	<center>
    	   <em><!--#var dt_edit_name--></em><br>has been changed.<br><br>
    	   <input type=submit name="SUBMIT" value="OK">
    	</center>
      </form></body></html>
    <!--#else CANCEL_ACTION-->
      <center>
    	 <em><!--#var dt_edit_name--></em><br>has been changed.
      </center>
    <!--#/if CANCEL_ACTION-->""")

############################################################################
# $Log: DT_UI.py,v $
# Revision 1.5  1998/09/02 14:35:54  jim
# open source copyright
#
# Revision 1.4  1997/11/05 15:11:26  paul
# Changed header to be more Principia-compliant in a way that does not break Bobo.
#
# Revision 1.3  1997/10/27 17:37:13  jim
# Removed old validation machinery.
#
# Revision 1.2  1997/09/02 19:04:52  jim
# Got rid of ^Ms
#
# Revision 1.1  1997/08/27 18:55:43  jim
# initial
#
