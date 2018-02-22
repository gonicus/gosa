import datetime
import multiprocessing

import ldap
import ldapurl
import logging
import os
import threading

import re

import time
import zope
from syncrepl_client import Syncrepl, SyncreplMode
from syncrepl_client.callbacks import BaseCallback
from zope.interface import implementer

from gosa.backend.utils.ldap import LDAPHandler
from gosa.common import Environment
from gosa.common.components import Plugin, PluginRegistry
from gosa.common.env import make_session
from gosa.common.error import GosaException
from gosa.common.event import EventMaker
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class SyncReplClient(Plugin):
    """
    The SyncReplClient notifies GOsa about LDAP changes from another origin.
    It uses the modifiers name to distinguish changes made by GOsa itself (which are ignored here) and
    changes done by third parties. To make this work you have to make sure, that GOsa uses a unique bind DN
    that no other third party LDAP client uses.

    The SyncReplClient needs the following config options:

    .. code-block:: ini

        [backend-monitor]
        syncrepl-data-path = <path-to-local-syncrepl-dir>
        modifier = <do not sync changes from this bind dn>

    .. IMPORTANT::

        Please make sure that you do not use the backend_ldap_monitor and the syncrepl-client
        together. Use either one or the other.

    """
    _priority_ = 21
    __thread = None
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

        path = self.env.config.get('backend-monitor.syncrepl-data-path')
        if path is None:
            # do not use syncrepl
            return

        if not os.path.exists(path):
            os.makedirs(path)

        if self.env.config.get('backend-monitor.modifier') is None:
            raise GosaException("backend-monitor.modifier config option is missing")

        client = Syncrepl(data_path=os.sep.join((path, 'database.db')),
                                 callback=ReplCallback(),
                                 ldap_url=self.__url,
                                 mode=SyncreplMode.REFRESH_AND_PERSIST)

        self.__thread = SyncReplThread(client)

        self.log.debug("Syncrepl Client active for '{}'".format(self.__url))
        self.__thread.start()

    def stop(self):
        self.__thread.stop()


class SyncReplThread(threading.Thread):

    def __init__(self, client):
        self.__client = client
        super(SyncReplThread, self).__init__(target=client.run)

    def run(self):
        try:
            if self.__client:
                self.__client.run()
        finally:
            self.__client.unbind()
            del self.__client

    def stop(self):
        self.__client.please_stop()


class ChangeProcessor(multiprocessing.Process):

    def __init__(self, queue):
        super(ChangeProcessor, self).__init__(target=self.process, args=(queue,))
        self.lh = LDAPHandler.get_instance()
        self.log = logging.getLogger(__name__)
        self.env = Environment.getInstance()
        index = PluginRegistry.getInstance('ObjectIndex')
        time = index.get_last_modification()
        self.log.info("initial cookie: %s " % time)
        if time is not None:
            self.__cookie = time.strftime('%Y%m%d%H%M%S.%fZ')
        else:
            self.__cookie = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S.%fZ')

    def process(self, queue):
        while True:
            cookie = queue.get()
            if cookie == "DONE":
                time.sleep(1)
            else:
                e = EventMaker()
                res = self.__get_change(self.__cookie, cookie)
                retried = 0
                while len(res) == 0 and retried <= 3:
                    # try again
                    time.sleep(0.05)
                    res = self.__get_change(self.__cookie, None)
                    retried += 1

                if len(res):
                    for change_dn, entry in res:
                        print(entry)
                        dn = entry['reqDN'][0].decode('utf-8')

                        change_type = entry['reqType'][0].decode('utf-8')
                        uuid = entry['reqEntryUUID'][0].decode('utf-8') if 'reqEntryUUID' in entry and len(entry['reqEntryUUID']) == 1 else None
                        modification_time = "%sZ" % res[0][1]['reqEnd'][0].decode('utf-8').split(".")[0]
                        if self.__cookie < modification_time:
                            self.__cookie = modification_time
                        if change_type in ["modrdn", "moddn"]:
                            if 'reqNewSuperior' in entry:
                                new_dn = "%s,%s" % (entry['reqNewRDN'][0].decode('utf-8'), entry['reqNewSuperior'][0].decode('utf-8'))
                            else:
                                new_dn = "%s," % entry['reqNewRDN'][0].decode('utf-8')
                            update = e.Event(
                                e.BackendChange(
                                    e.DN(dn),
                                    e.UUID(uuid),
                                    e.NewDN(new_dn),
                                    e.ModificationTime(modification_time),
                                    e.ChangeType(change_type)
                                )
                            )
                        else:
                            update = e.Event(
                                e.BackendChange(
                                    e.DN(entry['dn']),
                                    e.UUID(uuid),
                                    e.ModificationTime(modification_time),
                                    e.ChangeType(change_type)
                                )
                            )
                        self.log.debug("Sent update for entry '{}'".format(entry['dn']))
                        zope.event.notify(update)

    def __get_change(self, start, end):
        result = []
        with self.lh.get_handle() as con:
            try:
                fltr = "(&(objectClass=auditWriteObject)(reqResult=0)(reqStart>={0}){1}(!{2}))".format(
                    start,
                    ldap.filter.filter_format("(reqEnd>=%s)", [end]) if end is not None else "",
                    ldap.filter.filter_format("(reqAuthzID=%s)", [self.env.config.get('backend-monitor.modifier')])
                )

                self.log.debug("Searching in Base '{ldap_base}' with filter '{ldap_filter}'".
                               format(ldap_base=self.env.config.get('ldap.syncrepl-accesslog-base',
                                                                    default='cn=accesslog'),
                                      ldap_filter=fltr))

                result = con.search_s(self.env.config.get('ldap.syncrepl-accesslog-base', default='cn=accesslog'),
                                      ldap.SCOPE_ONELEVEL,
                                      fltr,
                                      attrlist=['*'])
                self.log.debug("Change found: %s" % result)
            except ldap.NO_SUCH_OBJECT:
                pass

        return result


class ReplCallback(BaseCallback):
    """
    Callback class which transfoms changes received by the syncrepl client and transforms them into
    `BackendChange`-events for GOsa.
    """
    __renamed = {}

    def __init__(self):
        self.__refresh_done = False
        self.__spool = []
        self.log = logging.getLogger(__name__)
        self.log.info("initializing syncrepl client callback")
        self.__queue = multiprocessing.Queue()

        p = ChangeProcessor(self.__queue)
        p.daemon = True
        p.start()

    def bind_complete(self, ldap, cursor):
        self.log.debug("LDAP Bind complete as DN '{}'".format(ldap.whoami_s()))

    def refresh_done(self, items, cursor):
        self.log.debug("LDAP Refresh complete")
        self.__refresh_done = True

    def record_add(self, dn, attrs, cursor):
        if not self.__refresh_done:
            return

        self.log.debug("New record '{}'".format(dn))
        # self.__spool.append({'dn': dn, 'cookie': self.__cookie, 'type': 'add'})

    def record_delete(self, dn, cursor):
        if not self.__refresh_done:
            return

        self.log.debug("Deleted record '{}'".format(dn))
        # self.__spool.append({'dn': dn, 'cookie': self.__cookie, 'type': 'delete'})

    def record_rename(self, old_dn, new_dn, cursor):
        if not self.__refresh_done:
            return

        self.log.debug("Renamed record '{}' -> '{}'".format(old_dn, new_dn))
        # self.__spool.append({'dn': old_dn, 'new_dn': new_dn, 'cookie': self.__cookie, 'type': 'modrdn'})

    def record_change(self, dn, old_attrs, new_attrs, cursor):
        if not self.__refresh_done:
            return

        self.log.debug("Changed record '{}'".format(dn))
        # self.__spool.append({'dn': dn, 'cookie': self.__cookie, 'type': 'modify'})

    def cookie_change(self, cookie):
        self.log.debug("Changed cookie '{}'".format(cookie))
        current_cookie = re.match(r".+?csn=([0-9.]+)Z", cookie).group(1) + "Z"
        self.__queue.put(current_cookie)

    def debug(self, message):
        self.log.debug(message)
