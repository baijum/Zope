/*
     $Id: cPickle.c,v 1.14 1997/01/27 22:00:55 chris Exp $

     Copyright 

       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
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
   
      Jim Fulton, jim@digicool.com
      Digital Creations L.C.  
   
      (540) 371-6909
*/

static char cPickle_module_documentation[] = 
""
;

#include "Python.h"
#include "cStringIO.h"
#include "graminit.h"
#include "PyErr_Format.h"

#include <errno.h>

static PyObject *ErrorObject;




#define UNLESS(E) if (!(E))

#define DEL_LIST_SLICE(list, from, to) (PyList_SetSlice(list, from, to, NULL))

#define WRITE_BUF_SIZE 256

#define MARK        '('
#define STOP        '.'
#define POP         '0'
#define DUP         '2'
#define FLOAT       'F'
#define INT         'I'
#define BININT      'J'
#define BININT1     'K'
#define LONG        'L'
#define BININT2     'M'
#define NONE        'N'
#define BININT8     'O'
#define PERSID      'P'
#define BINPERSID   'Q'
#define REDUCE      'R'
#define STRING      'S'
#define BINSTRING   'T'
#define SHORT_BINSTRING 'U'
#define APPEND      'a'
#define BUILD       'b'
#define GLOBAL      'c'
#define DICT        'd'
#define APPENDS     'e'
#define GET         'g'
#define BINGET      'h'
#define INST        'i'
#define LONG_BINGET 'j'
#define LIST        'l'
#define OBJ         'o'
#define PUT         'p'
#define BINPUT      'q'
#define LONG_BINPUT 'r'
#define SETITEM     's'
#define TUPLE       't'
#define SETITEMS    'u'

static char MARKv = MARK;

/* atol function from string module */
static PyObject *atol_func;

static PyObject *PicklingError;
static PyObject *UnpicklingError;

static PyObject *dispatch_table;
static PyObject *safe_constructors;
static PyObject *class_map;
static PyObject *empty_tuple;

/* __builtins__ module */
static PyObject *builtins;

static int save();


typedef struct {
     PyObject_HEAD
     FILE *fp;
     PyObject *write;
     PyObject *file;
     PyObject *memo;
     PyObject *arg;
     PyObject *pers_func;
     PyObject *inst_pers_func;
     char *mark;
     int bin;
     int (*write_func)();
     char *write_buf;
     int buf_size;
} Picklerobject;

staticforward PyTypeObject Picklertype;


typedef struct {
    PyObject_HEAD
    FILE *fp;
    PyObject *file;
    PyObject *readline;
    PyObject *read;
    PyObject *memo;
    PyObject *arg;
    PyObject *stack;
    PyObject *mark;
    PyObject *pers_func;
    PyObject *last_string;
    int *marks;
    int num_marks;
    int marks_size;
    int (*read_func)();
    int (*readline_func)();
    int buf_size;
    char *buf;
    char diddled_char;
    char *diddled_ptr;
} Unpicklerobject;
 
staticforward PyTypeObject Unpicklertype;


static int 
write_file(Picklerobject *self, char *s, int  n) {
    if (s == NULL) {
        return 0;
    }

    if (fwrite(s, sizeof(char), n, self->fp) != n) {
        PyErr_SetFromErrno(PyExc_IOError);
        return -1;
    }

    return n;
}


static int 
write_cStringIO(Picklerobject *self, char *s, int  n) {
    if (s == NULL) {
        return 0;
    }

    if (PycStringIO->cwrite((PyObject *)self->file, s, n) != n) {
        return -1;
    }

    return n;
}


static int 
write_other(Picklerobject *self, char *s, int  n) {
    PyObject *py_str = 0, *junk = 0;
    int res = -1;

    if (s == NULL) {
        UNLESS(py_str = 
            PyString_FromStringAndSize(self->write_buf, self->buf_size))
            goto finally;
    }
    else {
        if ((n + self->buf_size) > WRITE_BUF_SIZE) {
            if (write_other(self, NULL, 0) < 0)
                goto finally;
        }

        if (n > WRITE_BUF_SIZE) {    
            UNLESS(py_str = 
                PyString_FromStringAndSize(self->write_buf, self->buf_size))
                goto finally;
        }
        else {
            memcpy(self->write_buf + self->buf_size, s, n);
            self->buf_size += n;
            res = n;
            goto finally;
        }
    }

    UNLESS(self->arg)
        UNLESS(self->arg = PyTuple_New(1))
            goto finally;

    Py_INCREF(py_str);
    if (PyTuple_SetItem(self->arg, 0, py_str) < 0)
        goto finally;

    UNLESS(junk = PyObject_CallObject(self->write, self->arg))
        goto finally;
    Py_DECREF(junk);

    self->buf_size = 0;
 
    res = n;

finally:
    Py_XDECREF(py_str);

    return res;
}


static int 
read_file(Unpicklerobject *self, char **s, int  n) {

    if (self->buf_size == 0) {
        int size;

        size = ((n < 32) ? 32 : n); 
        UNLESS(self->buf = (char *)malloc(size * sizeof(char))) {
            PyErr_NoMemory();
            return -1;
        }

        self->buf_size = size;
    }
    else if (n > self->buf_size) {
        UNLESS(self->buf = (char *)realloc(self->buf, n * sizeof(char))) {     
            PyErr_NoMemory();
            return -1;
        }
 
        self->buf_size = n;
    }
            
    if (fread(self->buf, sizeof(char), n, self->fp) != n) {  
        if (feof(self->fp)) {
            PyErr_SetNone(PyExc_EOFError);
            return -1;
        }

        PyErr_SetFromErrno(PyExc_IOError);
        return -1;
    }

    *s = self->buf;

    return n;
}


static int 
readline_file(Unpicklerobject *self, char **s) {
    int i;

    if (self->buf_size == 0) {
        UNLESS(self->buf = (char *)malloc(40 * sizeof(char))) {
            PyErr_NoMemory();
            return -1;
        }
   
        self->buf_size = 40;
    }

    i = 0;
    while (1) {
        for (; i < (self->buf_size - 1); i++) {
            if (feof(self->fp) || (self->buf[i] = getc(self->fp)) == '\n') {
                self->buf[i + 1] = '\0';
                *s = self->buf;
                return i + 1;
            }
        }

        UNLESS(self->buf = (char *)realloc(self->buf, 
            (self->buf_size * 2) * sizeof(char))) {
            PyErr_NoMemory();
            return -1;
        }

        self->buf_size *= 2;
    }

}    


static int 
read_cStringIO(Unpicklerobject *self, char **s, int  n) {
    char *ptr;
    int size;

    if (self->diddled_ptr) {
        *self->diddled_ptr = self->diddled_char;
        self->diddled_ptr = NULL;
    }

    if (PycStringIO->cread((PyObject *)self->file, &ptr, n) != n) {
        PyErr_SetNone(PyExc_EOFError);
        return -1;
    }

    *s = ptr;

    return n;
}


static int 
readline_cStringIO(Unpicklerobject *self, char **s) {
    int n, size;
    char *ptr;

    if (self->diddled_ptr) {
        *self->diddled_ptr = self->diddled_char;
        self->diddled_ptr = NULL;
    }

    if ((n = PycStringIO->creadline((PyObject *)self->file, &ptr)) < 0) {
        return -1;
    }

    /* start nasty hack */
    self->diddled_char = ptr[n];
    self->diddled_ptr  = ptr + n;
    *self->diddled_ptr = '\0';

    *s = ptr;

    return n;
}


static int 
read_other(Unpicklerobject *self, char **s, int  n) {
    PyObject *bytes, *str;
    char *ret_str;
    int size, res = -1;

    UNLESS(bytes = PyInt_FromLong(n)) {
        if (!PyErr_Occurred())
            PyErr_SetNone(PyExc_EOFError);

        goto finally;
    }

    UNLESS(self->arg)
        UNLESS(self->arg = PyTuple_New(1))
            goto finally;

    Py_INCREF(bytes);
    if (PyTuple_SetItem(self->arg, 0, bytes) < 0)
        goto finally;

    UNLESS(str = PyObject_CallObject(self->read, self->arg))
        goto finally;

    Py_XDECREF(self->last_string);
    self->last_string = str;

    *s = PyString_AsString(str);

    res = n;

finally:
     Py_XDECREF(bytes);

     return res;
}


static int 
readline_other(Unpicklerobject *self, char **s) {
    PyObject *str;
    int str_size, buf_size;

    UNLESS(str = PyObject_CallObject(self->readline, empty_tuple)) {
        return -1;
    }

    str_size = PyString_Size(str);

    Py_XDECREF(self->last_string);
    self->last_string = str;

    *s = PyString_AsString(str);

    return str_size;
}


static int
get(Picklerobject *self, PyObject *id) {
    PyObject *value = 0;
    long c_value;
    char s[30];
    int len;

    UNLESS(value = PyDict_GetItem(self->memo, id))
        return -1;

    c_value = PyInt_AsLong(value);

    if (!self->bin) {
        s[0] = GET;
        sprintf(s + 1, "%ld\n", c_value);
        len = strlen(s);
    }
    else {
        if (c_value < 256) {
            s[0] = BINGET;
            s[1] = (int)(c_value & 0xff);
            len = 2;
        }
        else {
            s[0] = LONG_BINGET;
            s[1] = (int)(c_value & 0xff);
            s[2] = (int)((c_value >> 8)  & 0xff);
            s[3] = (int)((c_value >> 16) & 0xff);
            s[4] = (int)((c_value >> 24) & 0xff);
            len = 5;
        }
    }

    if ((*self->write_func)(self, s, len) < 0)
        return -1;

    return 0;
}
    
    
static int
put(Picklerobject *self, PyObject *ob) {
    char c_str[30];
    int p, len, res = -1;
    PyObject *py_ob_id = 0, *memo_len = 0;

    if (ob->ob_refcnt < 2)
        return 0;

    if ((p = PyDict_Size(self->memo)) < 0)
        goto finally;

    if (!self->bin) {
        c_str[0] = PUT;
        sprintf(c_str + 1, "%d\n", p);
        len = strlen(c_str);
    }
    else {
        if (p >= 256) {
            c_str[0] = LONG_BINPUT;
            c_str[1] = (int)(p & 0xff);
            c_str[2] = (int)((p >> 8)  & 0xff);
            c_str[3] = (int)((p >> 16) & 0xff);
            c_str[4] = (int)((p >> 24) & 0xff);
            len = 5;
        }
        else {
            c_str[0] = BINPUT;
            c_str[1] = p;
            len = 2; 
        }
    }

    if ((*self->write_func)(self, c_str, len) < 0)
        goto finally;

    UNLESS(py_ob_id = PyInt_FromLong((long)ob))
        goto finally;

    UNLESS(memo_len = PyInt_FromLong(p))
        goto finally;

    if (PyDict_SetItem(self->memo, py_ob_id, memo_len) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_ob_id);
    Py_XDECREF(memo_len);

    return res;
}


static PyObject *
whichmodule(PyObject *global, PyObject *global_name) {
    int has_key, i, j;
    PyObject *module = 0, *modules_dict = 0,
        *global_name_attr = 0, *name = 0;

    if ((has_key = PyMapping_HasKey(class_map, global)) < 0)
        return NULL;

    if (has_key) {
        return ((module = PyDict_GetItem(class_map, global)) ? module : NULL);
    }

    UNLESS(modules_dict = PySys_GetObject("modules"))
        return NULL;

    i = 0;
    while (j = PyDict_Next(modules_dict, &i, &name, &module)) {
        UNLESS(global_name_attr = PyObject_GetAttr(module, global_name)) {
            PyErr_Clear();
            continue;
        }

        if (global_name_attr != global) {
            Py_DECREF(global_name_attr);
            continue;
        }

        Py_DECREF(global_name_attr);

        break;
    }
    
    if (!j) {
        PyErr_Format(PicklingError, "Could not find module for %s.", 
            "O", global_name);
        return NULL;
    }

    PyDict_SetItem(class_map, global, name);

    return name;
}


static int
save_none(Picklerobject *self, PyObject *args) {
    static char none = NONE;
    if ((*self->write_func)(self, &none, 1) < 0)  
        return -1;

    return 0;
}

      
static int
save_int(Picklerobject *self, PyObject *args) {
    char c_str[25];
    long l = PyInt_AS_LONG((PyIntObject *)args);
    int len = 0;

    if (!self->bin) {
        c_str[0] = INT;
        sprintf(c_str + 1, "%ld\n", l);
        if ((*self->write_func)(self, c_str, strlen(c_str)) < 0)
            return -1;
    }
    else {
        c_str[1] = (int)(l & 0xff);
        c_str[2] = (int)((l >> 8)  & 0xff);
        c_str[3] = (int)((l >> 16) & 0xff);
        c_str[4] = (int)((l >> 24) & 0xff);

        if (sizeof(long) == 8) {
            c_str[5] = (int)((l >> 32) & 0xff);
            c_str[6] = (int)((l >> 40) & 0xff);
            c_str[7] = (int)((l >> 48) & 0xff);
            c_str[8] = (int)((l >> 56) & 0xff);

            if ((c_str[8] != 0) || (c_str[7] != 0) ||
                (c_str[6] != 0) || (c_str[5] != 0)) {
                c_str[0] = BININT8;
                len = 9;
	    }
        }

        if (len == 0) {
            if ((c_str[4] == 0) && (c_str[3] == 0)) {
                if (c_str[2] == 0) {
                    c_str[0] = BININT1;
                    len = 2;
                }
                else {
                    c_str[0] = BININT2;
                    len = 3;
                }
            }
            else {
                c_str[0] = BININT;
                len = 5;
            }
        }

        if ((*self->write_func)(self, c_str, len) < 0)
            return -1;
    }

    return 0;
}


static int
save_long(Picklerobject *self, PyObject *args) {
    int size, res = -1;
    PyObject *repr = 0;

    static char l = LONG;

    UNLESS(repr = PyObject_Repr(args))
        goto finally;

    if ((size = PyString_Size(repr)) < 0)
        goto finally;

    if ((*self->write_func)(self, &l, 1) < 0)
        goto finally;

    if ((*self->write_func)(self, 
        PyString_AS_STRING((PyStringObject *)repr), size) < 0)
        goto finally;

    if ((*self->write_func)(self, "\n", 1) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(repr);

    return res;
}


static int
save_float(Picklerobject *self, PyObject *args) {
    char c_str[250];

    c_str[0] = FLOAT;
    sprintf(c_str + 1, "%f\n", PyFloat_AS_DOUBLE((PyFloatObject *)args));

    if ((*self->write_func)(self, c_str, strlen(c_str)) < 0)
        return -1;

    return 0;
}


static int
save_string(Picklerobject *self, PyObject *args) {
    int size;

    if (!self->bin) {
        PyObject *repr;
        char *repr_str;

        static char string = STRING;

        UNLESS(repr = PyObject_Repr(args))
            return -1;

        repr_str = PyString_AS_STRING((PyStringObject *)repr);
        size = PyString_Size(repr);

        if ((*self->write_func)(self, &string, 1) < 0)
            return -1;

        if ((*self->write_func)(self, repr_str, size) < 0)
            return -1;

        if ((*self->write_func)(self, "\n", 1) < 0)
            return -1;

        Py_XDECREF(repr);
    }
    else {
        int len, i;
        char c_str[5];

        size = PyString_Size(args);

        if (size < 256) {
            c_str[0] = SHORT_BINSTRING;
            c_str[1] = size;
            len = 2;
        }
        else {
            c_str[0] = BINSTRING;
            for (i = 1; i < 5; i++)
                c_str[i] = (int)(size << ((i - 1) * 8));
            len = 5;
        }

        if ((*self->write_func)(self, c_str, len) < 0)
            return -1;

        if ((*self->write_func)(self, 
            PyString_AS_STRING((PyStringObject *)args), size) < 0)
            return -1;
    }

    if (put(self, args) < 0)
        return -1;

    return 0;
}


static int
save_tuple(Picklerobject *self, PyObject *args) {
    PyObject *element = 0, *py_tuple_id = 0;
    int len, i, has_key, res = -1;

    static char tuple = TUPLE;

    if ((*self->write_func)(self, &MARKv, 1) < 0)
        goto finally;

    if ((len = PyTuple_Size(args)) < 0)  
        goto finally;

    for (i = 0; i < len; i++) {
        UNLESS(element = PyTuple_GET_ITEM((PyTupleObject *)args, i))  
            goto finally;
    
        if (save(self, element, 0) < 0)
            goto finally;
    }

    UNLESS(py_tuple_id = PyInt_FromLong((long)args))
        goto finally;

    if ((has_key = PyMapping_HasKey(self->memo, py_tuple_id)) < 0)
        goto finally;

    if (has_key) {
        static char pop = POP;

        while (i-- > 0) {
            if ((*self->write_func)(self, &pop, 1) < 0)
                goto finally;
        }
        
        if (get(self, py_tuple_id) < 0)
            goto finally;

        res = 0;
        goto finally;
    }

    if ((*self->write_func)(self, &tuple, 1) < 0) {
        goto finally;
    }
    
    if (put(self, args) < 0)
        goto finally;
 
     res = 0;

finally:
    Py_XDECREF(py_tuple_id);

    return res;
}


static int
save_list(Picklerobject *self, PyObject *args) {
    PyObject *element = 0;
    int s_len, len, i, using_appends, res = -1;
    char s[3];

    static char append = APPEND, appends = APPENDS;

    s[0] = MARK;
    s[1] = LIST;
    s_len = 2;

    if ((len = PyList_Size(args)) < 0)
        goto finally;

    using_appends = (self->bin && (len > 1));

    if (using_appends) {
        s[2] = MARK;
        s_len++;
    }

    if ((*self->write_func)(self, s, s_len) < 0)
        goto finally;

    for (i = 0; i < len; i++) {
        UNLESS(element = PyList_GET_ITEM((PyListObject *)args, i))  
            goto finally;

        if (save(self, element, 0) < 0)  
            goto finally;	

        if (!using_appends) {
            if ((*self->write_func)(self, &append, 1) < 0)
                goto finally;
        }
    }

    if (using_appends) {
        if ((*self->write_func)(self, &appends, 1) < 0)
            goto finally;
    }

    if (put(self, args) < 0)
        goto finally;

    res = 0;

finally:

    return res;
}


static int
save_dict(Picklerobject *self, PyObject *args) {
    PyObject *key = 0, *value = 0;
    int i, len, res = -1, using_setitems;
    char s[3];

    static char setitem = SETITEM, setitems = SETITEMS;

    s[0] = MARK;
    s[1] = DICT;
    len = 2;

    using_setitems = (self->bin && (PyDict_Size(args) > 1));

    if (using_setitems) {
        s[2] = MARK;
        len++;
    }

    if ((*self->write_func)(self, s, len) < 0)
        goto finally;

    i = 0;
    while (PyDict_Next(args, &i, &key, &value)) {
        if (save(self, key, 0) < 0)
            goto finally;

        if (save(self, value, 0) < 0)
            goto finally;

        if (!using_setitems) {
            if ((*self->write_func)(self, &setitem, 1) < 0)
                goto finally;
        }
    }

    if (using_setitems) {
        if ((*self->write_func)(self, &setitems, 1) < 0)
            goto finally;
    }

    if (put(self, args) < 0)
        goto finally;

    res = 0;

finally:

    return res;
}


static int  
save_inst(Picklerobject *self, PyObject *args) {
    PyObject *class = 0, *module = 0, *name = 0, *state = 0, 
             *getinitargs_func = 0, *getstate_func = 0, *class_args = 0;
    char *module_str, *name_str;
    int module_size, name_size, inst_class, res = -1;

    static char inst = INST, obj = OBJ, build = BUILD;
    static PyObject *__class__str = 0, *__getinitargs__str = 0, 
                    *__dict__str = 0, *__getstate__str = 0;

    if ((*self->write_func)(self, &MARKv, 1) < 0)
        goto finally;

    UNLESS(__class__str)
        UNLESS(__class__str = PyString_FromString("__class__"))
            goto finally;

    UNLESS(class = PyObject_GetAttr(args, __class__str))
        goto finally;

    class_inst = PyClass_Check(class);

    if (self->bin && class_inst) {
        if (save(self, class, 0) < 0)
            goto finally;
    }

    UNLESS(__getinitargs__str)
        UNLESS(__getinitargs__str = PyString_FromString("__getinitargs__"))
            goto finally;

    if (getinitargs_func = PyObject_GetAttr(args, __getinitargs__str)) {
        PyObject *element = 0;
        int i, len;

        UNLESS(class_args = PyObject_CallObject(getinitargs_func, empty_tuple))
            goto finally;

        if (class_inst)
        {
            if ((len = PyObject_Length(class_args)) < 0)  
                goto finally;

            for (i = 0; i < len; i++) {
                UNLESS(element = PySequence_GetItem(class_args, i)) 
                    goto finally;

                if (save(self, element, 0) < 0) {
                    Py_DECREF(element);
                    goto finally;
                }

                Py_DECREF(element);
            }
        }
    }
    else {
        PyErr_Clear();
    }

    if (!class_inst)
    {
        if (!class_args)
            UNLESS(class_args = PyTuple_New(0));
                goto finally;
    
        UNLESS(save_global(class, class_args))
            goto finally;
    }
    else {
        if (!self->bin) {
            UNLESS(name = ((PyClassObject *)class)->cl_name) {
                PyErr_SetString(PicklingError, "class has no name");
                goto finally;
            }

            UNLESS(module = whichmodule(class, name))
                goto finally;
    
            module_str = PyString_AS_STRING((PyStringObject *)module);
            module_size = PyString_Size(module);
            name_str   = PyString_AS_STRING((PyStringObject *)name);
            name_size = PyString_Size(name);

            if ((*self->write_func)(self, &inst, 1) < 0)
                goto finally;

            if ((*self->write_func)(self, module_str, module_size) < 0)
                goto finally;

            if ((*self->write_func)(self, "\n", 1) < 0)
                goto finally;

            if ((*self->write_func)(self, name_str, name_size) < 0)
                goto finally;

             if ((*self->write_func)(self, "\n", 1) < 0)
                goto finally;
        }
        else if ((*self->write_func)(self, &obj, 1) < 0) {
            goto finally;
        }
    }
    else if (put(self, args) < 0)
    {
         goto finally;
    }

    UNLESS(__getstate__str)
        UNLESS(__getstate__str = PyString_FromString("__getstate__"))
            goto finally;

    if (getstate_func = PyObject_GetAttr(args, __getstate__str)) {
        UNLESS(state = PyObject_CallObject(getstate_func, empty_tuple))
            goto finally;
    }
    else {
        PyErr_Clear();

        UNLESS(__dict__str)
            UNLESS(__dict__str = PyString_FromString("__dict__"))
                goto finally;

        UNLESS(state = PyObject_GetAttr(args, __dict__str)) {
            PyErr_Clear();
            res = 0;
            goto finally;
        }
    }

    if (save(self, state, 0) < 0)
        goto finally;

    if ((*self->write_func)(self, &build, 1) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(class);
    Py_XDECREF(state);
    Py_XDECREF(getinitargs_func);
    Py_XDECREF(getstate_func);
    Py_XDECREF(class_args);

    return res;
}


static int
save_global(Picklerobject *self, PyObject *args) {
    PyObject *name = 0, *module = 0;
    char *name_str, *module_str, *c_str; 
    int module_size, name_size, size, res = -1;

    static char global = GLOBAL;
    static PyObject *__name__str = 0;

    UNLESS(__name__str)
        UNLESS(__name__str = PyString_FromString("__name__"))
            return -1;

    UNLESS(name = PyObject_GetAttr(args, __name__str))
        goto finally;

    UNLESS(module = whichmodule(args, name))
        goto finally;

    module_str = PyString_AS_STRING((PyStringObject *)module);
    module_size = PyString_Size(module);
    name_str   = PyString_AS_STRING((PyStringObject *)name);
    name_size = PyString_Size(name);

    if ((*self->write_func)(self, &global, 1) < 0)
        goto finally;

    if ((*self->write_func)(self, module_str, module_size) < 0)
        goto finally;

    if ((*self->write_func)(self, "\n", 1) < 0)
        goto finally;

    if ((*self->write_func)(self, name_str, name_size) < 0)
        goto finally;

    if ((*self->write_func)(self, "\n", 1) < 0)
        goto finally;

    if (put(self, args) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(name);

    return res;
}


save_pers(Picklerobject *self, PyObject *args, PyObject *f) {
    PyObject *pid = 0;
    int size, res = -1;

    static char persid = PERSID, binpersid = BINPERSID;

    UNLESS(self->arg)
        UNLESS(self->arg = PyTuple_New(1))
            goto finally;
    
    Py_INCREF(args);      
    if (PyTuple_SetItem(self->arg, 0, args) < 0)
        goto finally;
    
    UNLESS(pid = PyObject_CallObject(f, self->arg))
        goto finally;

    if (pid != Py_None) {
        if (!self->bin) {
            if (!PyString_Check(pid)) {
                PyErr_SetString(PicklingError, 
                    "persistent id must be string");
                goto finally;
            }

            if ((*self->write_func)(self, &persid, 1) < 0)
                goto finally;

            if ((size = PyString_Size(pid)) < 0)
                goto finally;

            if ((*self->write_func)(self, 
                PyString_AS_STRING((PyStringObject *)pid), size) < 0)
                goto finally;

            if ((*self->write_func)(self, "\n", 1) < 0)
                goto finally;
     
            res = 1;
            goto finally;
        }
        else if (save(self, pid, 1) >= 0) {
            if ((*self->write_func)(self, &binpersid, 1) < 0)
                res = -1;
            else
                res = 1;
        }

        goto finally;              
    }

    res = 0;

finally:
    Py_XDECREF(pid);

    return res;
}


static int 
save_reduce(Picklerobject *self, PyObject *callable, PyObject *tup) {
    static char reduce = REDUCE;

    if (save(self, callable, 0) < 0)
        return -1;

    if (save(self, tup, 0) < 0)
        return -1;

    return (*self->write_func)(self, &reduce, 1);
}


static int
save(Picklerobject *self, PyObject *args, int  pers_save) {
    PyTypeObject *type;
    PyObject *py_ob_id = 0, *__reduce__ = 0, *t = 0, *arg_tup = 0,
             *callable = 0;
    int res = -1, tmp;

    static PyObject *__reduce__str = 0;

    if (!pers_save && self->pers_func) {
        if ((tmp = save_pers(self, args, self->pers_func)) != 0) {
            res = tmp;
            goto finally;
        }
    }

    if (args == Py_None) {
        res = save_none(self, args);
        goto finally;
    }

    type = args->ob_type;

    switch (type->tp_name[0]) {
        case 'i':
            if (type == &PyInt_Type) {
                res = save_int(self, args);
                goto finally;
            }

            break;

        case 'l':
            if (type == &PyLong_Type) {
                res = save_long(self, args);
                goto finally;
            }

            break;

        case 'f':
            if (type == &PyFloat_Type) {
                res = save_float(self, args);
                goto finally;
            }
    }

    if (args->ob_refcnt > 1) {
        long ob_id;
        int  has_key;

        ob_id = (long)args;

        UNLESS(py_ob_id = PyInt_FromLong(ob_id))
            goto finally;

        if ((has_key = PyMapping_HasKey(self->memo, py_ob_id)) < 0)
            goto finally;

        if (has_key) {
            if (get(self, py_ob_id) < 0)
                goto finally;

            res = 0;
            goto finally;
        }
    }

    switch (type->tp_name[0]) {
        case 's':
            if (type == &PyString_Type) {
                res = save_string(self, args);
                goto finally;
            }

        case 't':
            if (type == &PyTuple_Type) {
                res = save_tuple(self, args);
                goto finally;
	    }

        case 'l':
            if (type == &PyList_Type) {
                res = save_list(self, args);
                goto finally;
            }

        case 'd':
            if (type == &PyDict_Type) {
                res = save_dict(self, args);
                goto finally; 
            }

        case 'i':
            if (type == &PyInstance_Type) {
                res = save_inst(self, args);
                goto finally;
            }

        case 'c':
            if (type == &PyClass_Type) {
                res = save_global(self, args);
                goto finally;
            }

        case 'f':
            if (type == &PyFunction_Type) {
                res = save_global(self, args);
                goto finally;
            }

        case 'b':
            if (type == &PyCFunction_Type) {
                res = save_global(self, args);
                goto finally;
            }
    }

    if (!pers_save && self->inst_pers_func) {
        if ((tmp = save_pers(self, args, self->inst_pers_func)) != 0) {
            res = tmp;
            goto finally;
        }
    }

    if (__reduce__ = PyDict_GetItem(dispatch_table, (PyObject *)type)) {
        Py_INCREF(__reduce__);

        UNLESS(self->arg)
            UNLESS(self->arg = PyTuple_New(1))
                goto finally;

        Py_INCREF(args);
        if (PyTuple_SetItem(self->arg, 0, args) < 0)
            goto finally;

        UNLESS(t = PyObject_CallObject(__reduce__, self->arg))
            goto finally;
    }        
    else {
        PyErr_Clear();

        UNLESS(__reduce__str)
            UNLESS(__reduce__str = PyString_FromString("__reduce__"))
                goto finally;

        if (__reduce__ = PyObject_GetAttr(args, __reduce__str)) {
            UNLESS(t = PyObject_CallObject(__reduce__, empty_tuple))
                goto finally;
        }
        else {
            PyErr_Clear();
        }
    }

    if (t) {
        if (!PyTuple_Check(t)) {
            PyErr_Format(PicklingError, "Value returned by %s must be a tuple", "O",
                __reduce__);
            goto finally;
        }

        UNLESS(callable = PyTuple_GetItem(t, 0))
            goto finally;

        UNLESS(arg_tup = PyTuple_GetItem(t, 1))
            goto finally;

        UNLESS(PyTuple_Check(arg_tup)) {
            PyErr_Format(PicklingError, "Second element of tuple "
                "returned by %s must be a tuple", "O", __reduce__);
            goto finally;
        }

        res = save_reduce(self, callable, arg_tup);
        goto finally;
    }

    if (PyObject_HasAttrString(args, "__class__")) {
        res = save_inst(self, args);
        goto finally;
    }

    PyErr_Format(PicklingError, "Cannot pickle %s objects.", 
        "O", (PyObject *)type);

finally:
    Py_XDECREF(py_ob_id);
    Py_XDECREF(__reduce__);
    Py_XDECREF(t);
   
    return res;
}


static PyObject *
Pickler_dump(Picklerobject *self, PyObject *args) {
    static char stop = STOP;

    UNLESS(PyArg_Parse(args, "O", &args))
        return NULL;

    if (save(self, args, 0) < 0)
        return NULL;

    if ((*self->write_func)(self, &stop, 1) < 0)
        return NULL;

    if ((*self->write_func)(self, NULL, 0) < 0)
        return NULL;

    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *
dump_special(Picklerobject *self, PyObject *args) {
    static char stop = STOP;

    PyObject *callable = 0, *arg_tup = 0;
    
    UNLESS(PyArg_ParseTuple(args, "OO", &callable, &arg_tup))
        return NULL;

    UNLESS(PyTuple_Check(arg_tup)) {
        PyErr_SetString(PicklingError, "Second arg to dump_special must "
            "be tuple");
        return NULL;
    }

    if (save_reduce(self, callable, arg_tup) < 0)
        return NULL;

    if ((*self->write_func)(self, &stop, 1) < 0)
        return NULL;

    if ((*self->write_func)(self, NULL, 0) < 0)
        return NULL;

    Py_INCREF(Py_None);
    return Py_None;
}


static struct PyMethodDef Pickler_methods[] = {
  {"dump",          (PyCFunction)Pickler_dump,  0, ""},
  {"dump_special",  (PyCFunction)dump_special,  1, ""},
  {NULL,                NULL}           /* sentinel */
};


static Picklerobject *
newPicklerobject(PyObject *file, int  bin) {
    Picklerobject *self;
    PyObject *memo = 0;

    UNLESS(memo = PyDict_New())  goto err;

    UNLESS(self = PyObject_NEW(Picklerobject, &Picklertype))  
        goto err;

    if (PyFile_Check(file)) {
        self->fp = PyFile_AsFile(file);
        self->write_func = write_file;
        self->write = NULL;
        self->write_buf = NULL;
    }
    else if (PycStringIO_OutputCheck(file)) {
        self->fp = NULL;
        self->write_func = write_cStringIO;
        self->write = NULL;
        self->write_buf = NULL;
    }
    else {
        PyObject *write; 
        static PyObject *write_str = 0;

        self->fp = NULL;
        self->write_func = write_other;

        UNLESS(write_str)
            UNLESS(write_str = PyString_FromString("write"))
                goto err;

        UNLESS(write = PyObject_GetAttr(file, write_str))
            goto err;

        self->write = write;

        UNLESS(self->write_buf = 
            (char *)malloc(WRITE_BUF_SIZE * sizeof(char))) { 
            PyErr_NoMemory();
            goto err;
        }


        self->buf_size = 0;
    }

    Py_INCREF(file);

    self->file  = file;
    self->bin   = bin;
    self->memo  = memo;
    self->arg   = NULL;
    self->pers_func = NULL;
    self->inst_pers_func = NULL;

    return self;

err:
    Py_XDECREF((PyObject *)self);
    Py_XDECREF(memo);
    return NULL;
}


static PyObject *
get_Pickler(PyObject *self, PyObject *args) {
    PyObject *file;
    int bin = 0;

    UNLESS(PyArg_ParseTuple(args, "O|i", &file, &bin))  return NULL;
    return (PyObject *)newPicklerobject(file, bin);
}


static void
Pickler_dealloc(Picklerobject *self) {
    Py_XDECREF(self->write);
    Py_XDECREF(self->memo);
    Py_XDECREF(self->arg);
    Py_XDECREF(self->file);
    Py_XDECREF(self->pers_func);
    Py_XDECREF(self->inst_pers_func);

    if (self->write_buf) {    
        free(self->write_buf);
    }

    PyMem_DEL(self);
}


static PyObject *
Pickler_getattr(Picklerobject *self, char *name) {
    if (strcmp(name, "persistent_id") == 0) {
        if (!self->pers_func) {
            PyErr_SetString(PyExc_AttributeError, name);
            return NULL;
        }

        Py_INCREF(self->pers_func);
        return self->pers_func;
    }

    if (strcmp(name, "memo") == 0) {
        if (!self->memo) {
            PyErr_SetString(PyExc_AttributeError, name);
            return NULL;
        }

        Py_INCREF(self->memo);
        return self->memo;
    }

    if (strcmp(name, "PicklingError") == 0) {
        Py_INCREF(PicklingError);
        return PicklingError;
    }
  
    return Py_FindMethod(Pickler_methods, (PyObject *)self, name);
}


int 
Pickler_setattr(Picklerobject *self, char *name, PyObject *value) {
    if (strcmp(name, "persistent_id") == 0) {
        Py_XDECREF(self->pers_func);
        self->pers_func = value;
        Py_INCREF(value);
        return 0;
    }

    if (strcmp(name, "inst_persistent_id") == 0) {
        Py_XDECREF(self->inst_pers_func);
        self->inst_pers_func = value;
        Py_INCREF(value);
        return 0;
    }

    PyErr_SetString(PyExc_AttributeError, name);
    return -1;
}


static char Picklertype__doc__[] = "";

static PyTypeObject Picklertype = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,                            /*ob_size*/
    "Pickler",                    /*tp_name*/
    sizeof(Picklerobject),                /*tp_basicsize*/
    0,                            /*tp_itemsize*/
    /* methods */
    (destructor)Pickler_dealloc,  /*tp_dealloc*/
    (printfunc)0,         /*tp_print*/
    (getattrfunc)Pickler_getattr, /*tp_getattr*/
    (setattrfunc)Pickler_setattr, /*tp_setattr*/
    (cmpfunc)0,           /*tp_compare*/
    (reprfunc)0,          /*tp_repr*/
    0,                    /*tp_as_number*/
    0,            /*tp_as_sequence*/
    0,            /*tp_as_mapping*/
    (hashfunc)0,          /*tp_hash*/
    (ternaryfunc)0,               /*tp_call*/
    (reprfunc)0,          /*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Picklertype__doc__ /* Documentation string */
};


PyObject *
PyImport_ImportModuleNi(char *module_name)
{
    char *import_str;
    int size, i;
    PyObject *import;

    static PyObject *eval_dict = 0;

    size = strlen(module_name);
    for (i = 0; i < size; i++) {
        if (((module_name[i] < 'A') || (module_name[i] > 'z')) &&
            (module_name[i] != '_')) {
            PyErr_SetString(PyExc_ImportError, "module name contains "
                "invalid characters.");
            return NULL;
        }
    }

    UNLESS(import_str = 
        (char *)malloc((strlen(module_name) + 15) * sizeof(char))) {
        PyErr_NoMemory();
        return NULL;
    }

    sprintf(import_str, "__import__('%s')", module_name);

    UNLESS(eval_dict)
        UNLESS(eval_dict = Py_BuildValue("{sO}", "__builtins__", builtins))
            return NULL;

    if (!(import = PyRun_String(import_str, eval_input, eval_dict, eval_dict)))
    {
        free(import_str);
        return NULL;
    }

    free(import_str);

    return import;
}


static PyObject *
find_class(PyObject *py_module_name, PyObject *py_class_name) {
    PyObject *import = 0, *class = 0, *t = 0;
    char *module_name, *class_name;
    PyObject *res = NULL;

    static PyObject *eval_dict = 0;

    module_name = PyString_AS_STRING((PyStringObject *)py_module_name);
    class_name  = PyString_AS_STRING((PyStringObject *)py_class_name);

    UNLESS(t = PyTuple_New(2))
        goto finally;

    PyTuple_SET_ITEM((PyTupleObject *)t, 0, py_module_name);
    Py_INCREF(py_module_name);
  
    PyTuple_SET_ITEM((PyTupleObject *)t, 1, py_class_name);
    Py_INCREF(py_class_name);

    if (class = PyDict_GetItem(class_map, t)) {
        res = class;
        goto finally;
    }

    PyErr_Clear();

    if (!(import = PyImport_ImportModuleNi(module_name)) ||    
        !(class = PyObject_GetAttr(import, py_class_name))) {
        PyErr_Format(PyExc_SystemError, "Failed to import global %s "
            "from module %s", "ss", class_name, module_name);
        goto finally;
    }  

    if (PyDict_SetItem(class_map, t, class) < 0)
        goto finally;

    Py_DECREF(class);
    Py_DECREF(t);
    Py_DECREF(import);

    res = class;
    return class;

finally:
    Py_XDECREF(import);
    Py_XDECREF(class);
    Py_XDECREF(t);
 
    return res;
}


static int
marker(Unpicklerobject *self) {
    return ((self->num_marks < 1) ? -1 : self->marks[--self->num_marks]);
}

    
static int
load_none(Unpicklerobject *self, PyObject *args) {
    if (PyList_Append(self->stack, Py_None) < 0)
        return -1;

    return 0;
}


static int
load_int(Unpicklerobject *self, PyObject *args) {
    PyObject *py_int = 0;
    char *endptr, *s;
    int len, res = -1;
    long l;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    errno = 0;
    l = strtol(s, &endptr, 0);

    if (errno || (endptr[0] != '\n') || (endptr[1] != '\0')) {
        PyErr_SetString(PyExc_ValueError, "could not convert string to int");
        goto finally;
    }

    UNLESS(py_int = PyInt_FromLong(l))
        goto finally;

    if (PyList_Append(self->stack, py_int) < 0)
        goto finally;

    res = 0;

finally:
  Py_XDECREF(py_int);

  return res;
}


static long 
calc_binint(char *s, int  x) {
    unsigned char c;
    int i;
    long l;

    for (i = 0, l = 0L; i < x; i++) {
        c = (unsigned char)s[i];
        l |= (long)c << (i * 8);
    }

    return l;
}


static int
load_binintx(Unpicklerobject *self, char *s, int  x) {
    PyObject *py_int = 0;
    long l;

    l = calc_binint(s, x);

    UNLESS(py_int = PyInt_FromLong(l))
        return -1;
    
    if (PyList_Append(self->stack, py_int) < 0) {
        Py_DECREF(py_int);
        return -1;
    }

    Py_DECREF(py_int);
    
    return 0;
}


static int
load_binint(Unpicklerobject *self, PyObject *args) {
    char *s;

    if ((*self->read_func)(self, &s, 4) < 0)
        return -1;

    return load_binintx(self, s, 4);
}


static int
load_binint1(Unpicklerobject *self, PyObject *args) {
    char *s;

    if ((*self->read_func)(self, &s, 1) < 0)
        return -1;

    return load_binintx(self, s, 1);
}


static int
load_binint2(Unpicklerobject *self, PyObject *args) {
    char *s;

    if ((*self->read_func)(self, &s, 2) < 0)
        return -1;

    return load_binintx(self, self->buf, 2);
}


static int
load_binint8(Unpicklerobject *self, PyObject *args) {
    PyObject *l = 0;
    char *end, *s;
    int res = -1;

    if ((*self->read_func)(self, &s, 8) < 0)
        goto finally;

    /* load a python int if we can */
    if (sizeof(long) == 8) {
        res = load_binintx(self, s, 8);
        goto finally;
    }

    /* load a python long otherwise */
    UNLESS(l = PyLong_FromString(s, &end, 0))
        goto finally;

    if (PyList_Append(self->stack, l) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(l);

    return res;
}

    
static int
load_long(Unpicklerobject *self, PyObject *args) {
    PyObject *l = 0;
    char *end, *s, *s2;
    int len, res = -1;

    static PyObject *arg = 0;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    UNLESS(l = PyLong_FromString(s, &end, 0))
        goto finally;

    if (PyList_Append(self->stack, l) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(l);

    return res;
}

 
static int
load_float(Unpicklerobject *self, PyObject *args) {
    PyObject *py_float = 0;
    char *endptr, *s;
    int len, res = -1;
    double d;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    errno = 0;
    d = strtod(s, &endptr);

    if (errno || (endptr[0] != '\n') || (endptr[1] != '\0')) {
        PyErr_SetString(PyExc_ValueError, "could not convert string to float");
        goto finally;
    }

    UNLESS(py_float = PyFloat_FromDouble(d))
        goto finally;

    if (PyList_Append(self->stack, py_float) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_float);

    return res;
}


static int
load_string(Unpicklerobject *self, PyObject *args) {
    PyObject *str = 0;
    int len, res = -1, i;
    char *s;

    static PyObject *eval_dict = 0;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    UNLESS(eval_dict)
        UNLESS(eval_dict = Py_BuildValue("{s{}}", "__builtins__"))
            goto finally;

    UNLESS(str = PyRun_String(s, eval_input, eval_dict, eval_dict))
        goto finally;

    if (PyList_Append(self->stack, str) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(str);

    return res;
} 


static int
load_binstring(Unpicklerobject *self, PyObject *args) {
    PyObject *py_string = 0;
    long l;
    int res = -1;
    char *s;

    if ((*self->read_func)(self, &s, 4) < 0)
        goto finally;

    l = calc_binint(s, 4);

    if ((*self->read_func)(self, &s, l) < 0)
        goto finally;

    UNLESS(py_string = PyString_FromStringAndSize(s, l))
        goto finally;

    if (PyList_Append(self->stack, py_string) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_string);

    return res;
}


static int
load_short_binstring(Unpicklerobject *self, PyObject *args) {
    PyObject *py_string = 0;
    unsigned char l;  
    int res = -1;
    char *s;

    if ((*self->read_func)(self, &s, 1) < 0)
        return -1;

    l = (unsigned char)self->buf[0];

    if ((*self->read_func)(self, &s, l) < 0)
        goto finally;

    UNLESS(py_string = PyString_FromStringAndSize(s, l))
        goto finally;

    if (PyList_Append(self->stack, py_string) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_string);

    return res;
} 


static int
load_tuple(Unpicklerobject *self, PyObject *args) {
    PyObject *tup = 0, *slice = 0, *list = 0;
    int i, j, res = -1;

    i = marker(self);

    if ((j = PyList_Size(self->stack)) < 0)  
        goto finally;

    UNLESS(slice = PyList_GetSlice(self->stack, i, j))
        goto finally;
  
    UNLESS(tup = PySequence_Tuple(slice))
        goto finally;

    UNLESS(list = PyList_New(1))
        goto finally;

    Py_INCREF(tup);
    if (PyList_SetItem(list, 0, tup) < 0)
        goto finally;

    if (PyList_SetSlice(self->stack, i, j, list) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(tup);
    Py_XDECREF(list);
    Py_XDECREF(slice);

    return res;
}


static int
load_list(Unpicklerobject *self, PyObject *args) {
    PyObject *list = 0, *slice = 0;
    int i, j, res = -1;

    i = marker(self);

    if ((j = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(slice = PyList_GetSlice(self->stack, i, j))
        goto finally;

    UNLESS(list = PyList_New(1))
        goto finally;

    Py_INCREF(slice);
    if (PyList_SetItem(list, 0, slice) < 0)
        goto finally;

    if (PyList_SetSlice(self->stack, i, j, list) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(list);
    Py_XDECREF(slice);

    return res;
}


static int
load_dict(Unpicklerobject *self, PyObject *args) {
    PyObject *list = 0, *dict = 0, *key = 0, *value = 0;
    int i, j, k, res = -1;

    i = marker(self);

    if ((j = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(dict = PyDict_New())
        goto finally;

    for (k = i; k < j; k += 2) {
        UNLESS(key = PyList_GET_ITEM((PyListObject *)self->stack, k))
            goto finally;

        UNLESS(value = PyList_GET_ITEM((PyListObject *)self->stack, k + 1))
            goto finally;

        if (PyDict_SetItem(dict, key, value) < 0)
            goto finally;
    }

    UNLESS(list = PyList_New(1))
        goto finally;

    Py_INCREF(dict);
    if (PyList_SetItem(list, 0, dict) < 0)
        goto finally;

    if (PyList_SetSlice(self->stack, i, j, list) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(dict);
    Py_XDECREF(list);

    return res;
}


static int
load_obj(Unpicklerobject *self, PyObject *args) {
    PyObject *class = 0, *slice = 0, *tup = 0, *obj = 0;
    int i, len, res = -1;

    i = marker(self);

    class = PyList_GET_ITEM((PyListObject *)self->stack, i);
    Py_INCREF(class);

    if ((len = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(slice = PyList_GetSlice(self->stack, i + 1, len))
        goto finally;

    UNLESS(tup = PySequence_Tuple(slice))
        goto finally;

    if (DEL_LIST_SLICE(self->stack, i, len) < 0)
        goto finally;

    UNLESS(obj = PyInstance_New(class, tup, NULL))
        goto finally;

    if (PyList_Append(self->stack, obj) < 0)
        goto finally;
  
    res = 0;

finally:
    Py_XDECREF(class);
    Py_XDECREF(slice);
    Py_XDECREF(tup);
    Py_XDECREF(obj);

    return res;
}


static int
load_inst(Unpicklerobject *self, PyObject *args) {
    PyObject *arg_tup = 0, *arg_slice = 0, *class = 0, *obj = 0,
             *module_name = 0, *class_name = 0;
    int i, j, len, res = -1;
    char *s;

    i = marker(self);

    if ((j = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(arg_slice = PyList_GetSlice(self->stack, i, j))
        goto finally;

    UNLESS(arg_tup = PySequence_Tuple(arg_slice))
        goto finally;

    if (DEL_LIST_SLICE(self->stack, i, j) < 0)
        goto finally;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    UNLESS(module_name = PyString_FromStringAndSize(s, len - 1))
        goto finally;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    UNLESS(class_name = PyString_FromStringAndSize(s, len - 1))
        goto finally;

    UNLESS(class = find_class(module_name, class_name))
        goto finally;

    UNLESS(obj = PyInstance_New(class, arg_tup, NULL))
        goto finally;

    if (PyList_Append(self->stack, obj) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(arg_slice);
    Py_XDECREF(arg_tup);
    Py_XDECREF(obj);
    Py_XDECREF(module_name);
    Py_XDECREF(class_name);

    return res;
}


static int
load_global(Unpicklerobject *self, PyObject *args) {
    PyObject *class = 0, *module_name = 0, *class_name = 0;
    int res = -1, len;
    char *s;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    UNLESS(module_name = PyString_FromStringAndSize(s, len - 1))
        goto finally;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    UNLESS(class_name = PyString_FromStringAndSize(s, len - 1))
        goto finally;

    UNLESS(class = find_class(module_name, class_name))
        goto finally;

    if (PyList_Append(self->stack, class) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(module_name);
    Py_XDECREF(class_name);

    return res;
}


static int
load_persid(Unpicklerobject *self, PyObject *args) {
    PyObject *pid = 0, *pers_load_val = 0;
    int len, res = -1;
    char *s;

    if (self->pers_func) {
        if ((len = (*self->readline_func)(self, &s)) < 0)
            goto finally;
  
        UNLESS(pid = PyString_FromStringAndSize(s, len - 1))
           goto finally;

        UNLESS(self->arg)
            UNLESS(self->arg = PyTuple_New(1))
                goto finally;

        Py_INCREF(pid);
        if (PyTuple_SetItem(self->arg, 0, pid) < 0)
            goto finally;
      
        UNLESS(pers_load_val = PyObject_CallObject(self->pers_func, self->arg))
            goto finally;

        if (PyList_Append(self->stack, pers_load_val) < 0)
            goto finally;
    }

    res = 0;

finally:
    Py_XDECREF(pid);
    Py_XDECREF(pers_load_val);

    return res;
}


static int
load_binpersid(Unpicklerobject *self, PyObject *args) {
    PyObject *pid = 0, *pers_load_val = 0;
    int len, res = -1;

    if (self->pers_func) {
        if ((len = PyList_Size(self->stack)) < 0)
            goto finally;

        pid = PyList_GET_ITEM((PyListObject *)self->stack, len - 1);
        Py_INCREF(pid);
 
        if (DEL_LIST_SLICE(self->stack, len - 1, len) < 0)
            goto finally;

        UNLESS(self->arg)
            UNLESS(self->arg = PyTuple_New(1))
                goto finally;

        Py_INCREF(pid);
        if (PyTuple_SetItem(self->arg, 0, pid) < 0)
            goto finally;

        UNLESS(pers_load_val = PyObject_CallObject(self->pers_func, self->arg))
            goto finally;

        if (PyList_Append(self->stack, pers_load_val) < 0)
            goto finally;
    }

    res = 0;

finally:
    Py_XDECREF(pid);
    Py_XDECREF(pers_load_val);

    return res;
}


static int
load_pop(Unpicklerobject *self, PyObject *args) {
    int len;

    if ((len = PyList_Size(self->stack)) < 0)  
        return -1;

    if (DEL_LIST_SLICE(self->stack, len - 1, len) < 0)  
        return -1;

    return 0;
}


static int
load_dup(Unpicklerobject *self, PyObject *args) {
    PyObject *last;
    int len;

    if ((len = PyList_Size(self->stack)) < 0)
        return -1;
  
    UNLESS(last = PyList_GetItem(self->stack, len - 1))  
        return -1;

    if (PyList_Append(self->stack, last) < 0)
        return -1;

    return 0;
}


static int
load_get(Unpicklerobject *self, PyObject *args) {
    PyObject *py_str = 0, *value = 0;
    int len, res = -1;
    char *s;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    UNLESS(py_str = PyString_FromStringAndSize(s, len - 1))
        goto finally;
  
    UNLESS(value = PyDict_GetItem(self->memo, py_str))  
        goto finally;

    if (PyList_Append(self->stack, value) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_str);

    return res;
}


static int
load_binget(Unpicklerobject *self, PyObject *args) {
    PyObject *py_key = 0, *value = 0;
    unsigned char key;
    int res = -1;
    char *s;

    if ((*self->read_func)(self, &s, 1) < 0)
        goto finally;

    key = (unsigned char)s[0];

    UNLESS(py_key = PyInt_FromLong((long)key))
        goto finally;

    UNLESS(value = PyDict_GetItem(self->memo, py_key))  
        goto finally;

    if (PyList_Append(self->stack, value) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_key);

    return res;
}


static int
load_long_binget(Unpicklerobject *self, PyObject *args) {
    PyObject *py_key = 0, *value = 0;
    unsigned char c, *s;
    long key;
    int res = -1;

    if ((*self->read_func)(self, &s, 4) < 0)
        goto finally;

    c = (unsigned char)s[0];
    key = (long)c;
    c = (unsigned char)s[1];
    key |= (long)c << 8;
    c = (unsigned char)s[2];
    key |= (long)c << 16;
    c = (unsigned char)s[3];
    key |= (long)c << 24;

    UNLESS(py_key = PyInt_FromLong(key))
        goto finally;

    UNLESS(value = PyDict_GetItem(self->memo, py_key))  
        goto finally;

    if (PyList_Append(self->stack, value) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_key);

    return res;
}


static int
load_put(Unpicklerobject *self, PyObject *args) {
    PyObject *py_str = 0, *value = 0;
    int len, res = -1;
    char *s;

    if ((len = (*self->readline_func)(self, &s)) < 0)
        goto finally;

    UNLESS(py_str = PyString_FromStringAndSize(s, len - 1))
        goto finally;

    if ((len = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(value = PyList_GetItem(self->stack, len - 1))  
        goto finally;

    if (PyDict_SetItem(self->memo, py_str, value) < 0)  
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_str);

    return res;
}


static int
load_binput(Unpicklerobject *self, PyObject *args) {
    PyObject *py_key = 0, *value = 0;
    unsigned char key, *s;
    int len, res = -1;

    if ((*self->read_func)(self, &s, 1) < 0)
        goto finally;

    key = (unsigned char)s[0];

    UNLESS(py_key = PyInt_FromLong((long)key))
        goto finally;

    if ((len = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(value = PyList_GetItem(self->stack, len - 1))  
        goto finally;

    if (PyDict_SetItem(self->memo, py_key, value) < 0)  
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_key);

    return res;
}


static int
load_long_binput(Unpicklerobject *self, PyObject *args) {
    PyObject *py_key = 0, *value = 0;
    long key;
    unsigned char c, *s;
    int len, res = -1;

    if ((*self->read_func)(self, &s, 4) < 0)
        goto finally;

    c = (unsigned char)s[0];
    key = (long)c;
    c = (unsigned char)s[1];
    key |= (long)c << 8;
    c = (unsigned char)s[2];
    key |= (long)c << 16;
    c = (unsigned char)s[3];
    key |= (long)c << 24;

    UNLESS(py_key = PyInt_FromLong(key))
        goto finally;

    if ((len = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(value = PyList_GetItem(self->stack, len - 1))  
        goto finally;

    if (PyDict_SetItem(self->memo, py_key, value) < 0)  
        goto finally;

    res = 0;

finally:
    Py_XDECREF(py_key);

    return res;
}


static int do_append(Unpicklerobject *self, int  x) {
    PyObject *value = 0, *list = 0, *append_method = 0;
    int len, i;

    if ((len = PyList_Size(self->stack)) < 0)  
        return -1;

    UNLESS(list = PyList_GetItem(self->stack, x - 1))  
        goto err;

    if (PyList_Check(list)) {
        PyObject *slice = 0;
        int list_len;
       
        UNLESS(slice = PyList_GetSlice(self->stack, x, len))
            return -1;
  
        list_len = PyList_Size(list);
        if (PyList_SetSlice(list, list_len, list_len, slice) < 0) {
            Py_DECREF(slice);
            return -1;
        }

        Py_DECREF(slice);
    }
    else {
        static PyObject *append_str = 0;

        UNLESS(append_str)
            UNLESS(append_str = PyString_FromString("append"))
                return -1;

        UNLESS(append_method = PyObject_GetAttr(list, append_str))
            return -1;
         
        for (i = x; i < len; i++) {
            UNLESS(value = PyList_GetItem(self->stack, i))  
                return -1;

            if (PyList_Check(list)) {
                if (PyList_Append(list, value) < 0)
                   goto err;
            }
            else {
                PyObject *junk;

                UNLESS(self->arg)
                    UNLESS(self->arg = PyTuple_New(1)) {
                        Py_DECREF(append_method);
                        goto err;
                    }

                Py_INCREF(value);
                if (PyTuple_SetItem(self->arg, 0, value) < 0) {
                    Py_DECREF(append_method);
                    goto err;
                }

                UNLESS(junk = PyObject_CallObject(append_method, self->arg)) {
                    Py_DECREF(append_method);
                    goto err;
                }
                Py_DECREF(junk);
            }
        }
    }

    if (DEL_LIST_SLICE(self->stack, x, len) < 0)  
        goto err;

    Py_XDECREF(append_method);

    return 0;

err:
    Py_XDECREF(append_method);
 
    return -1;
}

    
static int
load_append(Unpicklerobject *self, PyObject *args) {
    return do_append(self, PyList_Size(self->stack) - 1);
}


static int
load_appends(Unpicklerobject *self, PyObject *args) {
    return do_append(self, marker(self));
}


static int
do_setitems(Unpicklerobject *self, int  x) {
    PyObject *value = 0, *key = 0, *dict = 0;
    int len, i, res = -1;

    if ((len = PyList_Size(self->stack)) < 0)  
        goto finally;

    UNLESS(dict = PyList_GetItem(self->stack, x - 1))
        goto finally;

    for (i = x; i < len; i += 2) {
        UNLESS(key = PyList_GetItem(self->stack, i))  
            goto finally;

        UNLESS(value = PyList_GetItem(self->stack, i + 1))
            goto finally;

        if (PyObject_SetItem(dict, key, value) < 0)  
            goto finally;
    }

    if (DEL_LIST_SLICE(self->stack, x, len) < 0)  
        goto finally;

    res = 0;

finally:

    return res;
}


static int
load_setitem(Unpicklerobject *self, PyObject *args) {
    return do_setitems(self, PyList_Size(self->stack) - 2);
}


static int
load_setitems(Unpicklerobject *self, PyObject *args) {
    return do_setitems(self, marker(self));
}


static int
load_build(Unpicklerobject *self, PyObject *args) {
    PyObject *value = 0, *inst = 0, *instdict = 0, *d_key = 0, *d_value = 0, 
             *junk = 0;
    static PyObject *py_string__dict__ = 0;
    int len, i, res = -1;

    UNLESS(py_string__dict__)
        UNLESS(py_string__dict__ = PyString_FromString("__dict__"))
            goto finally;

    if ((len = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(value = PyList_GetItem(self->stack, len - 1))
        goto finally; 
    Py_INCREF(value);

    if (DEL_LIST_SLICE(self->stack, len - 1, len) < 0)
        goto finally;

    UNLESS(inst = PyList_GetItem(self->stack, len - 2))
        goto finally;

    UNLESS(PyObject_HasAttrString(inst, "__setstate__")) {
        UNLESS(instdict = PyObject_GetAttr(inst, py_string__dict__))
            goto finally;

        i = 0;
        while (PyDict_Next(value, &i, &d_key, &d_value)) {
            if (PyObject_SetItem(instdict, d_key, d_value) < 0)
                goto finally;
        }
    }
    else {
        UNLESS(junk = PyObject_CallMethod(inst, "__setstate__", "O", value))
            goto finally;
        Py_DECREF(junk);
    }

    res = 0;

finally:
  Py_XDECREF(value);
  Py_XDECREF(instdict);
  
  return res;
}


static int
load_mark(Unpicklerobject *self, PyObject *args) {
    int len;
  
    if ((len = PyList_Size(self->stack)) < 0)
        return -1;

    if (!self->num_marks) {
        UNLESS(self->marks = (int *)malloc(20 * sizeof(int))) {
            PyErr_NoMemory();
            return -1;
        }
 
        self->marks_size = 20;
    }
    else if ((self->num_marks + 1) > self->marks_size) {
        UNLESS(self->marks = (int *)realloc(self->marks,
            (self->marks_size + 20) * sizeof(int))) {
            PyErr_NoMemory();
            return -1;
        }

        self->marks_size += 20;
    }

    self->marks[self->num_marks++] = len;

    return 0;
}


static int
load_reduce(Unpicklerobject *self, PyObject *args) {
    PyObject *callable = 0, *arg_tup = 0, *ob = 0, *safe = 0;
    int len, has_key, res = -1;

    if ((len = PyList_Size(self->stack)) < 0)
        goto finally;

    UNLESS(arg_tup = PyList_GetItem(self->stack, len - 1))
        goto finally;

    UNLESS(callable = PyList_GetItem(self->stack, len - 2))
        goto finally;

    if (!PyClass_Check(callable)) {
        if ((has_key = PyMapping_HasKey(safe_constructors, callable)) < 0)
            goto finally;

        if (!has_key) {
            if (!(safe = PyObject_GetAttrString(callable, 
                "__safe_for_unpickling__")) || !PyObject_IsTrue(safe)) {
                PyErr_Format(UnpicklingError, "%s is not safe for unpickling", 
                    "O", callable);
                goto finally;
	    }
        }
    }

    UNLESS(ob = PyObject_CallObject(callable, arg_tup))
        goto finally;

    if (PyList_Append(self->stack, ob) < 0)
        goto finally;

    if (DEL_LIST_SLICE(self->stack, len - 2, len) < 0)
        goto finally;

    res = 0;

finally:
    Py_XDECREF(callable);
    Py_XDECREF(arg_tup);
    Py_XDECREF(ob);
    Py_XDECREF(safe);

    return res;
}
    

static PyObject *
Unpickler_load(Unpicklerobject *self, PyObject *args) {
    PyObject *stack = 0, *err = 0, *exc = 0, *val = 0, *tb = 0;
    int len;
    char *s;

    UNLESS(stack = PyList_New(0))
        goto err;

    self->stack = stack;
    self->num_marks = 0;

    while (1) {
        if ((*self->read_func)(self, &s, 1) < 0)
            break;

        switch (s[0]) {
            case NONE:
                if (load_none(self, NULL) < 0)
                    break;
                continue;

            case BININT:
                 if (load_binint(self, NULL) < 0)
                     break;
                 continue;

            case BININT1:
                if (load_binint1(self, NULL) < 0)
                    break;
                continue;

            case BININT2:
                if (load_binint2(self, NULL) < 0)
                    break;
                continue;

            case INT:
                if (load_int(self, NULL) < 0)
                    break;
                continue;

            case BININT8:
                if (load_binint8(self, NULL) < 0)
                    break;
                continue;

            case LONG:
                if (load_long(self, NULL) < 0)
                    break;
                continue;

            case FLOAT:
                if (load_float(self, NULL) < 0)
                    break;
                continue;

            case BINSTRING:
                if (load_binstring(self, NULL) < 0)
                    break;
                continue;

            case SHORT_BINSTRING:
                if (load_short_binstring(self, NULL) < 0)
                    break;
                continue;

            case STRING:
                if (load_string(self, NULL) < 0)
                    break;
                continue;

            case TUPLE:
                if (load_tuple(self, NULL) < 0)
                    break;
                continue;

            case LIST:
                if (load_list(self, NULL) < 0)
                    break;
                continue;

            case DICT:
                if (load_dict(self, NULL) < 0)
                    break;
                continue;

            case OBJ:
                if (load_obj(self, NULL) < 0)
                    break;
                continue;

            case INST:
                if (load_inst(self, NULL) < 0)
                    break;
                continue;

            case GLOBAL:
                if (load_global(self, NULL) < 0)
                    break;
                continue;

            case APPEND:
                if (load_append(self, NULL) < 0)
                    break;
                continue;

            case APPENDS:
                if (load_appends(self, NULL) < 0)
                    break;
                continue;
   
            case BUILD:
                if (load_build(self, NULL) < 0)
                    break;
                continue;
  
            case DUP:
                if (load_dup(self, NULL) < 0)
                    break;
                continue;

            case BINGET:
                if (load_binget(self, NULL) < 0)
                    break;
                continue;

            case LONG_BINGET:
                if (load_long_binget(self, NULL) < 0)
                    break;
                continue;
         
            case GET:
                if (load_get(self, NULL) < 0)
                    break;
                continue;

            case MARK:
                if (load_mark(self, NULL) < 0)
                    break;
                continue;

            case BINPUT:
                if (load_binput(self, NULL) < 0)
                    break;
                continue;

            case LONG_BINPUT:
                if (load_long_binput(self, NULL) < 0)
                    break;
                continue;
         
            case PUT:
                if (load_put(self, NULL) < 0)
                    break;
                continue;

            case POP:
                if (load_pop(self, NULL) < 0)
                    break;
                continue;

            case SETITEM:
                if (load_setitem(self, NULL) < 0)
                    break;
                continue;

            case SETITEMS:
                if (load_setitems(self, NULL) < 0)
                    break;
                continue;

            case STOP:
                break;

            case PERSID:
                if (load_persid(self, NULL) < 0)
                    break;
                continue;

            case BINPERSID:
                if (load_binpersid(self, NULL) < 0)
                    break;
                continue;

            case REDUCE:
                if (load_reduce(self, NULL) < 0)
                    break;
                continue;

            default: 
                PyErr_Format(UnpicklingError, "invalid load key, '%s'.", 
                    "c", self->buf[0]);
                return NULL;
        }

        break;
    }

    if (self->diddled_ptr) {
        *self->diddled_ptr = self->diddled_char;
        self->diddled_ptr = NULL;
    }

    if ((err = PyErr_Occurred()) == PyExc_EOFError) {
        PyErr_SetNone(PyExc_EOFError);
        return NULL;
    }    

    if (err)    
        return NULL;

    if ((len = PyList_Size(self->stack)) < 0)  
        return NULL;

    UNLESS(val = PyList_GetItem(self->stack, len - 1))  
        return NULL;
    Py_INCREF(val);

    if (DEL_LIST_SLICE(self->stack, len - 1, len) < 0) {
        Py_DECREF(val);
        return NULL;
    }

    return val;

err:
    Py_XDECREF(stack);

    return NULL;
}


static struct PyMethodDef Unpickler_methods[] = {
  {"load",         (PyCFunction)Unpickler_load,   0, ""},
  {NULL,              NULL}           /* sentinel */
};


static Unpicklerobject *
newUnpicklerobject(PyObject *f) {
    Unpicklerobject *self;
    PyObject *memo = 0;
        
    UNLESS(memo = PyDict_New())
        goto err;

    UNLESS(self = PyObject_NEW(Unpicklerobject, &Unpicklertype))
        goto err;

    if (PyFile_Check(f)) {
        self->fp = PyFile_AsFile(f);
        self->read_func = read_file;
        self->readline_func = readline_file;
        self->read = NULL;
        self->readline = NULL;
    }
    else if (PycStringIO_InputCheck(f)) {
        self->fp = NULL;
        self->read_func = read_cStringIO;
        self->readline_func = readline_cStringIO;
        self->read = NULL;
        self->readline = NULL;
    }
    else {
        PyObject *readline, *read;
        static PyObject *read_str = 0, *readline_str = 0;

        self->fp = NULL;
        self->read_func = read_other;
        self->readline_func = readline_other;

        UNLESS(readline_str)
            UNLESS(readline_str = PyString_FromString("readline"))
                goto err;

        UNLESS(readline = PyObject_GetAttr(f, readline_str))
            goto err;

        UNLESS(read_str)
            UNLESS(read_str = PyString_FromString("read"))
                goto err;

        UNLESS(read = PyObject_GetAttr(f, read_str)) {
            Py_DECREF(readline);
            goto err;
        }
  
        self->read = read; 
        self->readline = readline;

        self->diddled_ptr = NULL;
        self->diddled_char = '\0';
    }

    Py_INCREF(f);
  
    self->file = f;
    self->memo   = memo;
    self->arg    = NULL;
    self->stack  = NULL;
    self->pers_func = NULL;
    self->last_string = NULL;
    self->marks = NULL;
    self->num_marks = 0;
    self->marks_size = 0;
    self->buf_size = 0;

    return self;

err:
    Py_XDECREF(memo);
    Py_XDECREF((PyObject *)self);

    return NULL;
}


static PyObject *
get_Unpickler(PyObject *self, PyObject *args) {
    PyObject *file;
  
    UNLESS(PyArg_Parse(args, "O", &file))
        return NULL;
    return (PyObject *)newUnpicklerobject(file);
}


static void
Unpickler_dealloc(Unpicklerobject *self) {
    Py_XDECREF(self->readline);
    Py_XDECREF(self->read);
    Py_XDECREF(self->file);
    Py_XDECREF(self->memo);
    Py_XDECREF(self->stack);
    Py_XDECREF(self->pers_func);
    Py_XDECREF(self->arg);
    Py_XDECREF(self->last_string);

    if (self->marks) {
        free(self->marks);
    }

    if (self->buf_size) {
        free(self->buf);
    }
    
    PyMem_DEL(self);
}


static PyObject *
Unpickler_getattr(Unpicklerobject *self, char *name) {
    if (!strcmp(name, "persistent_load")) {
        if (!self->pers_func) {
            PyErr_SetString(PyExc_AttributeError, name);
            return NULL;
        }

        Py_INCREF(self->pers_func);
        return self->pers_func;
    }

    if (!strcmp(name, "memo")) {
        if (!self->memo) {
            PyErr_SetString(PyExc_AttributeError, name);
            return NULL;
        }

        Py_INCREF(self->memo);
        return self->memo;
    }

    if (!strcmp(name, "UnpicklingError")) {
        Py_INCREF(UnpicklingError);
        return UnpicklingError;
    }

    return Py_FindMethod(Unpickler_methods, (PyObject *)self, name);
}


static int
Unpickler_setattr(Unpicklerobject *self, char *name, PyObject *value) {
    if (!strcmp(name, "persistent_load")) {
        Py_XDECREF(self->pers_func);
        self->pers_func = value;
        Py_INCREF(value);
        return 0;
    }

    PyErr_SetString(PyExc_AttributeError, name);
    return -1;
}


static PyObject *
dump(PyObject *self, PyObject *args) {
    PyObject *ob, *file, *res = NULL;
    Picklerobject *pickler = 0;
    int bin = 0;

    UNLESS(PyArg_ParseTuple(args, "OO|i", &ob, &file, &bin))
        goto finally;

    UNLESS(pickler = newPicklerobject(file, bin))
        goto finally;

    res = Pickler_dump(pickler, ob);

finally:
    Py_XDECREF(pickler);

    return res;
}


static PyObject *
dumps(PyObject *self, PyObject *args) {
    PyObject *ob, *file = 0, *res = NULL;
    Picklerobject *pickler = 0;
    int bin = 0;

    UNLESS(PyArg_ParseTuple(args, "O|i", &ob, &bin))
        goto finally;

    UNLESS(file = PycStringIO->NewOutput(128))
        goto finally;

    UNLESS(pickler = newPicklerobject(file, bin))
        goto finally;

    UNLESS(Pickler_dump(pickler, ob))
        goto finally;

    res = PycStringIO->cgetvalue(file);

finally:
    Py_XDECREF(pickler);
    Py_XDECREF(file);

    return res;
}  
  

static PyObject *
cpm_load(PyObject *self, PyObject *args) {
    Unpicklerobject *unpickler = 0;
    PyObject *res = NULL;

    UNLESS(PyArg_Parse(args, "O", &args))
        goto finally;

    UNLESS(unpickler = newUnpicklerobject(args))
        goto finally;

    res = Unpickler_load(unpickler, NULL);

finally:
    Py_XDECREF(unpickler);

    return res;
}


static PyObject *
loads(PyObject *self, PyObject *args) {
    PyObject *file = 0, *res = NULL;
    Unpicklerobject *unpickler = 0;

    UNLESS(PyArg_Parse(args, "O", &args))
        goto finally;

    UNLESS(file = PycStringIO->NewInput(args))
        goto finally;
  
    UNLESS(unpickler = newUnpicklerobject(file))
        goto finally;

    res = Unpickler_load(unpickler, NULL);

finally:
    Py_XDECREF(file);
    Py_XDECREF(unpickler);

    return res;
}


static char Unpicklertype__doc__[] = "";

static PyTypeObject Unpicklertype = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,                            /*ob_size*/
    "Unpickler",                  /*tp_name*/
    sizeof(Unpicklerobject),              /*tp_basicsize*/
    0,                            /*tp_itemsize*/
    /* methods */
    (destructor)Unpickler_dealloc,        /*tp_dealloc*/
    (printfunc)0,         /*tp_print*/
    (getattrfunc)Unpickler_getattr,       /*tp_getattr*/
    (setattrfunc)Unpickler_setattr,       /*tp_setattr*/
    (cmpfunc)0,           /*tp_compare*/
    (reprfunc)0,          /*tp_repr*/
    0,                    /*tp_as_number*/
    0,            /*tp_as_sequence*/
    0,            /*tp_as_mapping*/
    (hashfunc)0,          /*tp_hash*/
    (ternaryfunc)0,               /*tp_call*/
    (reprfunc)0,          /*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Unpicklertype__doc__ /* Documentation string */
};


static struct PyMethodDef cPickle_methods[] = {
  {"dump",         (PyCFunction)dump,             1, ""},
  {"dumps",        (PyCFunction)dumps,            1, ""},
  {"load",         (PyCFunction)cpm_load,         0, ""},
  {"loads",        (PyCFunction)loads,            0, ""},
  {"Pickler",      (PyCFunction)get_Pickler,      1, ""},
  {"Unpickler",    (PyCFunction)get_Unpickler,    0, ""},
  { NULL, NULL }
};


#define CHECK_FOR_ERRORS(MESS) \
if(PyErr_Occurred()) { \
    PyObject *__sys_exc_type, *__sys_exc_value, *__sys_exc_traceback; \
    PyErr_Fetch( &__sys_exc_type, &__sys_exc_value, &__sys_exc_traceback); \
    fprintf(stderr, # MESS ":\n\t"); \
    PyObject_Print(__sys_exc_type, stderr,0); \
    fprintf(stderr,", "); \
    PyObject_Print(__sys_exc_value, stderr,0); \
    fprintf(stderr,"\n"); \
    fflush(stderr); \
    Py_FatalError(# MESS); \
}


static int
init_stuff(PyObject *module, PyObject *module_dict) {
    PyObject *string, *copy_reg;

    UNLESS(builtins = PyImport_ImportModule("__builtin__"))
        return -1;

    UNLESS(copy_reg = PyImport_ImportModule("copy_reg"))
        return -1;

    UNLESS(dispatch_table = PyObject_GetAttrString(copy_reg, 
        "dispatch_table"))
        return -1;

    UNLESS(safe_constructors = PyObject_GetAttrString(copy_reg, 
        "safe_constructors"))
        return -1;

    Py_DECREF(copy_reg);

    UNLESS(string = PyImport_ImportModule("string"))
        return -1;

    UNLESS(atol_func = PyObject_GetAttrString(string, "atol"))
        return -1;

    Py_DECREF(string);

    UNLESS(empty_tuple = PyTuple_New(0))
        return -1;

    UNLESS(class_map = PyDict_New())
        return -1;

    UNLESS(PicklingError = PyString_FromString("cPickle.PicklingError"))
        return -1;

    if (PyDict_SetItemString(module_dict, "PicklingError", 
        PicklingError) < 0)
        return -1;

    UNLESS(UnpicklingError = PyString_FromString("cPickle.UnpicklingError"))
        return -1;

    if (PyDict_SetItemString(module_dict, "UnpicklingError",
        UnpicklingError) < 0)
        return -1;

    PycString_IMPORT;
 
    return 0;
}


/* Initialization function for the module (*must* be called initcPickle) */
void
initcPickle() {
    PyObject *m, *d;

    /* Create the module and add the functions */
    m = Py_InitModule4("cPickle", cPickle_methods,
                     cPickle_module_documentation,
                     (PyObject*)NULL,PYTHON_API_VERSION);

    /* Add some symbolic constants to the module */
    d = PyModule_GetDict(m);
    ErrorObject = PyString_FromString("cPickle.error");
    PyDict_SetItemString(d, "error", ErrorObject);

    init_stuff(m, d);
    CHECK_FOR_ERRORS("can't initialize module cPickle");
}
