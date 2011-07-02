##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Application support
"""

import os, sys
from logging import getLogger
from cgi import escape

import Products
import transaction
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permission import ApplicationDefaultPermissions
from Acquisition import aq_base
from App.ApplicationManager import ApplicationManager
from App.config import getConfiguration
from App import FactoryDispatcher
from DateTime import DateTime
from OFS.metaconfigure import get_packages_to_initialize
from OFS.metaconfigure import package_initialized
from OFS.userfolder import UserFolder
from Persistence import Persistent
from webdav.NullResource import NullResource
from zExceptions import Redirect as RedirectException, Forbidden

from zope.interface import implements

import Folder
import misc_
import ZDOM
from FindSupport import FindSupport
from interfaces import IApplication
from misc_ import Misc_

LOG = getLogger('Application')

APP_MANAGER = None


class Application(ApplicationDefaultPermissions,
                  ZDOM.Root,
                  Folder.Folder,
                  FindSupport,
                 ):
    """Top-level system object"""

    implements(IApplication)

    security = ClassSecurityInfo()

    title = 'Zope'
    __defined_roles__ = ('Manager','Anonymous','Owner')
    web__form__method = 'GET'
    isTopLevelPrincipiaApplicationObject = 1

    manage_options=((
            Folder.Folder.manage_options[0],
            Folder.Folder.manage_options[1],
            {'label': 'Control Panel', 'action': 'Control_Panel/manage_main'}, ) +
                    Folder.Folder.manage_options[2:]
                    )

    p_=misc_.p_
    misc_=misc_.misc_

    _reserved_names=('Control_Panel',
                     'browser_id_manager',
                     'temp_folder')

    # This class-default __allow_groups__ ensures that the
    # emergency user can still access the system if the top-level
    # UserFolder is deleted. This is necessary to allow people
    # to replace the top-level UserFolder object.

    __allow_groups__ = UserFolder()

    # Set the universal default method to index_html
    _object_manager_browser_default_id = 'index_html'

    _initializer_registry = None

    def __init__(self):
        # Initialize users
        uf = UserFolder()
        self.__allow_groups__ = uf
        self._setObject('acl_users', uf)

    def id(self):
        try:
            return self.REQUEST['SCRIPT_NAME'][1:]
        except:
            return self.title

    def title_and_id(self):
        return self.title

    def title_or_id(self):
        return self.title

    def __class_init__(self):
        InitializeClass(self)

    @property
    def Control_Panel(self):
        return APP_MANAGER.__of__(self)

    def PrincipiaRedirect(self, destination, URL1):
        """Utility function to allow user-controlled redirects"""
        if destination.find('//') >= 0:
            raise RedirectException, destination
        raise RedirectException, ("%s/%s" % (URL1, destination))

    Redirect = ZopeRedirect = PrincipiaRedirect

    def __bobo_traverse__(self, REQUEST, name=None):
        if name == 'Control_Panel':
            return APP_MANAGER.__of__(self)
        try:
            return getattr(self, name)
        except AttributeError:
            pass

        try:
            return self[name]
        except KeyError:
            pass

        method = REQUEST.get('REQUEST_METHOD', 'GET')
        if not method in ('GET', 'POST'):
            return NullResource(self, name, REQUEST).__of__(self)

        # Waaa. unrestrictedTraverse calls us with a fake REQUEST.
        # There is proabably a better fix for this.
        try:
            REQUEST.RESPONSE.notFoundError("%s\n%s" % (name, method))
        except AttributeError:
            raise KeyError, name

    def PrincipiaTime(self, *args):
        """Utility function to return current date/time"""
        return apply(DateTime, args)

    ZopeTime = PrincipiaTime

    security.declarePublic('ZopeAttributionButton')
    def ZopeAttributionButton(self):
        """Returns an HTML fragment that displays the 'powered by zope'
        button along with a link to the Zope site."""
        return '<a href="http://www.zope.org/Credits" target="_top"><img ' \
               'src="%s/p_/ZopeButton" width="115" height="50" border="0" ' \
               'alt="Powered by Zope" /></a>' % escape(self.REQUEST.BASE1, 1)


    def DELETE(self, REQUEST, RESPONSE):
        """Delete a resource object."""
        self.dav__init(REQUEST, RESPONSE)
        raise Forbidden, 'This resource cannot be deleted.'

    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location."""
        self.dav__init(REQUEST, RESPONSE)
        raise Forbidden, 'This resource cannot be moved.'

    test_url___allow_groups__=None
    test_url = ZopeAttributionButton

    def absolute_url(self, relative=0):
        """The absolute URL of the root object is BASE1 or "/".
        """
        if relative: return ''
        try:
            # Take advantage of computed URL cache
            return self.REQUEST['BASE1']
        except (AttributeError, KeyError):
            return '/'

    def absolute_url_path(self):
        """The absolute URL path of the root object is BASEPATH1 or "/".
        """
        try:
            return self.REQUEST['BASEPATH1'] or '/'
        except (AttributeError, KeyError):
            return '/'

    def virtual_url_path(self):
        """The virtual URL path of the root object is empty.
        """
        return ''

    def getPhysicalRoot(self):
        return self

    def getPhysicalPath(self):
        """Get the physical path of the object.

        Returns a path (an immutable sequence of strings) that can be used to
        access this object again later, for example in a copy/paste operation.
        getPhysicalRoot() and getPhysicalPath() are designed to operate
        together.
        """
        # We're at the base of the path.
        return ('',)

    security.declarePrivate('_setInitializerFlag')
    def _setInitializerFlag(self, flag):
        if self._initializer_registry is None:
            self._initializer_registry = {}
        self._initializer_registry[flag] = 1

    security.declarePrivate('_getInitializerFlag')
    def _getInitializerFlag(self, flag):
        reg = self._initializer_registry
        if reg is None:
            reg = {}
        return reg.get(flag)

InitializeClass(Application)


class Expired(Persistent):

    icon='p_/broken'

    def __setstate__(self, s={}):
        dict=self.__dict__
        if s.has_key('id'):
            dict['id']=s['id']
        elif s.has_key('__name__'):
            dict['id']=s['__name__']
        else: dict['id']='Unknown'
        dict['title']='** Expired **'

    def __save__(self):
        pass

    __inform_commit__=__save__

def initialize(app):
    initializer = AppInitializer(app)
    initializer.initialize()


class AppInitializer:
    """ Initialze an Application object (called at startup) """

    def __init__(self, app):
        self.app = (app,)

    def getApp(self):
        # this is probably necessary, but avoid acquisition anyway
        return self.app[0]

    def commit(self, note):
        transaction.get().note(note)
        transaction.commit()

    def initialize(self):
        # make sure to preserve relative ordering of calls below.
        self.install_cp_and_products()
        self.install_tempfolder_and_sdc()
        self.install_session_data_manager()
        self.install_browser_id_manager()
        self.install_required_roles()
        self.install_inituser()
        self.install_errorlog()
        self.install_products()
        self.install_standards()
        self.install_virtual_hosting()

    def install_cp_and_products(self):
        global APP_MANAGER
        APP_MANAGER = ApplicationManager()
        APP_MANAGER._init()

        app = self.getApp()
        app._p_activate()

        # Remove Control Panel.
        if 'Control_Panel' in app.__dict__.keys():
            del app.__dict__['Control_Panel']
            app._objects = tuple(i for i in app._objects if i['id'] != 'Control_Panel')
            self.commit('Removed persistent Control_Panel')

    def install_tempfolder_and_sdc(self):
        app = self.getApp()
        from Products.ZODBMountPoint.MountedObject import manage_addMounts,\
             MountedObject
        from Products.ZODBMountPoint.MountedObject import getConfiguration as \
             getDBTabConfiguration

        dbtab_config = getDBTabConfiguration()

        tf = getattr(app, 'temp_folder', None)

        if getattr(tf, 'meta_type', None) == MountedObject.meta_type:
            # tf is a MountPoint object.  This means that the temp_folder
            # couldn't be mounted properly (the meta_type would have been
            # the meta type of the container class otherwise).  The
            # MountPoint object writes a message to zLOG so we don't
            # need to.
            return

        if tf is None:
            # do nothing if we've already installed one
            if not app._getInitializerFlag('temp_folder'):
                if dbtab_config is None:
                    # DefaultConfiguration, do nothing
                    return
                mount_paths = [ x[0] for x in dbtab_config.listMountPaths() ]
                if not '/temp_folder' in mount_paths:
                    # we won't be able to create the mount point properly
                    LOG.error('Could not initialze a Temporary Folder because '
                              'a database was not configured to be mounted at '
                              'the /temp_folder mount point')
                    return
                try:
                    manage_addMounts(app, ('/temp_folder',))
                    app._setInitializerFlag('temp_folder')
                    self.commit('Added temp_folder')
                    tf = app.temp_folder
                except:
                    LOG.error('Could not add a /temp_folder mount point due to an '
                              'error.', exc_info=sys.exc_info())
                    return

        # Ensure that there is a transient object container in the temp folder
        config = getConfiguration()

        if not hasattr(aq_base(tf), 'session_data'):
            from Products.Transience.Transience import TransientObjectContainer
            addnotify = getattr(config, 'session_add_notify_script_path', None)
            delnotify = getattr(config, 'session_delete_notify_script_path',
                                None)
            default_limit = 1000
            default_period_secs = 20
            default_timeout_mins = 20

            limit = getattr(config, 'maximum_number_of_session_objects',
                            default_limit)
            timeout_spec = getattr(config, 'session_timeout_minutes',
                                   default_timeout_mins)
            period_spec = getattr(config, 'session_resolution_seconds',
                                  default_period_secs)

            if addnotify and app.unrestrictedTraverse(addnotify, None) is None:
                LOG.warn('failed to use nonexistent "%s" script as '
                         'session-add-notify-script-path' % addnotify)
                addnotify=None

            if delnotify and app.unrestrictedTraverse(delnotify, None) is None:
                LOG.warn('failed to use nonexistent "%s" script as '
                         'session-delete-notify-script-path' % delnotify)
                delnotify=None

            if 1:  # Preserve indentation for diff
                toc = TransientObjectContainer('session_data',
                                               'Session Data Container',
                                               timeout_mins = timeout_spec,
                                               addNotification = addnotify,
                                               delNotification = delnotify,
                                               limit=limit,
                                               period_secs = period_spec)

            tf._setObject('session_data', toc)
            tf_reserved = getattr(tf, '_reserved_names', ())
            if 'session_data' not in tf_reserved:
                tf._reserved_names = tf_reserved + ('session_data',)
            self.commit('Added session_data to temp_folder')
            return tf # return the tempfolder object for test purposes

    def install_browser_id_manager(self):
        app = self.getApp()
        if app._getInitializerFlag('browser_id_manager'):
            # do nothing if we've already installed one
            return
        # Ensure that a browser ID manager exists
        if not hasattr(app, 'browser_id_manager'):
            from Products.Sessions.BrowserIdManager import BrowserIdManager
            bid = BrowserIdManager('browser_id_manager', 'Browser Id Manager')
            app._setObject('browser_id_manager', bid)
            # FIXME explicitely call manage_afterAdd, as sometimes
            # events are initialized too late
            browser_id_manager = app.browser_id_manager
            browser_id_manager.manage_afterAdd(browser_id_manager, app)
            app._setInitializerFlag('browser_id_manager')
            self.commit('Added browser_id_manager')

    def install_session_data_manager(self):
        app = self.getApp()
        if app._getInitializerFlag('session_data_manager'):
            # do nothing if we've already installed one
            return
        # Ensure that a session data manager exists
        if not hasattr(app, 'session_data_manager'):
            from Products.Sessions.SessionDataManager import SessionDataManager
            sdm = SessionDataManager('session_data_manager',
                title='Session Data Manager',
                path='/temp_folder/session_data',
                requestName='SESSION')
            app._setObject('session_data_manager', sdm)
            # FIXME explicitely call manage_afterAdd, as sometimes
            # events are initialized too late
            session_data_manager = app.session_data_manager
            session_data_manager.manage_afterAdd(session_data_manager, app)
            app._setInitializerFlag('session_data_manager')
            self.commit('Added session_data_manager')

    def install_required_roles(self):
        app = self.getApp()

        # Ensure that Owner role exists.
        if hasattr(app, '__ac_roles__') and not ('Owner' in app.__ac_roles__):
            app.__ac_roles__=app.__ac_roles__ + ('Owner',)
            self.commit('Added Owner role')

        # ensure the Authenticated role exists.
        if hasattr(app, '__ac_roles__'):
            if not 'Authenticated' in app.__ac_roles__:
                app.__ac_roles__=app.__ac_roles__ + ('Authenticated',)
                self.commit('Added Authenticated role')

    def install_inituser(self):
        app = self.getApp()
        # Install the initial user.
        if hasattr(app, 'acl_users'):
            users = app.acl_users
            if hasattr(users, '_createInitialUser'):
                app.acl_users._createInitialUser()
                self.commit('Created initial user')
            users = aq_base(users)
            migrated = getattr(users, '_ofs_migrated', False)
            if not migrated:
                klass = users.__class__
                from OFS.userfolder import UserFolder
                if klass is UserFolder:
                    # zope.deferredimport does a thourough job, so the class
                    # looks like it's from the new location already. And we
                    # don't want to migrate any custom user folders here.
                    users.__class__ = UserFolder
                    users._ofs_migrated = True
                    users._p_changed = True
                    app._p_changed = True
                    transaction.get().note('Migrated user folder')
                    transaction.commit()

    def install_errorlog(self):
        app = self.getApp()
        if app._getInitializerFlag('error_log'):
            # do nothing if we've already installed one
            return

        # Install an error_log
        if not hasattr(app, 'error_log'):
            from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
            error_log = SiteErrorLog()
            app._setObject('error_log', error_log)
            # FIXME explicitely call manage_afterAdd, as sometimes
            # events are initialized too late
            error_log = app.error_log
            error_log.manage_afterAdd(error_log, app)
            app._setInitializerFlag('error_log')
            self.commit('Added site error_log at /error_log')

    def install_virtual_hosting(self):
        app = self.getApp()
        if app._getInitializerFlag('virtual_hosting'):
            return
        if (not app.objectIds('Virtual Host Monster') and
            not hasattr(app, 'virtual_hosting')):
            from Products.SiteAccess.VirtualHostMonster \
                import VirtualHostMonster
            vhm = VirtualHostMonster()
            vhm.id = 'virtual_hosting'
            vhm.addToContainer(app)
            app._setInitializerFlag('virtual_hosting')
            self.commit('Added virtual_hosting')

    def install_products(self):
        return install_products()

    def install_standards(self):
        app = self.getApp()
        # this defers to a  function for b/c reasons
        return install_standards(app)

def install_products(app=None):
    folder_permissions = get_folder_permissions()
    meta_types = []
    done = {}
    for priority, product_name, index, product_dir in get_products():
        # For each product, we will import it and try to call the
        # intialize() method in the product __init__ module. If
        # the method doesnt exist, we put the old-style information
        # together and do a default initialization.
        if product_name in done:
            continue
        done[product_name] = 1
        install_product(app, product_dir, product_name, meta_types,
                        folder_permissions)

    # Delayed install of packages-as-products
    for module, init_func in tuple(get_packages_to_initialize()):
        install_package(app, module, init_func)

    Products.meta_types = Products.meta_types + tuple(meta_types)
    InitializeClass(Folder.Folder)

def get_products():
    """ Return a list of tuples in the form:
    [(priority, dir_name, index, base_dir), ...] for each Product directory
    found, sort before returning """
    products = []
    i = 0
    for product_dir in Products.__path__:
        product_names=os.listdir(product_dir)
        for name in product_names:
            fullpath = os.path.join(product_dir, name)
            # Products must be directories
            if os.path.isdir(fullpath):
                # Products must be directories with an __init__.py[co]
                if ( os.path.exists(os.path.join(fullpath, '__init__.py')) or
                     os.path.exists(os.path.join(fullpath, '__init__.pyo')) or
                     os.path.exists(os.path.join(fullpath, '__init__.pyc')) ):
                    # i is used as sort ordering in case a conflict exists
                    # between Product names.  Products will be found as
                    # per the ordering of Products.__path__
                    products.append((0, name, i, product_dir))
        i = i + 1
    products.sort()
    return products


def import_products():
    done = {}
    for priority, product_name, index, product_dir in get_products():
        if product_name in done:
            LOG.warn('Duplicate Product name: '
                     'After loading Product %s from %s, '
                     'I skipped the one in %s.' % (
                    `product_name`, `done[product_name]`, `product_dir`) )
            continue
        done[product_name] = product_dir
        import_product(product_dir, product_name)
    return done.keys()


def import_product(product_dir, product_name, raise_exc=None):
    path_join=os.path.join
    isdir=os.path.isdir
    exists=os.path.exists
    global_dict=globals()
    modules=sys.modules

    package_dir = path_join(product_dir, product_name)
    if not isdir(package_dir):
        return

    if not exists(path_join(package_dir, '__init__.py')):
        if not exists(path_join(package_dir, '__init__.pyc')):
            if not exists(path_join(package_dir, '__init__.pyo')):
                return

    pname = "Products.%s" % product_name
    product = __import__(pname, global_dict, global_dict, ('__doc__', ))
    if hasattr(product, '__module_aliases__'):
        for k, v in product.__module_aliases__:
            if k not in modules:
                if isinstance(v, str) and v in modules:
                    v = modules[v]
                modules[k] = v


def get_folder_permissions():
    folder_permissions={}
    for p in Folder.Folder.__ac_permissions__:
        permission, names = p[:2]
        folder_permissions[permission]=names
    return folder_permissions


def install_product(app, product_dir, product_name, meta_types,
                    folder_permissions, raise_exc=None):

    from App.ProductContext import ProductContext
    path_join=os.path.join
    isdir=os.path.isdir
    exists=os.path.exists
    global_dict=globals()

    package_dir=path_join(product_dir, product_name)
    __traceback_info__=product_name
    if not isdir(package_dir): return
    if not exists(path_join(package_dir, '__init__.py')):
        if not exists(path_join(package_dir, '__init__.pyc')):
            if not exists(path_join(package_dir, '__init__.pyo')):
                return

    product=__import__("Products.%s" % product_name,
                       global_dict, global_dict, ('__doc__', ))

    # Install items into the misc_ namespace, used by products
    # and the framework itself to store common static resources
    # like icon images.
    misc_ = pgetattr(product, 'misc_', {})
    if misc_:
        if isinstance(misc_, dict):
            misc_=Misc_(product_name, misc_)
        Application.misc_.__dict__[product_name]=misc_

    productObject = FactoryDispatcher.Product(product_name)
    context = ProductContext(productObject, None, product)

    # Look for an 'initialize' method in the product.
    initmethod = pgetattr(product, 'initialize', None)
    if initmethod is not None:
        initmethod(context)


def install_package(app, module, init_func, raise_exc=None):
    """Installs a Python package like a product."""
    from App.ProductContext import ProductContext
    name = module.__name__
    product = FactoryDispatcher.Product(name)
    product.package_name = name

    if init_func is not None:
        newContext = ProductContext(product, None, module)
        init_func(newContext)

    package_initialized(module, init_func)


def install_standards(app):
    # Check to see if we've already done this before
    if getattr(app, '_standard_objects_have_been_added', 0):
        return

    # Install the replaceable standard objects
    from App.Common import package_home
    from App.special_dtml import DTMLFile
    from Products.PageTemplates.PageTemplateFile import PageTemplateFile

    std_dir = os.path.join(package_home(globals()), 'standard')
    wrote = False
    for fn in os.listdir(std_dir):
        base, ext = os.path.splitext(fn)
        if ext == '.dtml':
            if hasattr(app, base):
                continue
            ob = DTMLFile(base, std_dir)
            app.manage_addProduct['OFSP'].manage_addDTMLMethod(
                id=base, file=open(ob.raw))
        elif ext in ('.pt', '.zpt'):
            if hasattr(app, base):
                continue
            ob = PageTemplateFile(fn, std_dir, __name__=fn)
            app.manage_addProduct['PageTemplates'].manage_addPageTemplate(
                id=base, title='', text=open(ob.filename))
        elif ext in ('.ico', '.gif', '.png'):
            if hasattr(app, fn):
                continue
            app.manage_addProduct['OFSP'].manage_addImage(
                id=fn, title='', file=open(os.path.join(std_dir, fn)))
        else:
            continue
        wrote = True
    if wrote:
        app._standard_objects_have_been_added = 1
        transaction.get().note('Installed standard objects')
        transaction.commit()


def pgetattr(product, name, default=install_products, __init__=0):
    if not __init__ and hasattr(product, name):
        return getattr(product, name)
    if hasattr(product, '__init__'):
        product=product.__init__
        if hasattr(product, name):
            return getattr(product, name)

    if default is not install_products:
        return default

    raise AttributeError(name)
