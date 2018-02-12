import ldap
import ldapurl
import logging
import os
import threading
import pprint

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


# TODO: Der Callback zu Änderungen wird zu einem Zeitpunkt aufgerufen, an dem die propagierte Änderung noch nicht in der LDAP-Datenbank committed wurde
# Die Vorgehensweise sollte sein:
# 1. Änderungscallback wird aufgerufen, spooled die Suche nach der Änderung mit dem aktuellen Cookie-Wert für die Suche
# 2. Neuer Cookie vom Server, die Änderung wurde also in der DB persistiert, eine Suche sollte jetzt ein Ergebnis bringen
#    Daher muss hier geschaut werden, ob noch Suchen gespooled sind, diese müssen dann durchgeführt werden

@implementer(IInterfaceHandler)
class SyncReplClient(Plugin):
    _priority_ = 21
    __client = None
    __url = None
    __tls = False

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing syncrepl client service")


    def serve(self):

        get = self.env.config.get
        self.__url = ldapurl.LDAPUrl(get("ldap.url"))
        self.__url.who = get('ldap.bind-dn', default=None)
        self.__url.cred = get('ldap.bind-secret', default=None)
        self.__url.scope = ldap.SCOPE_SUBTREE
        if get("ldap.tls", default="True").lower() == "true" and ldap.TLS_AVAIL and self.__url.urlscheme != "ldaps":
            self.__tls = True

        path = self.env.config.get('ldap.syncrepl-data-path', default=os.path.join(os.path.sep, 'var', 'lib', 'gosa', 'syncrepl', ''))
        if not os.path.exists(path):
            os.makedirs(path)

        self.__client = Syncrepl(data_path=path,
                                 callback=ReplCallback(),
                                 ldap_url=self.__url,
                                 mode=SyncreplMode.REFRESH_AND_PERSIST)

        # TODO: Evtl. threading verwenden?
        target=self.__client.run()

        self.log.debug("Syncrepl Client active for '{}'".format(self.__url))


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
        self.__refresh_done = False
        self.__spool = []
        self.lh = LDAPHandler.get_instance()
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing syncrepl client callback")


    def __get_change(self, dn, csn):
        result = None
        if self.__refresh_done and self.__cookie is not None:
            with self.lh.get_handle() as con:
                try:
                    fltr = "(&(objectClass=auditWriteObject)(reqResult=0){0}(reqStart>={1})(!{2}))".format(ldap.filter.filter_format("(reqDn=%s)", [dn]), csn, ldap.filter.filter_format("(reqAuthzID=%s)", [self.env.config.get('backend-monitor.modifier')]))
                    self.log.debug("Searching in Base '{ldap_base}' with filter '{ldap_filter}'".format(ldap_base=self.env.config.get('ldap.syncrepl-accesslog-base', default='cn=accesslog'), ldap_filter=fltr))
                    result = con.search_s(self.env.config.get('ldap.syncrepl-accesslog-base', default='cn=accesslog'), ldap.SCOPE_ONELEVEL, fltr, attrlist=['*'])

                except ldap.NO_SUCH_OBJECT:
                    pass

        return result


    def bind_complete(self, ldap):
        self.log.debug("LDAP Bind complete as DN '{}'".format(ldap.whoami_s()))


    def refresh_done(self, items):
        self.log.debug("LDAP Refresh complete")
        self.__refresh_done = True
        #for item in items:
        #    print(item, file=self.dest)
        #    attrs = items[item]
        #    for attr in attrs.keys():
        #        print("\t", attr, sep='', file=self.dest)
        #        for value in attrs[attr]:
        #            print("\t\t", value, sep='', file=self.dest)


    def record_add(self, dn, attrs):
        #res = self.__get_change(dn)
        #if res is None:
        #    return

        self.log.debug("New record '{}'".format(dn))
        #for attr in attrs.keys():
        #    print("\t", attr, sep='', file=self.dest)
        #    for value in attrs[attr]:
        #        print("\t\t", value, sep='', file=self.dest)


    def record_delete(self, dn):
        self.log.debug("Deleted record '{}'".format(dn))
        #res = self.__get_change(dn)
        #if res is None:
        #    return


        #e = EventMaker
        #update = e.Event(
        #    e.BackendChange(
        #        e.DN(dn),
        #        e.ModificationTime("%sZ" % res['reqEnd'].split(".")[0]),
        #        e.ChangeType(res['reqType'])
        #    )
        #)
        #zope.event.notify(update)

    def record_rename(self, old_dn, new_dn):
        #res = self.__get_change(dn)
        #if res is None:
        #    return
        self.log.debug("Renamed record '{}' -> '{}'".format(old_dn, new_dn))


    def record_change(self, dn, old_attrs, new_attrs):
        if not self.__refresh_done:
            return

        self.log.debug("Changed record '{}'".format(dn))
        self.__spool.append({'dn': dn, 'cookie': self.__cookie})


    def cookie_change(self, cookie):
        self.log.debug("Changed cookie '{}'".format(cookie))
        if self.__spool:
            e = EventMaker()
            spool = self.__spool
            self.__spool = []
            for entry in spool:
                res = self.__get_change(entry['dn'], entry['cookie'])
                if res:
                    update = e.Event(
                        e.BackendChange(
                            e.DN(entry['dn']),
                            e.ModificationTime("%sZ" % res[0][1]['reqEnd'][0].decode('utf-8').split(".")[0]),
                            e.ChangeType(res[0][1]['reqType'][0].decode('utf-8'))
                        )
                    )
                    self.log.debug("Sent update for entry '{}'".format(entry['dn']))
        # 'rid=000,csn=20180212123829.435971Z#000000#000#000000;20171012151750.124741Z#000000#001#000000;20171012152055.398182Z#000000#002#000000'
        # re.match matches from 'beginning' (!) of string
        self.__cookie = re.match(r".+?csn=([0-9.]+)Z", cookie).group(1) + "Z"


    def debug(self, message):
        self.log.debug(message)
