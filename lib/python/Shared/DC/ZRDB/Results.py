
from string import strip, lower, upper
from Acquisition import Implicit
from Record import Record

record_classes={}

class NoBrains: pass

class Results:
    """Class for providing a nice interface to DBI result data
    """
    _index=None

    def __init__(self,(items,data),brains=NoBrains, parent=None):

        self._data=data
        self.__items__=items
	self._parent=parent
        self._names=names=[]
	self._schema=schema={}
        self._data_dictionary=dd={}
        i=0
        for item in items:
            name=item['name']
	    name=strip(name)
	    if not name:
		raise ValueError, 'Empty column name, %s' % name
	    if schema.has_key(name):
		raise ValueError, 'Duplicate column name, %s' % name
	    schema[name]=i
	    schema[lower(name)]=i
	    schema[upper(name)]=i
            dd[name]=item
            names.append(name)
	    i=i+1

	self._nv=nv=len(names)
	
	# Create a record class to hold the records.
	names=tuple(names)
	if record_classes.has_key((names,brains)):
	    r=record_classes[names,brains]
	else:
	    class r(Record, Implicit, brains):
		'Result record class'		    

	    r.__record_schema__=schema
	    for k in filter(lambda k: k[:2]=='__', Record.__dict__.keys()):
		setattr(r,k,getattr(Record,k))
		record_classes[names,brains]=r

	    if hasattr(brains, '__init__'):
		binit=brains.__init__
		if hasattr(binit,'im_func'): binit=binit.im_func
		def __init__(self, data, parent, binit=binit):
		    Record.__init__(self,data)
		    binit(self.__of__(parent))

		r.__dict__['__init__']=__init__
		    

	self._class=r

	# OK, we've read meta data, now get line indexes

    def _searchable_result_columns(self): return self.__items__
    def names(self): return self._names
    def data_dictionary(self): return self._data_dictionary

    def __len__(self): return len(self._data)

    def __getitem__(self,index):
	if index==self._index: return self._row
	parent=self._parent
	fields=self._class(self._data[index], parent)
	self._index=index
	self._row=fields
	if parent is None: return fields
	return fields.__of__(parent)

