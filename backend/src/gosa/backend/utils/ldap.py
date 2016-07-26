# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The GOsa backend includes a *LDAPHandler* class and a couple of utilities
make LDAP connections a little bit easier to use.

------
"""
import ldapurl
import ldap.sasl
import logging
from ldap.filter import filter_format
from contextlib import contextmanager
from gosa.common import Environment
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.exceptions import LDAPException


C.register_codes(dict(
    NO_SASL_SUPPORT=N_("No SASL support in the installed python-ldap detected"),
    LDAP_NO_CONNECTIONS=N_("No LDAP connection available"),
    ))


class LDAPHandler(object):
    """
    The LDAPHandler provides a connection pool with automatically reconnecting
    LDAP connections and is accessible thru the
    :meth:`gosa.backend.utils.ldap.LDAPHandler.get_instance` method.

    Example::

        >>> from gosa.backend.utils.ldap import LDAPHandler
        >>> from ldap.filter import filter_format
        >>> lh = LDAPHandler.get_instance()
        >>> uuid = 'you-will-not-find-anything'
        >>> with lh.get_handle() as con:
        ...     res = con.search_s(lh.get_base(),
        ...         ldap.SCOPE_SUBTREE,
        ...         filter_format("(&(objectClass=device)(uuid=%s))", [uuid]),
        ...         ['deviceStatus'])
        ...

    This example uses the connection manager *get_handle* to retrieve and free
    a LDAP connection. **Please note that you've to release a LDAP connection
    after you've used it.**

    The *LDAPHandler* creates connections based on what's configured in the
    ``[ldap]`` section of the GOsa configuration files. Here's a list of valid
    keywords:

    ============== =============
    Key            Description
    ============== =============
    url            LDAP URL to connect to
    bind_dn        DN to connect with
    bind_secret    Password to connect with
    pool_size      Number of parallel connections in the pool
    retry_max      How often a connection should be tried after the service is considered dead
    retry_delay    Time delta on which to try a reconnection
    ============== =============

    Example::

        [ldap]
        url = ldap://ldap.example.net/dc=example,dc=net
        bind_dn = cn=manager,dc=example,dc=net
        bind_secret = secret
        pool_size = 10

    .. warning::

        The *LDAPHandler* should not be used for ordinary object handling, because there's
        an object abstraction layer which does related things automatically.
        See `Object abstraction <objects>`_.
    """
    connection_handle = []
    connection_usage = []
    instance = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        # Initialize from configuration
        get = self.env.config.get
        self.__url = ldapurl.LDAPUrl(get("ldap.url"))
        self.__bind_user = get('ldap.bind-user', default=None)
        self.__bind_dn = get('ldap.bind-dn', default=None)
        self.__bind_secret = get('ldap.bind-secret', default=None)
        self.__pool = int(get('ldap.pool-size', default=10))

        # Sanity check
        if self.__bind_user and not ldap.SASL_AVAIL:
            raise LDAPException(C.make_error("NO_SASL_SUPPORT"))

        # Initialize static pool
        LDAPHandler.connection_handle = [None] * self.__pool
        LDAPHandler.connection_usage = [False] * self.__pool

    def get_base(self):
        """
        Return the configured base DN.

        ``Return``: base DN
        """
        return self.__url.dn

    def get_connection(self):
        """
        Get a new connection from the pool.

        ``Return``: LDAP connection
        """
        # Are there free connections in the pool?
        try:
            next_free = LDAPHandler.connection_usage.index(False)
        except ValueError:
            raise LDAPException(C.make_error("LDAP_NO_CONNECTIONS"))

        # Need to initialize?
        if not LDAPHandler.connection_handle[next_free]:
            get = self.env.config.get
            self.log.debug("initializing LDAP connection to %s" %
                    str(self.__url))
            conn = ldap.ldapobject.ReconnectLDAPObject("%s://%s" % (self.__url.urlscheme,
                self.__url.hostport),
                retry_max=int(get("ldap.retry-max", default=3)),
                retry_delay=int(get("ldap.retry-delay", default=5)))

            # We only want v3
            conn.protocol_version = ldap.VERSION3

            # If no SSL scheme used, try TLS
            if get("ldap.tls", default="True").lower() == "true" and ldap.TLS_AVAIL and self.__url.urlscheme != "ldaps":
                try:
                    conn.start_tls_s()
                except ldap.PROTOCOL_ERROR as detail:
                    self.log.debug("cannot use TLS, falling back to unencrypted session")

            try:
                # Simple bind?
                if self.__bind_dn:
                    self.log.debug("starting simple bind using '%s'" %
                        self.__bind_dn)
                    conn.simple_bind_s(self.__bind_dn, self.__bind_secret)
                elif self.__bind_user:
                    self.log.debug("starting SASL bind using '%s'" %
                        self.__bind_user)
                    auth_tokens = ldap.sasl.digest_md5(self.__bind_user, self.__bind_secret)
                    conn.sasl_interactive_bind_s("", auth_tokens)
                else:
                    self.log.debug("starting anonymous bind")
                    conn.simple_bind_s()

            except ldap.INVALID_CREDENTIALS as detail:
                self.log.error("LDAP authentication failed: %s" %
                        str(detail))

            LDAPHandler.connection_handle[next_free] = conn

        # Lock entry
        LDAPHandler.connection_usage[next_free] = True

        return LDAPHandler.connection_handle[next_free]

    def free_connection(self, conn):
        """
        Free an allocated pool connection to make it available for others.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        conn              Allocated LDAP connection
        ================= ==========================
        """
        index = LDAPHandler.connection_handle.index(conn)
        LDAPHandler.connection_usage[index] = False

    @contextmanager
    def get_handle(self):
        """
        Context manager which is meant to be used with the :meth:`with` statement.
        For an example see above.

        ``Return``: LDAP connection
        """
        conn = self.get_connection()
        try:
            yield conn
        finally:
            self.free_connection(conn)

    @staticmethod
    def get_instance():
        """
        Singleton for *LDAPHandler* objects. Return the instance.

        ``Return``: LDAPHandler instance
        """
        if not LDAPHandler.instance:
            LDAPHandler.instance = LDAPHandler()
        return LDAPHandler.instance


def map_ldap_value(value):
    """
    Method to map various data into LDAP compatible values. Maps
    bool values to TRUE/FALSE.

    ================= ==========================
    Parameter         Description
    ================= ==========================
    value             data to be prepared for LDAP
    ================= ==========================

    ``Return``: adapted dict
    """
    if type(value) == bool:
        return "TRUE" if value else "FALSE"
    if type(value) == list:
        return map(map_ldap_value, value)
    return value


def check_auth(user, password):
    get = Environment.getInstance().config.get
    log = logging.getLogger(__name__)

    url = ldapurl.LDAPUrl(get("ldap.url"))
    bind_user = get('ldap.bind-user', default=None)
    bind_dn = get('ldap.bind-dn', default=None)
    bind_secret = get('ldap.bind-secret', default=None)

    conn = ldap.ldapobject.ReconnectLDAPObject("%s://%s" % (url.urlscheme, url.hostport),
        retry_max=int(get("ldap.retry-max", default=3)),
        retry_delay=int(get("ldap.retry-delay", default=5)))

    # We only want v3
    conn.protocol_version = ldap.VERSION3

    # If no SSL scheme used, try TLS
    if get("ldap.tls", default="True").lower() == "true" and ldap.TLS_AVAIL and url.urlscheme != "ldaps":
        try:
            conn.start_tls_s()
        except ldap.PROTOCOL_ERROR as detail:
            log.debug("cannot use TLS, falling back to unencrypted session")

    try:
        # Get a connection
        if bind_dn:
            log.debug("starting simple bind using '%s'" % bind_dn)
            conn.simple_bind_s(bind_dn, bind_secret)
        elif bind_user:
            log.debug("starting SASL bind using '%s'" % bind_user)
            auth_tokens = ldap.sasl.digest_md5(bind_user, bind_secret)
            conn.sasl_interactive_bind_s("", auth_tokens)
        else:
            self.log.debug("starting anonymous bind")
            conn.simple_bind_s()

        # Search for the given user UID
        res = conn.search_s(url.dn, ldap.SCOPE_SUBTREE,
                filter_format("(&(|(objectClass=person)(objectClass=registeredDevice))(uid=%s))", [user]),
                ['dn'])

        if len(res) == 1:
            dn = res[0][0]
            log.debug("starting simple bind using '%s'" % dn)
            conn.simple_bind_s(dn, password)
            return True
        elif len(res) > 1:
            log.error("LDAP authentication failed: user %s not unique" % user)
        else:
            log.error("LDAP authentication failed: user %s not found" % user)

    except ldap.INVALID_CREDENTIALS as detail:
        log.error("LDAP authentication failed: %s" % str(detail))

    return False


def normalize_ldap(data):
    """
    Convert *single values* to lists.

    ================= ==========================
    Parameter         Description
    ================= ==========================
    data              input string or list
    ================= ==========================

    ``Return``: adapted data
    """
    if type(data) != list:
        return [data]

    return data
