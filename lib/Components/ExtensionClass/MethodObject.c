
#include "ExtensionClass.h"

static PyObject *
of(PyObject *self, PyObject *args)
{
  PyObject *inst;

  if(PyArg_Parse(args,"O",&inst)) return PyECMethod_New(self,inst);
  else return NULL;
}

struct PyMethodDef Method_methods[] = {
  {"__of__",(PyCFunction)of,0,""},  
  {NULL,		NULL}		/* sentinel */
};

static struct PyMethodDef methods[] = {{NULL,	NULL}};

void
initMethodObject()
{
  PyObject *m, *d;
  PURE_MIXIN_CLASS(Method,
	"Base class for objects that want to be treated as methods\n"
	"\n"
	"The method class provides a method, __of__, that\n"
	"binds an object to an instance.  If a method is a subobject\n"
	"of an extension-class instance, the the method will be bound\n"
	"to the instance and when the resulting object is called, it\n"
	"will call the method and pass the instance in addition to\n"
	"other arguments.  It is the responsibility of Method objects\n"
	"to implement (or inherit) a __call__ method.\n",
	Method_methods)

    /* Create the module and add the functions */
    m = Py_InitModule4("MethodObject", methods,
		       "Method-object mix-in class module",
		       (PyObject*)NULL,PYTHON_API_VERSION);

  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"Method",MethodType);

  /* Check for errors */
  CHECK_FOR_ERRORS("can't initialize module MethodObject");
}

