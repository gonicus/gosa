# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
Overview
========

The *client* module bundles the client daemon and a couple code modules
needed to run it. The client itself is meant to be extended by plugins
using the :class:`gosa.common.components.plugin.Plugin` interface.
When starting up the system, the client looks for plugins in the setuptools
system and registers them into to the :class:`gosa.common.components.registry.PluginRegistry`.

After the *PluginRegistry* is ready with loading the modules, it orders
them by priority and loads them in sorted order.

The client is now in a state where it enters the main loop by sending
an AMQP ``ClientAnnounce`` event to be recognized by agents.

To provide services an ordinary client will load a couple of modules
exposing functionality to the outside world. Here are some of them:

 * :class:`gosa.client.command.CommandRegistry` inspects all loaded modules
   for the :meth:`gosa.common.components.command.Command` decorator
   and registers all decorated methods to be available thru the CommandRegistry
   dispatcher.

 * :class:`gosa.client.amqp_service.AMQPService` joins to the qpid broker
   federation and provides methods to *speak* with the bus.


This happens automatically depending on what's registered on the
``[client.module]`` setuptools entrypoint.

The client will send a **ClientLeave** event when shutting down.

If you're looking for documentation on how to write plugins, please take a look
at the :ref:`Plugin section<plugins>`.

Joining clients
===============

Before a GOsa client can connect to the AMQP bus, it needs to be known to
the infrastructure - which is done by *joining* the client. The process
of joining is like joining a windows client to a domain: you need someone
with adequate permission to do that.

While the *gosa-join* binary will do this for you, it is possible to extend
it to use i.e. a graphical join dialog. At present, we provide a ncurses
and a readline based join mechanism. More can be added using the setuptools
``join.module`` entrypoint. For more information, take a look at the
:mod:`gosa.client.join` and :class:`gosa.client.plugins.join.join_method` documentation.

Using the binaries
==================

The gosa-client binary gets installed when you run the setup process. It
has a couple of command line arguments:

    .. program-output::  gosa-client --help
       :prompt:

.. note::

   Take a look at the :ref:`quickstart <quickstart>` to see how the client is
   controlled.

For production environments, just start the client using the *supervisor*
package.

"""
__version__ = __import__('pkg_resources').get_distribution('gosa.client').version
__import__('pkg_resources').declare_namespace(__name__)
