
"""External Method Product

This product provides support for external methods, which allow
domain-specific customization of web environments.
"""

from Acquisition import Implicit
from Globals import Persistent, HTMLFile, MessageDialog
import OFS.SimpleItem, os
from string import split, join
import AccessControl.Role
	    
braindir=SOFTWARE_HOME+'/Extensions'    
modules={}

addForm=HTMLFile('methodAdd', globals())

def add(self, id, title, module, function, REQUEST=None):
    """Add an external method to a folder"""
    i=ExternalMethod(id,title,module,function)
    self._setObject(id,i)
    return self.manage_main(self,REQUEST)

class ExternalMethod(OFS.SimpleItem.Item, Persistent,
		     AccessControl.Role.RoleManager):
    """An external method is a web-callable function that encapsulates
    an external function."""

    meta_type='External Method'
    icon='misc_/ExternalMethod/function_icon'
    func_defaults=()
    func_code=None
    
    manage_options=(
	{'label':'Properties', 'action':'manage_main'},
	{'label':'Try It', 'action':''},
	{'label':'Access Control', 'action':'manage_access'},
	)

    def __init__(self, id, title, module, function):
	self.id=id
	self.manage_edit(title, module, function)

    manage_main=HTMLFile('methodEdit', globals())
    def manage_edit(self, title, module, function, REQUEST=None):
	"Change the external method"
	self.title=title
	if module[-3:]=='.py': module=module[:-3]
	elif module[-4:]=='.py': module=module[:-4]
	self._module=module
	self._function=function
	try: del modules[module]
	except: pass
	self.getFunction()
	if REQUEST: return MessageDialog(
	    title  ='Changed %s' % self.id,
	    message='%s has been updated' % self.id,
	    action =REQUEST['URL1']+'/manage_main',
	    target ='manage_main')

    def getFunction(self):

	module=self._module
	
	try: m=modules[module]
	except:
	    d,n = os.path.split(module)
	    if d: raise ValueError, (
	    'The file name, %s, should be a simple file name' % module)
	    m={}
	    exec open("%s/%s.py" % (braindir, module)) in m
	    modules[module]=m

	f=m[self._function]
	if hasattr(f,'im_func'): ff=f.im_func
	else: ff=f
	    
	if self.func_defaults != ff.func_defaults:
	   self.func_defaults  = ff.func_defaults
	    
	func_code=FuncCode(ff,f is not ff)
	if func_code != self.func_code: self.func_code=func_code
    
	self._v_f=f

	return f

    def __call__(self, *args):
	try: f=self._v_f
	except: f=self.getFunction()

	return apply(f,args)

    def function(self): return self._function
    def module(self): return self._module
    
class FuncCode:

    def __init__(self, f, im=0):
	self.co_varnames=f.func_code.co_varnames[im:]
	self.co_argcount=f.func_code.co_argcount-im

    def __cmp__(self,other):
	return cmp((self.co_argcount, self.co_varnames),
		   (othr.co_argcount, othr.co_varnames))
