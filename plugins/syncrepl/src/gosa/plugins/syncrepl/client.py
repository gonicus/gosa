import ldap
import ldapurl
import os

import re
import zope
from syncrepl_client import Syncrepl, SyncreplMode
from syncrepl_client.callbacks import BaseCallback
from sys import stdout
from zope.interface import implementer

from gosa.backend.utils.ldap import LDAPHandler
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.event import EventMaker
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class SyncReplClient(Plugin):
    _priority_ = 21
    __client = None
    __url = None
    __tls = False

    def __init__(self):
        self.env = Environment.getInstance()

    def serve(self):

        get = self.env.config.get
        self.__url = ldapurl.LDAPUrl(get("ldap.url"))
        self.__url.who = get('ldap.bind-dn', default=None)
        self.__url.cred = get('ldap.bind-secret', default=None)
        self.__url.scope = ldap.SCOPE_SUBTREE
        if get("ldap.tls", default="True").lower() == "true" and ldap.TLS_AVAIL and self.__url.urlscheme != "ldaps":
            self.__tls = True

        path = self.env.config.get('ldap.syncrepl-data-path', default=os.path.join(os.path.sep, 'var', 'lib', 'gosa', 'syncrepl'))
        if not os.path.exists(path):
            os.makedirs(path)

        self.__client = Syncrepl(data_path=path,
                                 callback=ReplCallback(),
                                 ldap_url=self.__url,
                                 mode=SyncreplMode.REFRESH_AND_PERSIST)


class ReplCallback(BaseCallback):
    """
    :class:`~syncrepl_client.callbacks.LoggingCallback` is a callback class
    which logs each callback.  It is useful for debugging purposes, as the
    output is not meant to be machine-readable.
    Each callback will cause messages to be printed to the file set in
    :attr:`~syncrepl_client.callbacks.LoggingCallback.dest`.  For the
    :meth:`~syncrepl_client.callbacks.BaseCallback.bind_complete` callback, the
    bind DN is printed.  For callbacks containing DNs, the DNs are printed.
    For callbacks containing attribute dictionaries, each dictionary's contents
    are printed.
    For a list of callbacks, and what they mean, see
    :class:`~syncrepl_client.callbacks.BaseCallback`.
    """

    dest = stdout
    """The log destination.
    This can be anything which can be used in :func:`print`'s `file` parameter.
    Defaults to :obj:`sys.stdout`.
    """
    
    def __init__(self):
        self.__cookie = None
        self.lh = LDAPHandler.get_instance()
        self.env = Environment.getInstance()

    def __get_change(self, dn):
        with self.lh.get_handle() as con:
            try:
                fltr = "(&(objectClass=auditWriteObject)(reqResult=0)({0})(reqStart>={1})(!({2})))".format(ldap.filter.filter_format("(reqDn=%s)", [dn]), self.__cookie, ldap.filter.filter_format("(reqAuthzID=%s)", [self.env.config.get('backend-monitor.modifier')]))
                return con.search_s(self.env.config.get('ldap.syncrepl-accesslog-base', default='cn=accesslog'), ldap.SCOPE_ONE, fltr,
                                   ['*'])

            except ldap.NO_SUCH_OBJECT:
                return None

    def bind_complete(self, ldap):
        print('BIND COMPLETE!', file=self.dest)
        print("\tWE ARE:", ldap.whoami_s(), file=self.dest)

    
    def refresh_done(self, items):
        print('REFRESH COMPLETE!', file=self.dest)
        print('BEGIN DIRECTORY CONTENTS:', file=self.dest)
        for item in items:
            print(item, file=self.dest)
            attrs = items[item]
            for attr in attrs.keys():
                print("\t", attr, sep='', file=self.dest)
                for value in attrs[attr]:
                    print("\t\t", value, sep='', file=self.dest)
        print('END DIRECTORY CONTENTS', file=self.dest)

    
    def record_add(self, dn, attrs):
        print('NEW RECORD:', dn, file=self.dest)
        for attr in attrs.keys():
            print("\t", attr, sep='', file=self.dest)
            for value in attrs[attr]:
                print("\t\t", value, sep='', file=self.dest)

    
    def record_delete(self, dn):
        print('DELETED RECORD:', dn, file=self.dest)

        res = self.__get_change(dn)
        if res is None:
            return

        e = EventMaker
        update = e.Event(
            e.BackendChange(
                e.DN(dn),
                e.ModificationTime("%sZ" % res['reqEnd'].split(".")[0]),
                e.ChangeType(res['reqType'])
            )
        )
        zope.event.notify(update)
    
    def record_rename(self, old_dn, new_dn):
        print('RENAMED RECORD:', file=self.dest)
        print("\tOld:", old_dn, file=self.dest)
        print("\tNew:", new_dn, file=self.dest)

    
    def record_change(self, dn, old_attrs, new_attrs):
        print('RECORD CHANGED:', dn, file=self.dest)
        for attr in new_attrs.keys():
            print("\t", attr, sep='', file=self.dest)
            for value in new_attrs[attr]:
                print("\t\t", value, sep='', file=self.dest)

    
    def cookie_change(self, cookie):
        print('COOKIE CHANGED:', cookie)
        #self.__cookie = cookie
        # rid=000,csn=20180209133349.356454Z#000000#000#000000
        self.__cookie = re.match(cookie, r"csn=([0-9.]+)Z").group(1) + "Z"

    
    def debug(self, message):
        print('[DEBUG]', message, file=self.dest)