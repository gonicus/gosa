Plugins
=======

This section contains documentation for available Clacks plugins. These may
come as standalone plugins or may be included in the core Clacks modules.
If you find missing plugins, please send patches to these documentation files.

Backend plugins
---------------

.. toctree::
   :maxdepth: 2

   backend/goto
   backend/gosa
   backend/password
   backend/posix
   backend/misc
   backend/samba
   backend/user
   backend/foreman


Client plugins
--------------

.. toctree::
   :maxdepth: 2

   client/dbus
   client/goto
   client/inventory
   client/notify


DBUS plugins
------------

.. toctree::
   :maxdepth: 2

   dbus/shell
   dbus/wakeonlan
   dbus/notify
   dbus/services


Plugin development
==================

Basically there are four plugin types that are used inside of Clacks. Two of
them are *backend* plugins - namely handlers and ordinary plugins, one flavor
of *client* plugins and one flavor of *dbus* plugins.

.. _plugins:

In order to help with quick plugin templating, there's a helper script **tools/gosa-plugin-skel**
which asks a couple of questions and generates a quickstart for you::

  $ tools/gosa-plugin-skel
  Generate plugin skeleton. Please provide some information:
  
  Plugin name (must be [a-z][a-z0-9]+): sample
  Plugin type (backend, client, dbus): backend
  Version: 1.0
  Authors name: Cajus Pollmeier
  Authors email: pollmeier@gonicus.de

  Done. Please check out the 'sample' directory.
  $

Here's the resulting directory structure::

  $ find sample
  sample
  sample/README
  sample/setup.cfg
  sample/setup.py
  sample/src
  sample/src/gosa
  sample/src/gosa/__init__.py
  sample/src/gosa/backend
  sample/src/gosa/backend/__init__.py
  sample/src/gosa/backend/plugins
  sample/src/gosa/backend/plugins/__init__.py
  sample/src/gosa/backend/plugins/sample
  sample/src/gosa/backend/plugins/sample/locale
  sample/src/gosa/backend/plugins/sample/__init__.py
  sample/src/gosa/backend/plugins/sample/tests
  sample/src/gosa/backend/plugins/sample/main.py

**Topics:**

.. toctree::
   :maxdepth: 2

   backend/index
   client/index
   dbus/index

