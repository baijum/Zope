#!/usr/local/bin/python 
# $What$

__doc__='''Bobo test script

Usage:

   bobo [options] module_path [path_info]

Options:

   -u username=password


$Id: Test.py,v 1.1 1996/09/13 22:51:52 jim Exp $'''
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
# $Log: Test.py,v $
# Revision 1.1  1996/09/13 22:51:52  jim
# *** empty log message ***
#
#
# 
__version__='$Revision: 1.1 $'[11:-2]


#! /usr/local/bin/python

import sys,traceback
from cgi_module_publisher import publish_module
    
o=open('/dev/null','w')


def main():
    import sys, os, getopt, string

    try:
	optlist,args=getopt.getopt(sys.argv[1:], 'du:p:')
	if len(args) > 2: raise TypeError, None
	if len(args) == 2: path_info=args[1]
    except:
	sys.stderr.write(__doc__)
	sys.exit(-1)

    profile=u=debug=None
    for opt,val in optlist:
	if opt=='-d':
	    debug=1
	if opt=='-u':
	    u=val
	elif opt=='-p':
	    profile=val

    
    publish(args[0],path_info,u=u,p=profile,d=debug)

def publish(script,path_info,u=None,p=None,d=None):

    import sys, os, getopt, string

    profile=p
    debug=d

    env={'SERVER_NAME':'bobo.server',
	 'SERVER_PORT':'80',
	 'REQUEST_METHOD':'GET',
	 'REMOTE_ADDR': '204.183.226.81 ',
	 'REMOTE_HOST': 'bobo.remote.host',
	 'HTTP_USER_AGENT': 'Bobo/%s' % __version__,
	 'HTTP_HOST': 'ninny.digicool.com:8081 ',
	 'SERVER_SOFTWARE': 'Bobo/%s' % __version__,
	 'SERVER_PROTOCOL': 'HTTP/1.0 ',
	 'HTTP_ACCEPT': 'image/gif, image/x-xbitmap, image/jpeg, */* ',
	 'SERVER_HOSTNAME': 'bobo.server.host',
	 'GATEWAY_INTERFACE': 'CGI/1.1 ',
	 }
    env['SCRIPT_NAME']=script
    p=string.split(path_info,'?')
    if   len(p)==1: env['PATH_INFO'] = p[0]
    elif len(p)==2: [env['PATH_INFO'], env['QUERY_STRING']]=p
    else: raise TypeError, ''

    if u:
	import base64
	env['HTTP_AUTHORIZATION']="Basic %s" % base64.encodestring(u)

    dir,file=os.path.split(script)
    sys.path[0:0]=[dir]

    if profile:
	import __main__
	from profile import run
	__main__.publish_module=publish_module
	__main__.file=file
	__main__.env=env
	print profile
	if profile: run('publish_module(file, environ=env)',profile)
	else:       run('publish_module(file, environ=env)')
    elif debug:
	import cgi_module_publisher
	from cgi_module_publisher import ModulePublisher
	import pdb

	class Pdb(pdb.Pdb):
	    def do_pub(self,arg):
		if hasattr(self,'done_pub'):
		    print 'pub already done.'
		else:
		    self.do_s('')
		    self.do_s('')
		    self.do_c('')
		    self.done_pub=1
	    def do_ob(self,arg):
		if hasattr(self,'done_ob'):
		    print 'ob already done.'
		else:
		    self.do_pub('')
		    self.do_c('')
		    self.done_ob=1

	import codehack
       	db=Pdb()

	code=ModulePublisher.publish.im_func.func_code
	lineno = codehack.getlineno(code)
	filename = code.co_filename
	db.set_break(filename,lineno)

	code=ModulePublisher.call_object.im_func.func_code
	lineno = codehack.getlineno(code)
	filename = code.co_filename
	db.set_break(filename,lineno)
	db.prompt='pdb> '
	# db.set_continue()

	print '''Type "s<cr>c<cr>" to jump to beginning of real
		 publishing process. Then type c<ret> to jub to
		 published object call.'''
	db.run('publish_module(file,environ=env,debug=1)',
	       cgi_module_publisher.__dict__,
	       {'file':file, 'env':env})
    else:
	publish_module(file, environ=env)

if __name__ == "__main__": main()
