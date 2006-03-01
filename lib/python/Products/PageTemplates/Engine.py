
# Common Engine for Zope3-ZPT-in-Zope-2


from zope.tales.tales import ExpressionEngine
from zope.tales.expressions import PathExpr, StringExpr, NotExpr, DeferExpr, SubPathExpr
from zope.tales.expressions import SimpleModuleImporter, _marker
from zope.tales.pythonexpr import PythonExpr
from zope.tales.tales import _valid_name, _parse_expr, NAME_RE, Undefined 


def BoboTraverseAwareSimpleTraverse(object, path_items, econtext):
    """ a slightly modified version of zope.tales.expressions.simpleTraverse()
        that interacts correctly with objects implementing bobo_traverse().
    """

    for name in path_items:
        next = getattr(object, name, _marker)
        if next is not _marker:
            object = next
        else:
            try:
                object = object.restrictedTraverse(name)
            except (KeyError, AttributeError):
                try:
                    object = object[name]
                except:
                    object = getattr(object, name)

    return object


class PathExpr(PathExpr):
    """We need to subclass PathExpr at this point since there is no other
       away to pass our own traverser because we do not instantiate 
       PathExpr on our own...this sucks!
    """

    def __init__(self, name, expr, engine, traverser=BoboTraverseAwareSimpleTraverse):
        self._s = expr
        self._name = name
        paths = expr.split('|')
        self._subexprs = []
        add = self._subexprs.append
        for i in range(len(paths)):
            path = paths[i].lstrip()
            if _parse_expr(path):
                # This part is the start of another expression type,
                # so glue it back together and compile it.
                add(engine.compile('|'.join(paths[i:]).lstrip()))
                break
            add(SubPathExpr(path, traverser, engine)._eval)


from zope.tales.tales import Context


from zope.i18n import translate

class Context(Context):


    def translate(self, msgid, domain=None, mapping=None, default=None):
        # fix that
        return msgid
#        return translate(msgid, domain, mapping,
#                         context=context, default=default)



class ExpressionEngine(ExpressionEngine):
    
    def getContext(self, contexts=None, **kwcontexts):
        if contexts is not None:
            if kwcontexts:
                kwcontexts.update(contexts)
            else:
                kwcontexts = contexts
        return Context(self, kwcontexts)


def Engine():
    e = ExpressionEngine()
    reg = e.registerType
    for pt in PathExpr._default_type_names:
        reg(pt, PathExpr)
    reg('string', StringExpr)
    reg('python', PythonExpr)
    reg('not', NotExpr)
    reg('defer', DeferExpr)
    e.registerBaseName('modules', SimpleModuleImporter())
    return e

Engine = Engine()

