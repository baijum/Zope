/***********************************************************
     Copyright 

       Copyright 1997 Digital Creations, L.L.C., 910 Princess Anne
       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
       rights reserved.  Copyright in this software is owned by DCLC,
       unless otherwise indicated. Permission to use, copy and
       distribute this software is hereby granted, provided that the
       above copyright notice appear in all copies and that both that
       copyright notice and this permission notice appear. Note that
       any product, process or technology described in this software
       may be the subject of other Intellectual Property rights
       reserved by Digital Creations, L.C. and are not licensed
       hereunder.

     Trademarks 

       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
       All other trademarks are owned by their respective companies. 

     No Warranty 

       The software is provided "as is" without warranty of any kind,
       either express or implied, including, but not limited to, the
       implied warranties of merchantability, fitness for a particular
       purpose, or non-infringement. This software could include
       technical inaccuracies or typographical errors. Changes are
       periodically made to the software; these changes will be
       incorporated in new editions of the software. DCLC may make
       improvements and/or changes in this software at any time
       without notice.

     Limitation Of Liability 

       In no event will DCLC be liable for direct, indirect, special,
       incidental, economic, cover, or consequential damages arising
       out of the use of or inability to use this software even if
       advised of the possibility of such damages. Some states do not
       allow the exclusion or limitation of implied warranties or
       limitation of liability for incidental or consequential
       damages, so the above limitation or exclusion may not apply to
       you.

    If you have questions regarding this software,
    contact:
   
      Digital Creations L.L.C.  
      info@digicool.com
      (540) 371-6909

******************************************************************/


static char Trie_module_documentation[] = 
""
"\n$Id: Trie.c,v 1.6 1997/04/03 15:53:48 jim Exp $"
;


#define PERSISTENT
/* Note that I haven't put ifdefs everywhere they apply yet. */

#ifdef PERSISTENT
#  include "cPersistence.h"
#else
#  include "ExtensionClass.h"
#endif

static void PyVar_Assign(PyObject **v, PyObject *e) { Py_XDECREF(*v); *v=e;}
#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)
#define PyOb(O) ((PyObject*)(O))
#define LIST(O) ((PyListObject*)(O))
#define STRING(O) ((PyStringObject*)(O))
#define PyList_SIZE(O) (((PyListObject*)(O))->ob_size)

static PyObject *py___class__, *py_Trief;

/* Declarations for objects of type Trie */

typedef struct {
#ifdef PERSISTENT
  cPersistent_HEAD
#endif
  int min;
  PyObject *bins;
  PyObject *value;
} TrieObject;

staticforward PyExtensionClass TrieType;

/* ---------------------------------------------------------------- */

static PyObject *
Trie___setstate__(TrieObject *self, PyObject *args)
{
  PyObject *state;

  UNLESS(PyArg_ParseTuple(args, "O", &state)) return NULL;
  if(state != Py_None)
    {
      self->value=NULL;
      UNLESS(PyArg_ParseTuple(state, "iO|O", &(self->min), &(self->bins),
			      &(self->value)))
	return NULL;
      if(self->min < 0)
	{
	  self->value=self->bins;
	  self->bins=NULL;
	}
      Py_XINCREF(self->value);
      Py_XINCREF(self->bins);
    }
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
Trie___getstate__(TrieObject *self, PyObject *args)
{
  UNLESS(PyArg_ParseTuple(args, "")) return NULL;

#ifdef PERSISTENT
  if(cPersistenceCAPI->setstate(PyOb(self)) < 0) return NULL;
#endif

  if(self->value)
    if(self->bins)
      return Py_BuildValue("(iOO)", self->min, self->bins, self->value);
    else
      return Py_BuildValue("(iO)", -1, self->value);
  else
    if(self->bins)
      return Py_BuildValue("(iO)", self->min, self->bins);
  Py_INCREF(Py_None);
  return Py_None;
}

#ifdef PERSISTENT
static PyObject *
Trie__p___reinit__(TrieObject *self, PyObject *args)
{
  PyObject *oid, *jar, *copy;

  if(PyArg_ParseTuple(args, ""))
    {
      if(self->state==cPersistent_UPTODATE_STATE)
	{
	  Py_XDECREF(self->bins);
	  Py_XDECREF(self->value);
	  self->bins=NULL;
	  self->value=NULL;
	  self->min=0;
	  self->state=cPersistent_GHOST_STATE;
	}
    }
  else
    {
      UNLESS(PyArg_ParseTuple(args, "OOO", &oid, &jar, &copy)) return NULL;
      UNLESS(self->oid)
	{
	  Py_INCREF(oid);
	  ASSIGN(self->oid, oid);
	}
      if((self->oid==oid || PyObject_Compare(self->oid, oid)==0)
	 && self->state==cPersistent_UPTODATE_STATE)
	{
	  Py_XDECREF(self->bins);
	  Py_XDECREF(self->value);
	  self->bins=NULL;
	  self->value=NULL;
	  self->min=0;
	  self->state=cPersistent_GHOST_STATE;
	}
    }
  Py_INCREF(Py_None);
  return Py_None;
}
#endif

typedef struct {
  char *data;
  int size;
} keybuf;

static PyObject *
getiork(TrieObject *self, PyObject * r, keybuf *buf, int l, int dokeys)
{
  int i;
  PyObject *item=0;
  
#ifdef PERSISTENT
  if(cPersistenceCAPI->setstate(PyOb(self)) < 0) return NULL;
#endif

  if(self->value)
    {
      if(dokeys)
	{
	  UNLESS(item=PyString_FromStringAndSize(buf->data,l)) return NULL;
	}
      else
	UNLESS(item=Py_BuildValue("(s#O)",buf->data,l,self->value)) return NULL;
      i=PyList_Append(r,item);
      Py_DECREF(item);
      if(i < 0) return NULL;
    }
  if(l==buf->size)
    {
      buf->size *= 2;
      UNLESS(buf->data=realloc(buf->data, buf->size)) return PyErr_NoMemory();
    }
  if(self->bins)
    {
      PyObject *bin;
      int s, l1, ibin;

      for(ibin=0, l1=l+1, s=PyList_SIZE(self->bins); ibin < s; ibin++)
	{
	  bin=PyList_GET_ITEM(LIST(self->bins), ibin);
	  if(bin->ob_type==self->ob_type)
	    {
	      buf->data[l]=self->min+ibin;
	      UNLESS(getiork((TrieObject*)bin,r,buf,l1,dokeys)) return NULL;
	    }
	  else if(PyTuple_Check(bin))
	    {
	      buf->data[l]=self->min+ibin;
	      UNLESS(item=PyString_FromStringAndSize(buf->data,l1))
		return NULL;
	      ASSIGN(item,PySequence_Concat(item,PyTuple_GET_ITEM(bin,0)));
	      if(! dokeys && item)
		ASSIGN(item, Py_BuildValue("OO",item,PyTuple_GET_ITEM(bin,1)));
	      UNLESS(item) return NULL;
	      i=PyList_Append(r,item);
	      Py_DECREF(item);
	      if(i < 0) return NULL;
	    }
	}
    }
  return r;
}

static PyObject *
iork(TrieObject *self, int dokeys)
{
  PyObject *r=0;
  keybuf buf;

  buf.size=32;
  UNLESS(buf.data=(char*)malloc(buf.size)) return PyErr_NoMemory();
  UNLESS(r=PyList_New(0)) goto err;

  UNLESS(getiork(self, r, &buf, 0, dokeys)) goto err;
  free(buf.data);
  return r;
err:
  free(buf.data);
  Py_XDECREF(r);
  return NULL;
}

static PyObject *
Trie_keys(TrieObject *self, PyObject *args)
{
  UNLESS(PyArg_ParseTuple(args, "")) return NULL;
  return iork(self,1);
}

static PyObject *
Trie_cvalues(TrieObject *self, PyObject *r)
{
#ifdef PERSISTENT
  if(cPersistenceCAPI->setstate(PyOb(self)) < 0) return NULL;
#endif

  if(self->value)
    if(PyList_Append(r,self->value) < 0) return NULL;
  if(self->bins)
    {
      PyObject *bin;
      int i, s=0;

      for(i=0, s=PyList_SIZE(self->bins); i < s; i++)
	{
	  bin=PyList_GET_ITEM(LIST(self->bins), i);
	  if(bin->ob_type==self->ob_type)
	    {
	      UNLESS(Trie_cvalues((TrieObject*)bin,r)) return NULL;
	    }
	  else if(PyTuple_Check(bin))
	    if(PyList_Append(r,PyTuple_GET_ITEM(bin,1)) < 0) return NULL;
	}
    }
  return r;
}

static PyObject *
Trie_values(TrieObject *self, PyObject *args)
{
  PyObject *r;

  UNLESS(PyArg_ParseTuple(args, "")) return NULL;
  UNLESS(r=PyList_New(0)) return NULL;
  UNLESS(Trie_cvalues(self,r))
    {
      Py_DECREF(r);
      r=NULL;
    }
  return r;
}

static PyObject *
Trie_items(TrieObject *self, PyObject *args)
{
  UNLESS(PyArg_ParseTuple(args, "")) return NULL;
  return iork(self,0);
}

static struct PyMethodDef Trie_methods[] = {
  {"__getstate__", 	(PyCFunction)Trie___getstate__,  	METH_VARARGS,
   "__getstate__() -- Get the persistent state of the trie"},
  {"__setstate__", 	(PyCFunction)Trie___setstate__, 	METH_VARARGS,
   "__setstate__(v) -- Set the persistent state of the trie"},
#ifdef PERSISTENT
  {"_p___reinit__",	(PyCFunction)Trie__p___reinit__,	METH_VARARGS,
   "_p___reinit__(oid,jar,copy) -- Reinitialize from a newly created copy"},
#endif
  {"keys", 		(PyCFunction)Trie_keys,		METH_VARARGS,
   "keys() -- Get the keys of the trie"},
  {"values", 		(PyCFunction)Trie_values,		METH_VARARGS,
   "values() -- Get the values of the trie"},
  {"items", 		(PyCFunction)Trie_items,		METH_VARARGS,
   "items() -- Get the items of the trie"},
  {NULL,		NULL}		/* sentinel */
};

static PyObject *
NotFoundError()
{
  PyErr_SetObject(PyExc_KeyError, Py_None);
  return NULL;
}

static PyObject *
Trie_cget(TrieObject *self, char *word)
{
  int c;
  char *k;
  PyObject *bins;
  PyTypeObject *typ;
  PyObject *key;

#ifdef PERSISTENT
  if(cPersistenceCAPI->setstate(PyOb(self)) < 0) return NULL;
#endif

  typ=self->ob_type;
  while(c=*word++)
    {
      if(! (bins=self->bins) || c < self->min) return NotFoundError();
      c-=self->min;
      if(c >= PyList_SIZE(bins)) return NotFoundError();
      self=(TrieObject *)PyList_GET_ITEM(LIST(bins), c);
      if(self->ob_type != typ)
	if(PyTuple_Check(PyOb(self)) &&
	   PyString_Check((key=PyTuple_GET_ITEM(PyOb(self),0))) &&
	   strcmp(word,PyString_AS_STRING(STRING(key)))==0)
	  return PySequence_GetItem(PyOb(self),1);
	else
	  return NotFoundError();
	  
#ifdef PERSISTENT
      if(cPersistenceCAPI->setstate(PyOb(self)) < 0) return NULL;
#endif
    }
  if(! self->value) return NotFoundError();
  Py_INCREF(self->value);
  return self->value;
}

static int
Trie_cset(TrieObject *self, char *word, PyObject *v)
{
  PyObject *bin;
  int c, r, max;
#ifdef PERSISTENT
  int ch=0;

  if(cPersistenceCAPI->setstate(PyOb(self)) < 0) return -1;
#endif

  c=*word++;
  if(! c)
    {
      if(!v && !self->value)
	{
	  NotFoundError();
	  return -1;
	}
      Py_XINCREF(v);
      ASSIGN(self->value, v);
#ifdef PERSISTENT
      if(cPersistenceCAPI->changed(PyOb(self)) < 0) return -1;
#endif
      return 0;
    }
  if(!v &&
     (!self->bins || c < self->min || c-self->min >= PyList_SIZE(self->bins))
     )
    {
      NotFoundError();
      return -1;
    }
  if(! self->bins)
    {
      UNLESS(self->bins=PyList_New(1)) return -1;
      self->min=c;
#ifdef PERSISTENT
      ch=1;
#endif
    }
  else if(c < self->min)
    while(c < self->min)
      {
	if(PyList_Insert(self->bins,0,Py_None) < 0) return -1;
	self->min--;
#ifdef PERSISTENT
	ch=1;
#endif
      }
  else
    {
      max=PyList_SIZE(self->bins)-1+self->min;
      if(c > max)
	while(c > max)
	  {
	    if(PyList_Append(self->bins,Py_None) < 0) return -1;
	    max++;
#ifdef PERSISTENT
	    ch=1;
#endif
	  }
    }
  c-=self->min;
  bin=PyList_GET_ITEM(LIST(self->bins), c);
  if(!bin || bin->ob_type != self->ob_type)
    {
      PyObject *key;

      if(!v)
	if(bin && PyTuple_Check(bin) && (key=PyTuple_GET_ITEM(bin,0)) &&
	   PyString_Check(key) &&
	   strcmp(word,PyString_AS_STRING(STRING(key))) == 0
	   )
	  {
	    Py_INCREF(Py_None);
	    bin=Py_None;
	  }
	else
	  {
	    NotFoundError();
	    return -1;
	  }
      else
	{
	  if(bin && PyTuple_Check(bin) && (key=PyTuple_GET_ITEM(bin,0)) &&
	     PyString_Check(key) &&
	     strcmp(word,PyString_AS_STRING(STRING(key))) != 0
	     )
	    {
	      PyObject *o;
	      
	      o=PyTuple_GET_ITEM(bin,1);
	      UNLESS(bin=PyObject_GetAttr(PyOb(self),py___class__)) return -1;
	      UNLESS_ASSIGN(bin,PyObject_CallObject(bin,NULL)) return -1;
	      if(Trie_cset((TrieObject*)bin,
			   PyString_AS_STRING(STRING(key)),o) < 0 ||
		 Trie_cset((TrieObject*)bin,word,v) < 0
		 ) goto err;
	    }
	  else
	    UNLESS(bin=Py_BuildValue("sO",word,v)) goto err;
	}
  
#ifdef PERSISTENT
      if(cPersistenceCAPI->changed(PyOb(self)) < 0) goto err;
#endif

      return PyList_SetItem(self->bins, c, bin);
    }

#ifdef PERSISTENT
  if(ch && cPersistenceCAPI->changed(PyOb(self)) < 0) return -1;
#endif

  return Trie_cset((TrieObject*)bin,word,v);
err:
  Py_DECREF(bin);
  return -1;
}

static int 
Trie_length(TrieObject *self)
{
  int i, li, l=0;
  PyObject *bin;

#ifdef PERSISTENT
  if(cPersistenceCAPI->setstate(PyOb(self)) < 0) return NULL;
#endif

  if(self->bins)
    for(i=PyList_SIZE(self->bins); --i >= 0; )
      {
	bin=PyList_GET_ITEM(LIST(self->bins), i);
	if(bin->ob_type==self->ob_type)
	  {
	    li=Trie_length((TrieObject*)bin);
	    if(li < 0) return li;
	    if(li)
	      l+=li;
	    else
	      {      
#ifdef PERSISTENT
		if(cPersistenceCAPI->changed(PyOb(self)) < 0) return -1;
#endif
		/* Database management concerns make us leery of this
		Py_INCREF(Py_None);
		if(PyList_SetItem(self->bins, i, Py_None) < 1) return -1;
		*/
	      }
	  }
	else if(PyTuple_Check(bin)) l++;
      }
  if(self->value) l++;
  return l;
}

static PyObject *
Trie_subscript(TrieObject *self, PyObject *key)
{
  char *word;
  if(PyString_Check(key))
    {
      UNLESS(word=PyString_AsString(key)) return NULL;
      return Trie_cget(self,word);
    }
  PyErr_SetString(PyExc_TypeError, "Only string keys are allowed for tries.");
  return NULL;
}

static int
Trie_ass_sub(TrieObject *self, PyObject *key, PyObject *v)
{
  char *word;
  if(PyString_Check(key))
    {
      UNLESS(word=PyString_AsString(key)) return -1;
      return Trie_cset((TrieObject*)self,word,v);
    }
  PyErr_SetString(PyExc_TypeError, "Only string keys are allowed for tries.");
  return NULL;
}

static PyMappingMethods Trie_as_mapping = {
  (inquiry)Trie_length,		/*mp_length*/
  (binaryfunc)Trie_subscript,	/*mp_subscript*/
  (objobjargproc)Trie_ass_sub,	/*mp_ass_subscript*/
};

static void
Trie_dealloc(TrieObject *self)
{
  Py_XDECREF(self->bins);
  Py_XDECREF(self->value);
  PyMem_DEL(self);
}

static PyObject *
Trie_getattr(TrieObject *self, PyObject *name)
{
  return Py_FindAttr(PyOb(self), name);
}

static PyObject *
Trie_repr(TrieObject *self)
{
  PyObject *r;
  UNLESS(r=iork(self,0)) return NULL;
  ASSIGN(r,PyString_Format(py_Trief,r));
  return r;
}

static int
Trie_compare(TrieObject *v, TrieObject *w)
{
  if(v > w) return -1;
  return w > v;
}

static PyExtensionClass TrieType = {
  PyObject_HEAD_INIT(NULL)
  0,				/*ob_size*/
  "Trie",			/*tp_name*/
  sizeof(TrieObject),	/*tp_basicsize*/
  0,				/*tp_itemsize*/
  /* methods */
  (destructor)Trie_dealloc,	/*tp_dealloc*/
  (printfunc)0,			/*tp_print*/
  (getattrfunc)0,		/*obsolete tp_getattr*/
  (setattrfunc)0,		/*obsolete tp_setattr*/
  (cmpfunc)Trie_compare,	/*tp_compare*/
  (reprfunc)Trie_repr,	/*tp_repr*/
  0,				/*tp_as_number*/
  0,				/*tp_as_sequence*/
  &Trie_as_mapping,		/*tp_as_mapping*/
  (hashfunc)0,			/*tp_hash*/
  (ternaryfunc)0,		/*tp_call*/
  (reprfunc)0,			/*tp_str*/
  (getattrofunc)Trie_getattr,	/*tp_getattro*/
  0,				/*tp_setattro*/
  
  /* Space for future expansion */
  0L,0L,
  "",
  METHOD_CHAIN(Trie_methods),
};

/* End of code for Trie objects */
/* -------------------------------------------------------- */


/* List of methods defined in the module */

static PyObject *
spam(PyObject *self, PyObject *args)
{
  PyObject *d, *v;
  int i,s,j;

  d=PySequence_GetItem(args,0);
  s=PyTuple_Size(args);
  for(j=10000; --j >= 0; )
    for(i=s; --i > 0; )
      {
	v=PyObject_GetItem(d,PyTuple_GET_ITEM(args,i));
	Py_XDECREF(v);
      }
  return d;
}

static struct PyMethodDef Triem_methods[] = {
  {"spam", (PyCFunction)spam, 1, ""},
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initTrie) */

void
initTrie()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.6 $";

  UNLESS(ExtensionClassImported) return;

#ifdef PERSISTENT
  if(cPersistenceCAPI=PyCObject_Import("cPersistence","CAPI"))
    {
      static PyMethodChain m;
      m.methods=TrieType.methods.methods;
      TrieType.methods.methods=cPersistenceCAPI->methods->methods;
      TrieType.methods.link=&m;
      TrieType.tp_getattro=cPersistenceCAPI->getattro;
      TrieType.tp_setattro=cPersistenceCAPI->setattro;
    }
  else return;
#endif

  /* Create the module and add the functions */
  m = Py_InitModule4("Trie", Triem_methods,
		     Trie_module_documentation,
		     PyOb(NULL),PYTHON_API_VERSION);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);

  PyExtensionClass_Export(d, "Trie", TrieType);
  PyDict_SetItemString(d, "__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

  py___class__=PyString_FromString("__class__");
  py_Trief=PyString_FromString("Trie(%s)");
  /* Check for errors */
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module Trie");
}

/*****************************************************************************
 Revision Log:

  $Log: Trie.c,v $
  Revision 1.6  1997/04/03 15:53:48  jim
  Fixed bug in reinitialization code.

  Revision 1.5  1997/03/20 19:30:04  jim
  Major rewrite to use more efficient data structure.  In particular,
  try to avoid one-element tries by storing partial-key/value tuples
  instead of sub-tries.

  Revision 1.4  1997/03/17 23:23:09  jim
  Fixed reinit bug.

  Revision 1.3  1997/03/17 23:17:30  jim
  Added reinit method.  Need something better than this.
  Fixed dealloc bug.

  Revision 1.2  1997/03/17 21:29:39  jim
  Moved external imports before module initialization to give
  better error handling.

  Revision 1.1  1997/03/14 23:20:28  jim
  initial


*****************************************************************************/
