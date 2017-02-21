.. _quickstart:

Getting started
***************

This document contains information on *how to get started* with
the Clacks framework. It covers package based installations (Debian/Ubuntu),
package less installations and the common tasks that are needed to
operate an agent.


Common prerequisites
====================

The Clacks framework is a piece of software that has certain dependencies: it
communicates using the AMQP protocol and stores its information in directory
services or databases. These services - and their authentication - need to
be properly orchestrated to form a valid Clacks domain.

This section explains how to setup an AMQP broker, a LDAP server and optionally
shows how to tweak a DNS for service discovery in networks where local service
discovery is not sufficient.

.. note::

   In this guide all services run on the same host - which is not mandatory.

It also covers the configuration of SASL to get the AMQP broker to authenticate
with the LDAP service and helps to configure the AMQP authorization to avoid
malicious use of AMQP queues.


Choosing a domain
-----------------

The first step is to choose a domain where Clacks should operate
on. It is recommended to use a reversed form of the DNS domain name that is
valid for your current setup.

If you're operating in **example.net**, the Clacks domain should be **net.example**.
This reverse domain notation is used for determining access to certain objects
and makes it more easy to grant access to sub domains like **foo.example.net** later
on.

.. note::

   You're not forced to use this reversed notation, but you're encouraged to
   do so in setups that may be nested later on.


Choosing a hostname
-------------------

Be sure that your current hostname is the one you're going to use later on
and that *hostname* returns different output than *hostname -f*: hostname
alone should not return the fully qualified domain name.

Below, we use **agent** for the Clacks agent hostname and **client** for the
Clacks client hostname.


.. _setting-up-dns:

Service discovery
-----------------

Clacks uses the zeroconf protocol to find its counterparts by default. While
this works fine in local networks (like your test setup that you're using
to get started), this may lead to problems when your network is split to
several physical zones and routing of the discovery packages doesn't seam
reasonable.

If this is the case for you, you should configure your site DNS to allow
static zeroconf DNS service discovery.

Here is an example for the example.net domain::

  ; Zeroconf base setup
  b._dns-sd._udp                  PTR @   ;  b = browse domain
  lb._dns-sd._udp                 PTR @   ;  lb = legacy browse domain
  _services._dns-sd._udp          PTR _amqps._tcp
                                  PTR _https._tcp
  
  ; Zeroconf clacks records
  _amqps._tcp                     PTR Clacks\ RPC\ Service._amqps._tcp
  Clacks\ RPC\ Service._amqps._tcp  SRV 0 0 5671 agent.example.net.
                                  TXT path=/net.example service=clacks
  
  _https._tcp                     PTR Clacks\ Web\ Service._https._tcp
                                  PTR Clacks\ RPC\ Service._https._tcp
  Clacks\ Web\ Service._https._tcp  SRV 0 0 443 agent.example.net.
                                  TXT path=/admin/index.html
  Clacks\ RPC\ Service._https._tcp SRV 0 0 8080 agent.example.net.
                                  TXT path=/rpc service=clacks

This will add static service discovery entries for an agent with the
hostname *agent.example.net*.

After reloading your DNS, you may test your setup with::

  you@agent:~$ avahi-browse -D
  +  n/a  n/a example.net

  you@agent:~$ avahi-browse -rd example.net _amqps._tcp
  +   k.A. k.A. Clacks RPC Service                              _amqps._tcp          example.net
  =   k.A. k.A. Clacks RPC Service                              _amqps._tcp          example.net
     hostname = [agent.example.net]
     address = [10.3.64.59]
     port = [5671]
     txt = ["service=clacks" "path=/net.example"]


.. _setting-up-mongo:

Installing MongoDB
------------------

The Clacks framework maintains an index of all objects of its own. The reason for
this is that you can combine several backends like LDAP, JSON, Opsi, SQL, etc. to
assemble a single object. Searching in all backends is expensive and therefore we
use the local index.

Indexing is done with MongoDB which needs a basic, local install for the simplest
case::

  $ sudo apt-get install mongodb-server

Unless you're not doing bigger replicated setups, you should be fine with this.
Note that mongodb doesn't use authentication in this basic installation. Be sure
that you've at least restricted the access to *localhost* via

  ::
  bind_ip = 127.0.0.1

in your */etc/mongodb.conf*.


.. _setting-up-amqp:

Installing an AMQP service
--------------------------

Clacks uses AMQP as a messaging service. It will not work without it. Several 
used AMQP features lead to the requirement that Qpid needs to be used as
an AMQP message broker. Your distribution should have one for you::

  $ sudo apt-get install qpidd qpid-client qpid-tools


After qpid has been installed, you may modify the access policy
to fit the clacks-agent needs. A starting point could be a
`/etc/qpid/qpidd.acl` containing::
	
	# Group definitions
	group admins admin@QPID
	group agents agent@QPID
	group event-consumer agent@QPID
	group event-publisher agent@QPID
	
	# Admin is allowed to do everything
	acl allow admins all
	
	# Reply queue handling
	acl allow all access exchange name=reply-*
	acl allow all access queue name=reply-* owner=self
	acl allow all create queue name=reply-* durable=false autodelete=true
	acl allow all consume queue name=reply-* owner=self
	acl allow all publish exchange routingkey=reply-* owner=self
	
	# Event producer
	acl allow event-publisher all     queue    name=net.example
	acl allow event-publisher all     exchange name=net.example
	
	# Event consumer
	acl allow all create  queue    name=event-listener-*
	acl allow all delete  queue    name=event-listener-* owner=self
	acl allow all consume queue    name=event-listener-* owner=self
	acl allow all access  queue    name=event-listener-* owner=self
	acl allow all purge   queue    name=event-listener-* owner=self
	acl allow all access  queue    name=net.example
	acl allow all access  exchange name=net.example
	acl allow all access  exchange name=event-listener-* owner=self
	acl allow all bind    exchange name=net.example queuename=event-listener-* routingkey=event
	acl allow all unbind  exchange name=net.example queuename=event-listener-* routingkey=event
	acl allow all publish exchange name=net.example routingkey=event
	
	# Let agents do everything with the net.example queues and exchanges, agents itself
	# are trusted by now.
	acl allow agents all queue name=net.example.*
	acl allow agents all exchange name=net.example.*
	acl allow agents all exchange name=amq.direct queuename=net.example.*
	
	# Let every authenticated instance publish to the command queues
	acl allow all access   queue    name=net.example.command.*
	acl allow all publish  queue    name=net.example.command.*
	acl allow all publish  exchange routingkey=net.example.command.*
	acl allow all access   exchange name=net.example.command.*
	
	# Let clients create their own queue to listen on
	acl allow all access  queue    name=net.example
	acl allow all access  queue    name=net.example.client.* owner=self
	acl allow all consume queue    name=net.example.client.* owner=self
	acl allow all create  queue    name=net.example.client.* exclusive=true autodelete=true durable=false
	acl allow all access  exchange name=net.example
	acl allow all access  exchange name=net.example.client.* owner=self
	acl allow all bind    exchange name=amq.direct queuename=net.example.client.*
	
	# Let agents send to the client queues
	acl allow agents publish  exchange  routingkey=net.example.client.*
	
	# By default, drop everything else
	acl deny all all

.. note::

   Remember that you've to adjust the domain from *net.example* to whatever you've
   chosen in the beginning. Same for *agent* which is the hostname of your Clacks
   agent and *admin* which is the *cn* of your LDAP administrator.


For production use, you should enable SSL for the AMQP broker. To generate the SSL
certificates, you need to install the nss tools::

  $ sudo apt-get install libnss3-tools
  $ mkdir CA_db
  $ certutil -N -d CA_db
  $ certutil -S -d CA_db -n "ExampleCA" -s "CN=ExampleCA,O=Example,ST=Network,C=DE" -t "CT,," -x -2

At the prompt, answer:

 * It will prompt you for a password. Enter the password you specified when creating the root CA database.
 * Type “y” for “Is this a CA certificate [y/N]?”
 * Press enter for “Enter the path length constraint, enter to skip [<0 for unlimited path]: >”
 * Type “n” for “Is this a critical extension [y/N]?”

::

  $ certutil -L -d CA_db -n "ExampleCA" -a -o CA_db/rootca.crt
  $ mkdir server_db
  $ certutil -N -d server_db
  $ certutil -A -d server_db -n "ExampleCA" -t "TC,," -a -i CA_db/rootca.crt
  $ certutil -R -d server_db -s "CN=agent.example.net,O=Example,ST=Network,C=DE" -a -o server_db/server.req
  $ certutil -C -d CA_db -c "ExampleCA" -a -i server_db/server.req -o server_db/server.crt -2 -6

At the prompt, answer:

 * Select “0 - Server Auth” at the prompt
 * Press 9 at the prompt
 * Type “n” for “Is this a critical extension [y/N]?”
 * Type “n” for “Is this a CA certificate [y/N]?”
 * Enter “-1″ for “Enter the path length constraint, enter to skip [<0 for unlimited path]: >”
 * Type “n” for “Is this a critical extension [y/N]?”
 * When prompted password, enter the password you specified when creating the root CA database.

::

  $ certutil -A -d server_db -n agent.example.net -a -i server_db/server.crt -t ",,"


This information has been taken from http://rajith.2rlabs.com/2010/03/01/apache-qpid-securing-connections-with-ssl/
where you can find more detailed information about that.

Copy the *server_db* directory to */etc/qpid/ssl*, create a *broker-pfile* containing
the secret to unlock the certificate and add these lines to your qpidd.conf::

  ssl-cert-password-file=/etc/qpid/ssl/broker-pfile
  ssl-cert-db=/etc/qpid/ssl/server_db/
  ssl-cert-name=agent.example.net
  ssl-port=5671

.. _setting-up-ldap:

Installing the LDAP service
---------------------------

In the base setup you need to setup an LDAP server. It contains the very basic
structure you're going to maintain with Clacks. Your distribution has LDAP packages
for sure. We're using OpenLDAP in this case::

  $ sudo DEBIAN_PRIORITY=low apt-get install slapd ldap-utils

Select a base and the administrative credentials. Memorize these values, because
you'll need them later on.

.. note::

   In this document we'll use the domain-component style for your current
   domain. I.e. **dc=example,dc=net** is the base. **cn=admin,dc=example,dc=net** is
   the administrative DN.

Clacks itself does not require to install an additional LDAP schema. Nearly.
Except if you plan to use Clacks *clients*.

To use the client mechanisms, a couple of schema files have to be added to
your configuration. The following text assumes that you've a plain / empty
stock Debian configuration on your system. If it's not the case, you've to
know what to do yourself.

First, install the provided schema files. These commands have to be executed
with *root* power by default, so feel free to use sudo and find the schema
*LDIF* files in the ``contrib/ldap`` directory of your clacks document
directory. Install these schema files like this::

	$ sudo ldapadd -Y EXTERNAL -H ldapi:/// -f registered-device.ldif
	$ sudo ldapadd -Y EXTERNAL -H ldapi:/// -f installed-device.ldif
	$ sudo ldapadd -Y EXTERNAL -H ldapi:/// -f configured-device.ldif

After you've done that, find out which base is configured for your system::

	$ sudo ldapsearch -LLL -Y EXTERNAL -H ldapi:/// -b cn=config olcSuffix=* olcSuffix
	SASL/EXTERNAL authentication started
	SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
	SASL SSF: 0
	dn: olcDatabase={1}hdb,cn=config
	olcSuffix: dc=example,dc=net

In this case, you'll see the configured suffix as **dc=example,dc=net** in the
result set. Your milieage may vary.

Based on the suffix, create a *LDIF* file containing an updated index - on top with
the *DN* shown in the result of the search above::

	dn: olcDatabase={1}hdb,cn=config
	changetype: modify
	replace: olcDbIndex
	olcDbIndex: default sub
	olcDbIndex: objectClass pres,eq
	olcDbIndex: cn pres,eq,sub
	olcDbIndex: uid eq,sub
	olcDbIndex: uidNumber eq
	olcDbIndex: gidNumber eq
	olcDbIndex: mail eq,sub
	olcDbIndex: deviceStatus pres,sub
	olcDbIndex: deviceType pres,eq
	olcDbIndex: sn pres,eq,sub
	olcDbIndex: givenName pres,eq,sub
	olcDbIndex: ou pres,eq,sub
	olcDbIndex: memberUid eq
	olcDbIndex: uniqueMember eq
	olcDbIndex: deviceUUID pres,eq

.. warning::

   If you have not installed the Clacks device schema files, you have to skip the
   attributes *deviceUUID*, *deviceStatus* and *deviceType* in the index list.

Save that file to *index-update.ldif* and add it to your LDAP using::

	$ sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f index-update.ldif

Your LDAP now has the required schema files and an updated index to perform
searches in reliable speed.

The agent itself needs an entry inside that LDAP that is used to authenticate
to the AMQP service. Create this entry - again inside an LDIF file like this::

  dn: cn=agent,dc=example,dc=net
  objectClass: simpleSecurityObject
  objectClass: organizationalRole
  cn: agent
  userPassword: secret

Save that file to *agent.ldif* and apply it to your LDAP using::

  $ sudo ldapadd -Y EXTERNAL -H ldapi:/// -f agent.ldif

The password is unencrypted in the moment, that can be changed using::

  $ sudo ldappasswd -Y EXTERNAL -H ldapi:/// cn=agent,dc=example,dc=net

Change the password to the one you like and memorize it for use with the
Clacks agent configuration below.


.. _setting-up-ldap-auth:

AMQP LDAP-Authentication
------------------------

Qpid is not LDAP enabled by default, but it supports everything supported
by SASL thru the *saslauthd*. To install *saslauthd* run::

  $ sudo apt-get install sasl2-bin

The daemon is not started by default. To configure it to start up automatically
and to use LDAP for it's authentication source, edit the file /etc/default/saslauthd
like this::

  #
  # Settings for saslauthd daemon
  # Please read /usr/share/doc/sasl2-bin/README.Debian for details.
  #
  
  # Should saslauthd run automatically on startup? (default: no)
  START=yes
  
  # Description of this saslauthd instance. Recommended.
  # (suggestion: SASL Authentication Daemon)
  DESC="SASL Authentication Daemon"
  
  # Short name of this saslauthd instance. Strongly recommended.
  # (suggestion: saslauthd)
  NAME="saslauthd"
  
  # Which authentication mechanisms should saslauthd use? (default: pam)
  #
  # Available options in this Debian package:
  # getpwent  -- use the getpwent() library function
  # kerberos5 -- use Kerberos 5
  # pam       -- use PAM
  # rimap     -- use a remote IMAP server
  # shadow    -- use the local shadow password file
  # sasldb    -- use the local sasldb database file
  # ldap      -- use LDAP (configuration is in /etc/saslauthd.conf)
  #
  # Only one option may be used at a time. See the saslauthd man page
  # for more information.
  #
  # Example: MECHANISMS="pam"
  MECHANISMS="ldap"
  
  # Additional options for this mechanism. (default: none)
  # See the saslauthd man page for information about mech-specific options.
  MECH_OPTIONS=""
  
  # How many saslauthd processes should we run? (default: 5)
  # A value of 0 will fork a new process for each connection.
  THREADS=5
  
  # Other options (default: -c -m /var/run/saslauthd)
  # Note: You MUST specify the -m option or saslauthd won't run!
  #
  # WARNING: DO NOT SPECIFY THE -d OPTION.
  # The -d option will cause saslauthd to run in the foreground instead of as
  # a daemon. This will PREVENT YOUR SYSTEM FROM BOOTING PROPERLY. If you wish
  # to run saslauthd in debug mode, please run it by hand to be safe.
  #
  # See /usr/share/doc/sasl2-bin/README.Debian for Debian-specific information.
  # See the saslauthd man page and the output of 'saslauthd -h' for general
  # information about these options.
  #
  # Example for postfix users: "-c -m /var/spool/postfix/var/run/saslauthd"
  OPTIONS="-c -m /var/run/saslauthd"

Additionally, you've to set up the LDAP configuration for *saslauthd* in the
configuration file */etc/saslauthd.conf*::

  ldap_servers: ldap://agent.example.net
  ldap_search_base: dc=example,dc=net
  ldap_filter: (|(&(objectClass=simpleSecurityObject)(cn=%U))(&(objectClass=inetOrgPerson)(uid=%U))(&(objectClass=registeredDevice)(deviceUUID=%U)))
  ldap_scope: sub
  ldap_size_limit: 0
  ldap_time_limit: 15
  ldap_timeout: 15
  ldap_version: 3
  ldap_debug: 255

.. note::

   You may need to adjust the list of LDAP servers and the search base
   according to your setup.

If you have **not** installed the Clacks device schema files, you have to skip the
search for *registeredDevice* and the search filter should look like this::

  ldap_filter: (|(&(objectClass=simpleSecurityObject)(cn=%U))(&(objectClass=inetOrgPerson)(uid=%U)))

Start the service and test it::

  $ sudo service saslauthd start
  $ sudo testsaslauthd -u agent -p secret -r QPID

If that works pretty well, connect the Qpid SASL mechaism to *saslauthd* by editing
*/etc/sasl2/qpidd.conf* like this::

  pwcheck_method: saslauthd
  mech_list: PLAIN LOGIN

To let Qpid access the *saslauthd* socket, it needs to be added to the *sasl* group and the
service needs to be restarted::

  $ sudo adduser qpidd sasl
  $ sudo service qpidd restart

Check if it works like supposed to::

  $ qpid-config -a admin/secret@hostname queues

The command should list a few queues that are defined by default.


Using pre-built packages
========================

Currently there are only Debian/Ubuntu packages available for the Clacks
framework. Additionally you need at least Wheezy/12.04 to proceed.

.. note::

    Older versions of Debian/Ubuntu do not have the required package versions
    installed. Installations may work using backports and/or re-building


APT repository
--------------

Please create a new file under /etc/apt/sources.list.d/clacks.list and place
the following content inside::

   deb http://apt.gonicus.de/debian wheezy clacks

Now install the key package::

   $ sudo apt-get install gonicus-keyring

The installer will report an untrusted package - which is ok in this case,
because it *contains* the GONICUS signing key. It is used to sign the packages
we'll download in the next step.


Installing a Clacks agent
-------------------------

To use the Clacks framework, you need at least one agent that loads some
plugins and provides the base communication framework. Compared to the
client and the shell, the agent is the part that needs most supplying
services.

.. warning::

  Until we reach version 1.0, you can only use one agent.


For the first node, install *QPID*, *LDAP* and *MongoDB*::
  
  $ sudo apt-get install mongodb-server slapd ldap-utils sasl2-bin

Memorize the user and passwords you've used for LDAP. MongoDB is just
fine and can be configured to only run locally for now.

To proceed, you have to perform the actions detailed in:

 * :ref:`setting-up-dns`
 * :ref:`setting-up-ldap`
 * :ref:`setting-up-amqp`
 * :ref:`setting-up-ldap-auth`

If this is fine, copy over the configuration file for the Clacks agent to
/etc/clacks/config and adapt the settings to match the ones for your site::
  
  $ sudo install -o root -g clacks -m 0640 /usr/share/doc/clacks-agent/examples/config /etc/clacks/config
  $ sudo vi /etc/clacks/config

At least adapt the node-name to fit the current host name of your server
and the LDAP credentials that you've created in **Setting up LDAP**.

No you can start the agent using::
  
  $ sudo supervisorctl start clacks-agent

Watch out for errors in */var/log/clacks.log*. If everything went up well,
the agent starts indexing your LDAP and you might see some warnings about
not recognized objects.

After the agent is up and running, you should define a couple of ACL sets
in order to get rid of the initial ACL override in your Clacks configuration.

Please take a look at :ref:`setting-up-acl`.


Installing a Clacks client
--------------------------

Clacks clients are nodes that you want to have *under the hood* in some form. They
are monitored, inventorized using fusioninventory (optionally) and can be controlled
in various ways. Controlling addresses topics like *config management* (i.e. using puppet),
*system states* (reboot, wake on lan, etc.), user notifications and executing certain
commands as **root** on these systems.

To install the client you need to work thru two steps. First, install it (the
example includes the inventory part)::
    
  $ sudo apt-get install clacks-client fusioninventory-agent

The client tries to start, but will fail due to missing configurations, so the
second step is to generate a configuration - aka *joining* the client to the
Clacks domain. May sound familiar to Microsoft users.

.. warning::

  In the current version, it is only possible to do an *active* join. The former
  GOsa client *incoming* mechanism is currently being implemented and not usable
  right now.

Joining is easy::

  $ sudo clacks-join

It will first search for an active agent. Then you'll have to provide the credentials
of a user that is allowed to join the client (i.e. the administrator you've initially
created).

.. note::

  Maybe the zeroconf mechanism that is used to find an agent is not working
  in your setup. In this case use the *--url* switch to provide the complete
  AMQP URL. Example::
    
    $ sudo clacks-join --url amqps://agent.example.net/net.example

If this succeeds, a configuration file is created automatically and you can start the
client::
  
  $ sudo supervisorctl start clacks-client

If everything went fine, the client is up and running. You'll see some messages
in the agent's log and the client log for that. As for servers, messages find their
way to */var/log/clacks.log*.

.. note::

  Joining requires at least one active agent.

Note that while it is technically no problem to run both - a client and an agent -- on the
same physical node, it is not supported by the packages in the moment.


Installing the shell
--------------------

Compared to agents and clients, the shell installation is trivial::

  $ sudo apt-get install clacks-shell

Just try to run it::
  
  $ clacksh
  Searching service provider...
  Connected to https://amqp.example.net:8080/rpc
  Username [cajus]:
  Password:
  Clacks infrastructure shell. Use Ctrl+D to exit.
  >>> clacks.help()
  ...


Without pre-built packages
==========================

Installing without packages makes sense for - well distributions where we
have no packages yet, and for developers of course.

This section describes how to get things up and running.


Common setup
------------

System prerequisites
^^^^^^^^^^^^^^^^^^^^

To run the services in the designed way later on, you need a special user
and a couple of directories::

    $ sudo adduser --system --group clacks --home=/var/lib/clacks

If you're going to run the service in daemon mode, please take care that
there's a */var/run/clacks* for placing the PID files.


Python prerequisites
^^^^^^^^^^^^^^^^^^^^

While we try to keep everything inside a virtual python environment for
development, some of the python modules need compilation - which rises the
number of required packages drastically. For the time being, please install
the following packages in your system::

  $ sudo apt-get install avahi-daemon hal pep8 pylint python python-avahi python-cjson \
                 python-coverage python-crypto python-dateutil python-dbus \
                 python-dmidecode python-dumbnet python-gtk2 python-kid python-ldap \
                 python-libxml2 python-logilab-astng python-logilab-common \
                 python-logilab-constraint python-lxml python-netifaces python-newt \
                 python-nose python-notify python-openssl python-pkg-resources python-pybabel \
                 python-pymongo python-qpid python-setuptools python-smbpasswd python-tornado \
                 python-unidecode python-zope.event python-zope.interface

If you've an RPM'ish distribution, you've to find the rpm names for this or install
everything via *easy_install*.


Setup a virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^

As a non-root user, initialize the virtual environment::

  $ virtualenv --setuptools --system-site-packages --python=python2.7 clacks
  $ cd clacks
  $ source bin/activate


Obtaining the source
^^^^^^^^^^^^^^^^^^^^

For now, please use git::

   $ cd clacks
   $ git clone git://github.com/gonicus/clacks.git src

This will place all relevant files inside the 'src' directory.

.. warning::
      The "source bin/activate" has to be done every time you work in or with the
      virtual environment. Stuff will fail if you don't do this. If you're asked for
      sudo/root, you're doing something wrong.


Installing a Clacks agent
-------------------------

To run the agent, you most likely need a working AMQP broker and
a working LDAP setup.

To proceed, you have to perform the actions detailed in:

 * :ref:`setting-up-dns`
 * :ref:`setting-up-ldap`
 * :ref:`setting-up-amqp`
 * :ref:`setting-up-ldap-auth`


Deploy a development agent
^^^^^^^^^^^^^^^^^^^^^^^^^^

To deploy the agent, please run these commands inside the activated
virtual environment::

  $ ( cd common && ./setup.py develop )
  $ ( cd agent && ./setup.py develop )


  Alternatively you can deploy the complete package using::

  $ ./setup.py develop


.. warning:: 

	Using the above command to build the complete package will also build
	additional modules like libinst, amires, ... 

     	This will increase the configuration effort drastically, which is not 
	recommended during the quickstart quide.


Starting the service
^^^^^^^^^^^^^^^^^^^^

In a productive environment, everything should be defined in the configuration
file, so copy the configuration file to the place where clacks expects it::

  $ mkdir -p /etc/clacks
  $ cp ./src/agent/src/clacks/agent/data/agent.conf /etc/clacks/config

Now take a look at the config file and adapt it to your needs.

You can start the daemon in foreground like this::

  $ clacks-agent

.. warning::

    Make sure, you've entered the virtual environment using "source bin/activate"
    from inside the clacks directory.


If you want to run the agent in a more productive manner, you should
use a tool like *supervisord* to run it as a daemon.

Here is an example config file::

	[core]
	domain = net.example
	profile = False
	id = agent
	admins = admin
	base = dc=example,dc=net
	
	[amqp]
	url = amqps://amqp.example.net:5671
	id = agent
	key = secret
	command-worker = 10
	
	[http]
	host = agent.example.net
	port = 8080
	ssl = true
	keyfile = /etc/clacks/agent.key
	certfile = /etc/clacks/agent.crt
	
	[ldap]
	url = ldap://localhost/dc=example,dc=net
	bind_dn = cn=admin,dc=example,dc=net
	bind_secret = secret
	pool_size = 10
	
	[backend-monitor]
	modifier = cn=admin,dc=gonicus,dc=de
	audit-log = /var/log/ldap-audit.log

	[handlers]
	keys=syslog,console
	
	[formatters]
	keys=syslog,console
	
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
	
	[handler_syslog]
	class=logging.handlers.SysLogHandler
	formatter=syslog
	args=('/dev/log',)
	
	[formatter_syslog]
	format=%(name)s: %(module)s - %(message)s
	datefmt=
	class=logging.Formatter
	
	[formatter_console]
	format=%(asctime)s %(levelname)s: %(module)s - %(message)s
	datefmt=
	class=logging.Formatter

You need to generate *agent.crt* and *agent.key* either from your existing
CA or you can quickly generate a self-signed server cert/key pair::

  $ openssl genrsa -des3 -out agent.key 1024
  Generating RSA private key, 1024 bit long modulus
  .........................................................++++++
  ........++++++
  e is 65537 (0x10001)
  Enter PEM pass phrase:
  Verifying password - Enter PEM pass phrase:

Certificate signing request::

  $ openssl req -new -key agent.key -out agent.csr

Strip the password from the key::

  $ cp agent.key agent.key.org
  $ openssl rsa -in agent.key.org -out agent.key

Generate the certificate::

  $ openssl x509 -req -days 365 -in agent.csr -signkey agent.key -out agent.crt

Install these files to a directory where *clacks-agent* can read them - i.e.
like shown in the configuration above: */etc/clacks*


Installing a Clacks shell
-------------------------

Installing
^^^^^^^^^^

To deploy the shell, use::

  $ ( cd common && ./setup.py develop )
  $ ( cd shell && ./setup.py develop )

inside your activated virtual env. You can skip this if you ran *./setup.py* for
a complete deployment.


First steps
^^^^^^^^^^^

The clacks shell will use zeroconf/DNS to find relevant connection methods. Alternatively
you can specify the connection URL to skip zeroconf/DNS.

Start the shell and send a command::

  $ clacksh
  Searching service provider...
  Connected to amqps://agent.example.net:5671/net.example
  Username [admin]: 
  Password: 
  Clacks infrastructure shell. Use Ctrl+D to exit.
  >>> clacks.help()
  ...
  >>> mksmbhash("secret")
  >>> <Strg+D>

If you tend to use a connection URL directly, use::

  $ clacksh http[s]://agent.example.net:8080/rpc

for HTTP based sessions or ::

  $ clacksh amqp[s]://agent.example.net/net.example

for AMQP based sessions.


Installing a Clacks client
--------------------------

A clacks client is a device instance that has been joined into the clacks network.
Every client can incorporate functionality into the network - or can just be
a managed client.


Installing
^^^^^^^^^^

To deploy the client components, use ::

  $ ( cd common && ./setup.py develop )
  $ ( cd client && ./setup.py develop )
  $ ( cd dbus && ./setup.py develop )

inside your activated virtual env. You can skip this if you ran *./setup.py* for
a complete deployment.


Joining the party
^^^^^^^^^^^^^^^^^

A client needs to authenticate to the Clacks framework. In order to create the required
credentials for that, you've to "announce" or "join" the client to the system.

To do that, run ::

  $ sudo -s
  # cd clacks
  # source bin/activate
  # clacks-join

on the client you're going to join. In the development case, this may be the
same machine which runs the agent.


Running the root component
^^^^^^^^^^^^^^^^^^^^^^^^^^

Some functionality may need root permission, while we don't want to run the complete
client as root. The clacks-dbus component is used to run dedicated tasks as root. It
can be extended by simple plugins and registers the resulting methods in the dbus
interface.

To use the dbus-component, you've to allow the clacks system user (or whatever user
the clacks-client is running later on) to use certain dbus services. Copy and eventually
adapt the file src/contrib/dbus/org.clacks.conf to /etc/dbus-1/system.d/ and
reload your dbus service. ::

  $ sudo service dbus reload

To start the dbus component, activate the python virtual environment as root and run
the clacks-dbus component in daemon or foreground mode::

  $ sudo -s
  # cd clacks
  # source bin/activate
  # clacks-dbus


Running the client
^^^^^^^^^^^^^^^^^^

To run the client, you should put your development user into the clacks group - to
be able to use the dbus features::

  $ sudo adduser $USER clacks

You might need to re-login to make the changes happen. After that, start the clacks
client inside the activated virtual environment::

  $ clacks-client


Common configuration
====================

.. _setting-up-acl:

Configuring access control
--------------------------

Because the Clacks framework supports various backends, it does access control of its
own. In order to do something reasonable with the framework, you've either to override
the access control (like done with the *admin* user), or you can apply fine grained
ACL rules and roles to your directory tree.

On the command line, you can use the *acl-admin* tool to manage the ACL system. It uses
the service discovery feature and asks for a username and password if it finds a service.

.. note::
  
  You can override the service discovery by issuing::

    $ acl-admin --user agent --password secret --url https://agent.example.net:8080/rpc

The *acl-admin* is in development. Currently, you need to fire one subcommand per call,
which makes it a bit uncomfortable for the first time. Here are a couple of ACLs and
roles that make sense::

  # Allow clients to send certain events
  add role dc=example,dc=net Clients
  add roleacl with-actions name=Clients,dc=example,dc=net 0 psub "^net\.example\.command\.core\.(getMethods|sendEvent):x"
  add roleacl with-actions name=Clients,dc=example,dc=net 0 psub "^net\.example\.event\.(Inventory|ClientAnnounce|ClientLeave|ClientSignature|ClientPing|UserSession)$:x"
  add acl with-role dc=example,dc=net 0 '^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$' Clients
  
  # Create GUI ACL role that allows login to a GUI
  add role dc=example,dc=net GUI
  add roleacl with-actions "name=GUI,dc=example,dc=net" 1 sub "^net\.example\.command\.core\.(getSessionUser|get_error|getBase|search|openObject|dispatchObjectMethod|setObjectProperty|closeObject|reloadObject)$:x"
  add roleacl with-actions "name=GUI,dc=example,dc=net" 1 sub "^net\.example\.command\.gosa\.(getTemplateI18N|getAvailableObjectNames|getGuiTemplates|getUserDetails|search|getObjectDetails|searchForObjectDetails|loadUserPreferences|saveUserPreferences)$:x"
  add roleacl with-actions "name=GUI,dc=example,dc=net" 1 sub "^net\.example\.command\.password\.(accountUnlockable|accountLockable|listPasswordMethods)$:x"

  # Create SelfService role that allows occupants to modify some of their attributes
  add role "dc=example,dc=net" SelfService
  add roleacl with-actions name=SelfService,dc=example,dc=net 0 sub "^net\.example\.command\.core\.(openObject|dispatchObjectMethod|setObjectProperty|closeObject):x"
  add roleacl with-actions name=SelfService,dc=example,dc=net 0 sub "^net\.example\.command\.password\.(listPasswordMethods|accountLockable|accountUnlockable):x"
  add roleacl with-actions name=SelfService,dc=example,dc=net 0 sub "^net\.example\.command\.objects\.(User|PosixUser|SambaUser|ShadowUser):crowdsexm"
  
  # Create Administrative role - everything is allowed
  add role "dc=example,dc=net" Administrators
  add roleacl with-actions name=Administrators,dc=example,dc=net -100 psub "^net\.example\..*:crwdsex"
  
  # Assign user 'ruth' the role 'Administrators'
  add acl with-role dc=example,dc=net -100 ruth Administrators 
  
  # Assign user 'foobar' the SelfService and GUI role
  add acl with-role dc=example,dc=net 0 foobar SelfService 
  add acl with-role dc=example,dc=net 0 foobar GUI


Configuring an LDAP update hook
-------------------------------

Maintaining an index of our own has several advantages: better search capabilities than
LDAP has, faster, proper sorted subset queries, etc. Nevertheless maintaining and index
has the disadvantage that modifications that happen to our backends don't find their way
to the index at all.

For LDAP, there's a tool called *clacks-ldap-monitor* in the tools directory. It uses the
same configuration like the agent does and needs to be started in the background - or by
the *supervisord*.

If you use it, please add a section to the Clacks configuration::

  [backend-monitor]
  modifier = cn=agent,dc=example,dc=net
  audit-log = /var/log/ldap-audit.log

============ ==========================================================================
Key          Description
============ ==========================================================================
modifier     Account that does modifications in the LDAP in behalf of the clacks-agent.
audit-log    LDAP auditlog
============ ==========================================================================

In your OpenLDAP configuration you need to load the *auditlog* overlay and configure it
to log to */var/log/ldap-audit.log*.
