Configuration
=============

This section details static configuration switches and runtime settings that
can be used to control the behaviour of the Clacks framework.

Common
******

All configuration flags detailed in this section (can) affect every component
of Clacks: they can be used to configure the *agent* or the *client*, etc.

Command line
------------

These are the common command line flags:

+--------+---------------+------------------------------------------------------------+
+ Short  | Long option   | Description                                                |
+========+===============+============================================================+
+ -c     | ----config    | Path to the configuration file used for this instance of   |
+        |               | Clacks. Note that this is only the base path: it is        |
+        |               | extended by  config  as a plain file and  config.d  as a   |
+        |               | directory containing configuration snippets i.e. for       |
+        |               | specific plugins.                                          |
+--------+---------------+------------------------------------------------------------+
+        | ----url       | URL to the AMQP broker to use.                             |
+--------+---------------+------------------------------------------------------------+
+        | ----profile   | If specified a performance analysis profile is written on  |
+        |               | shutdown.                                                  |
+--------+---------------+------------------------------------------------------------+


Configuration
-------------

Clacks configuration files are written in *ini*-Style. This simplifies editing and
enhances the overview. The common configuration covers a couple of sections detailed
here.

The frameworks configuration reader looks for two different styles of configuration:

 * single configuration file called 'config'
 * a directory with configuration snippets called 'config.d'

Splitting configuration makes sense if multiple plugins have been installed: they can
bring their own default configuration file without the need of modifying the main
configuration file.

The default base path where Clacks does look for configurations is **/etc/clacks**. It
scans for **/etc/clacks/config** and files matching **/etc/clacks/config.d/*.conf**. You
can override the base path using the *--config* switch.

Here is a sample of a clacks configuration (*/etc/clacks/config*)::

  [core]
  domain = net.example
  id = amqp
  base = dc=example,dc=net

  # Admin override for the user "admin"
  admins = admin
  
  [amqp]
  url = amqps://amqp.example.net:5671
  key = secret
  command-worker = 10
  
  [http]
  host = amqp.example.net
  port = 8080
  ssl = true
  keyfile = /etc/clacks/agent.key
  certfile = /etc/clacks/agent.crt
  
  [ldap]
  url = ldap://ldap.example.net/dc=example,dc=net
  bind-dn = cn=clacks,dc=example,dc=net
  bind-secret = secret
  pool-size = 10
  
  [backend-monitor]
  modifier = cn=clacks,dc=example,dc=net
  audit-log = /tmp/ldap-audit.log

This is an example of a split out logging configuration (*/etc/clacks/config.d/logging.conf*)::

  [loggers]
  keys=root,clacks
  
  [handlers]
  keys=console
  
  [formatters]
  keys=console
  
  
  [logger_root]
  level=WARNING
  handlers=console
  
  [logger_clacks]
  level=DEBUG
  handlers=console
  qualname=clacks
  propagate=0
  
  [handler_console]
  class=StreamHandler
  formatter=console
  args=(sys.stderr,)
  
  [formatter_console]
  format=%(asctime)s %(levelname)s: %(module)s - %(message)s
  datefmt=
  class=logging.Formatter


Section **core**
~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ base             | String     + The base is the LDAP style base DN where this Clacks        |
+                  |            + entity is responsible for. Example: dc=example,dc=net       |
+------------------+------------+-------------------------------------------------------------+
+ domain           | String     + Domain is the prefix that is used to address AMQP queues    |
+                  |            + and describe access control rules. In contrast to the base  |
+                  |            + keyword, it must only contain plain ASCII characters.       |
+                  |            +                                                             |
+                  |            + As a rule of thumb, we use a reversed domain notation i.e.  |
+                  |            + net.example                                                 |
+------------------+------------+-------------------------------------------------------------+
+ id               | String     + This is the instance ID. It is mandatory and used to connect|
+                  |            + to the AMQP broker.                                         |
+------------------+------------+-------------------------------------------------------------+
+ profile          | Boolean    + Flag to enable profiling.                                   |
+------------------+------------+-------------------------------------------------------------+


Section **amqp**
~~~~~~~~~~~~~~~~

Common AMQP related settings go to the [amqp] section.

+-------------------+------------+-------------------------------------------------------------+
+ Key               | Format     +  Description                                                |
+===================+============+=============================================================+
+ failover          | Boolean    + Flag to determine if automatic failover should be used.     |
+-------------------+------------+-------------------------------------------------------------+
+ key               | String     + The credentials used to connect to the AMQP broker(s).      |
+-------------------+------------+-------------------------------------------------------------+
+ reconnect         | Boolean    + Flag to determine if automatic reconnects should happen.    |
+-------------------+------------+-------------------------------------------------------------+
+ reconnect_interval| Integer    + Time interval to reconnect.                                 |
+-------------------+------------+-------------------------------------------------------------+
+ reconnect_limit   | Integer    + Number of maximum reconnect tries.                          |
+-------------------+------------+-------------------------------------------------------------+
+ url               | String     + The AMQP URL used to connect to a broker - initially.       |
+                   |            + Fallback is done automatically. Format is:                  |
+                   |            + amqp[s]://host.dns-domain:port/clacks-domain                |
+-------------------+------------+-------------------------------------------------------------+
+ worker            | Integer    + Number of workers to process commands.                      + 
+-------------------+------------+-------------------------------------------------------------+

Section **mongo**
~~~~~~~~~~~~~~~~~

The index is maintained in a MongoDB. These are the keys related to connecting
the NoSQL database.

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ uri              | String     + The hostname / port combination used to connect to the      |
+                  |            + MongoDB. Example: localhost:27017                           |
+------------------+------------+-------------------------------------------------------------+
+ user             | String     + Username used to connect to MongoDB - if required           |
+------------------+------------+-------------------------------------------------------------+
+ password         | String     + Password used to connect to MongoDB - if required           |
+------------------+------------+-------------------------------------------------------------+

Logging
~~~~~~~

Sections related to logging are using :ref:`the Python logging mechanism <python:logger>`.

Agent
*****

The agent has a set of configuration parameters that are detailed below. By default it comes with
a couple of plugins that may have parameters of their own. 

 * :ref:`Generic plugins <backend-misc>`
 * :ref:`GOsa GUI plugin <backend-gosa>`
 * :ref:`GOto system management <backend-goto>`
 * :ref:`Inventory handler <backend-inventory>`
 * :ref:`Password handler <backend-password>`
 * :ref:`POSIX related plugin <backend-posix>`
 * :ref:`Samba related plugin <backend-samba>`
 * :ref:`Generic user plugin <backend-user>`


Configuration
-------------

Section **agent**
~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ admins           | String     + Comma separated list of users where the ACL engine is       |
+                  |            + overridden.                                                 |
+------------------+------------+-------------------------------------------------------------+
+ index            | Boolean    +  Flag to enable/disable indexing.                           |
+------------------+------------+-------------------------------------------------------------+
+ node-timeout     | Integer    + Timeout in seconds when an agent is considered 'dead'.      |
+------------------+------------+-------------------------------------------------------------+

Section **amqp**
~~~~~~~~~~~~~~~~

Common AMQP related settings go to the [amqp] section.

+-------------------+------------+-------------------------------------------------------------+
+ Key               | Format     +  Description                                                |
+===================+============+=============================================================+
+ announce          | Boolean    + Publish the service via Zeroconf.                           +
+-------------------+------------+-------------------------------------------------------------+

Section **jsonrpc**
~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ path             | String     + Path where JSONRPC over HTTP is hooked in.                  |
+------------------+------------+-------------------------------------------------------------+

Section **http**
~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ announce         | Boolean    + Publish the service via Zeroconf.                           +
+------------------+------------+-------------------------------------------------------------+
+ cookie-lifetime  | Integer    + Lifetime of the cookie in seconds.                          |
+------------------+------------+-------------------------------------------------------------+
+ cookie-secret    | String     + Key used to encrypt the cookie.                             |
+------------------+------------+-------------------------------------------------------------+
+ host             | String     + Hostname to bind to / IP to bind to.                        |
+------------------+------------+-------------------------------------------------------------+
+ port             | Integer    + Portnumber to bind to.                                      |
+------------------+------------+-------------------------------------------------------------+
+ ssl              | Boolean    + Flag to tell that we want SSL.                              |
+------------------+------------+-------------------------------------------------------------+
+ certfile         | String     + Path to the certificate.                                    |
+------------------+------------+-------------------------------------------------------------+
+ keyfile          | String     + Path to the key file.                                       |
+------------------+------------+-------------------------------------------------------------+
+ ca-certs         | String     + Path to the CA file.                                        |
+------------------+------------+-------------------------------------------------------------+

Section **scheduler**
~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ gracetime        | Integer    + Gracetime for foreign jobs before they're assimilated.      +
+------------------+------------+-------------------------------------------------------------+

Section **ldap**
~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ bind-secret      | String     + Credentials for the bind user.                              +
+------------------+------------+-------------------------------------------------------------+
+ bind-user        | String     + DN of the bind user.                                        +
+------------------+------------+-------------------------------------------------------------+
+ retry-delay      | String     + Delay before a retry should be done.                        +
+------------------+------------+-------------------------------------------------------------+
+ retry-max        | String     + Maximum of retries before considering connection 'dead'.    +
+------------------+------------+-------------------------------------------------------------+
+ tls              | Boolean    + Use TLS to connect to the LDAP server.                      +
+------------------+------------+-------------------------------------------------------------+
+ url              | String     + URL to connect to - includes the LDAP base.                 +
+------------------+------------+-------------------------------------------------------------+

Backends
--------

Section **backend-sql**
~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ connection       | String     + SQLAlchemy string to connect to a SQL database.             +
+------------------+------------+-------------------------------------------------------------+

Section **backend-json**
~~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ database-file    | String     + Path to the database file that keeps the JSON information.  +
+------------------+------------+-------------------------------------------------------------+

Section **backend-ldap**
~~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ uuid-attribute   | String     + Attribute that keeps the object UUID.                       +
+------------------+------------+-------------------------------------------------------------+
+ create-attribute | String     + Attribute that keeps the creation date.                     +
+------------------+------------+-------------------------------------------------------------+
+ modify-attribute | String     + Attribute that keeps the modification date.                 +
+------------------+------------+-------------------------------------------------------------+
+ pool-filter      | String     + Filter to find nex ID.                                      +
+------------------+------------+-------------------------------------------------------------+

Section **backend-mongodb**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ database         | String     + Name of the MongoDB database.                               +
+------------------+------------+-------------------------------------------------------------+
+ collection       | String     + Name of the MongoDB collection inside the database.         +
+------------------+------------+-------------------------------------------------------------+


Backend monitor
---------------

Section **backend-monitor**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ audit-log        | String     + LDAP audit log file which is scanned for updates.           |
+------------------+------------+-------------------------------------------------------------+
+ modifier         | String     + DN of Clacks configured LDAP managing user.                 |
+------------------+------------+-------------------------------------------------------------+

ACL
---

Managing access control is configuration in the broader sense. You can read more on
this topic in the section :ref:`acl-handling`.


Client
******

The Clacks client is divided into two parts: the main part and the DBUS part. The client can
be extended thru plugins that may have separate configuration parameters, too:

 * :ref:`Generic DBUS support <client-dbus>`
 * :ref:`DBUS libnotify user notifications <client-notify>`
 * :ref:`Fusioninventory integration <client-fusion>`
 * :ref:`Powermanagement related methods <client-power>`
 * :ref:`Session notifications <client-session>`

Configuration
-------------

Section **client**
~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ ping-interval    | Integer    + Update ping to the Clacks framework to show: I'm still here.|
+------------------+------------+-------------------------------------------------------------+
+ spool            | String     + Spool directory used for several temporary files.           |
+------------------+------------+-------------------------------------------------------------+

DBUS
****

The DBUS component is the root-component of the Clacks client side. It allows the client
to trigger certain commands as root, but grants non-root operation for the client itself. By
default it comes with a couple of plugins that may have parameters of their own.

 * :ref:`Fusioninventory integration <dbus-fusion>`
 * :ref:`DBUS libnotify user notifications <dbus-notify>`
 * :ref:`Managing unix services <dbus-service>`
 * :ref:`Executing shell commands <dbus-shell>`
 * :ref:`Wake on lan client <dbus-wakeonlan>`

Configuration
-------------

Section **dbus**
~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ script-path      | String     + Script directory that is scanned for DBUS exported scripts. |
+------------------+------------+-------------------------------------------------------------+
