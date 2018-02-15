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
from gosa.common.components import Plugin, PluginRegistry
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

        thread=threading.Thread(target=self.__client.run)

        self.log.debug("Syncrepl Client active for '{}'".format(self.__url))
        thread.start()
        thread.join()

    def stop(self):
        self.__client.please_stop()


class ReplCallback(BaseCallback):
    """
    Callback class which transfoms changes received by the syncrepl client and transforms them into
    `BackendChange`-events for GOsa.
    """

    def __init__(self):
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
                    fltr = "(&(objectClass=auditWriteObject)(reqResult=0){0}(reqStart>={1})(!{2}))".format(
                        ldap.filter.filter_format("(reqDn=%s)", [dn]),
                        csn,
                        ldap.filter.filter_format("(reqAuthzID=%s)", [self.env.config.get('backend-monitor.modifier')]))

                    self.log.debug("Searching in Base '{ldap_base}' with filter '{ldap_filter}'".
                                   format(ldap_base=self.env.config.get('ldap.syncrepl-accesslog-base',
                                                                        default='cn=accesslog'),
                                          ldap_filter=fltr))

                    result = con.search_s(self.env.config.get('ldap.syncrepl-accesslog-base', default='cn=accesslog'),
                                          ldap.SCOPE_ONELEVEL,
                                          fltr,
                                          attrlist=['*'])

                except ldap.NO_SUCH_OBJECT:
                    pass

        return result

    def bind_complete(self, ldap):
        self.log.debug("LDAP Bind complete as DN '{}'".format(ldap.whoami_s()))

    def refresh_done(self, items):
        self.log.debug("LDAP Refresh complete")
        self.__refresh_done = True

    def record_add(self, dn, attrs):
        if not self.__refresh_done:
            return

        self.log.debug("New record '{}'".format(dn))
        self.__spool.append({'dn': dn, 'cookie': self.__cookie})

    def record_delete(self, dn):
        if not self.__refresh_done:
            return

        self.log.debug("Deleted record '{}'".format(dn))
        self.__spool.append({'dn': dn, 'cookie': self.__cookie})

    def record_rename(self, old_dn, new_dn):
        if not self.__refresh_done:
            return

        self.log.debug("Renamed record '{}' -> '{}'".format(old_dn, new_dn))
        self.__spool.append({'dn': old_dn, 'new_dn': new_dn, 'cookie': self.__cookie})

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
                    change_type = res[0][1]['reqType'][0].decode('utf-8')
                    if change_type == "modrdn":
                        update = e.Event(
                            e.BackendChange(
                                e.DN(entry['dn']),
                                e.ModificationTime("%sZ" % res[0][1]['reqEnd'][0].decode('utf-8').split(".")[0]),
                                e.ChangeType(change_type)
                            )
                        )
                    else:
                        update = e.Event(
                            e.BackendChange(
                                e.DN(entry['dn']),
                                e.ModificationTime("%sZ" % res[0][1]['reqEnd'][0].decode('utf-8').split(".")[0]),
                                e.ChangeType(change_type)
                            )
                        )
                    self.log.debug("Sent update for entry '{}'".format(entry['dn']))
                    zope.event.notify(update)

        # 'rid=000,csn=20180212123829.435971Z#000000#000#000000;20171012151750.124741Z#000000#001#000000;20171012152055.398182Z#000000#002#000000'
        # re.match matches from 'beginning' (!) of string
        self.__cookie = re.match(r".+?csn=([0-9.]+)Z", cookie).group(1) + "Z"

    def debug(self, message):
        self.log.debug(message)
