Backend plugins
===============

The backend supports two kinds of plugins. Plain plugins normally provide commands
to the outside world, which are exposed by the *@Command* decorator. Handler plugins
have *serve*/*stop* methods and a *priority*: they're started by the backend on
service startup.

Plain plugins
-------------

Plain plugins just need to inherit from :class:`clacks.common.components.plugin.Plugin`
and make use of :meth:`clacks.common.components.command.Command`. Additionally, they've
to specify their target queue - :ref:`see agent queues <agent-queues>`.

Use the **tools/clacks-plugin-skell** command to get a Clacks agent plugin skeleton and
take a look at the *main.py* file::

    # -*- coding: utf-8 -*-
    import gettext
    from clacks.common import Environment
    from clacks.common.components import Command, Plugin
    
    # Load gettext
    t = gettext.translation('messages', resource_filename("sample", "locale"), fallback=True)
    _ = t.ugettext
    
    
    class SamplePlugin(Plugin):
        _target_ = 'sample'
    
        def __init__(self):
            self.env = Environment.getInstance()
    
        @Command(__help__=N_("Return a pre-defined message to the caller"))
        def hello(self, name="unknown"):
            self.env.log.debug("Now calling 'hello' with parameter %s" % name)
            return _("Hello %s!") % name

It shows a very minimal sample plugin which provides the command *hello* to
the Clacks agents *CommandRegistry* - which is callable for users later on. You
can see a couple of things that are common to all plugins:

 * they import *Command* and *Plugin* from the :mod:`clacks.common.components`
 * they optionally import the *Environment* if there's a need for it (i.e.
   logging or config management)
 * they optionally initialize the gettext module for i18n support
 * they define a '_target_' queue where the plugin is registered to
   
Just modify the code to your needs. After that you can do a test deployment
using::

  $ ./setup.py develop

and *restart* your Clacks agent to let it notice the newly created plugin. From
now on you can use the *hello* command from the shell or one of the proxies - whatever
makes sense for you.


Handler plugins
---------------

Handler plugins differ from plain plugins because they provide *something*
which needs to be started when the agent starts up. Maybe this is a web service
or a special scheduler service. To enable this, you need to specify the ::

    implements(IInterfaceHandler)

keywords in top of the class definition, and optionally provide a priority
which indicates the time of 'serving'. Bigger values mean later, smaller mean
earlier. You can maintain service dependencies this way if you need to.

Here's the modified snipped from above to run as a handler::

    # -*- coding: utf-8 -*-
    import gettext
    from zope.interface import implements
    from clacks.common import Environment
    from clacks.common.handler import IInterfaceHandler
    from clacks.common.components import Command, Plugin
    
    # Load gettext
    t = gettext.translation('messages', resource_filename("sample", "locale"), fallback=True)
    _ = t.ugettext
    
    
    class SampleHandler(Plugin):
        implements(IInterfaceHandler)

        _target_ = 'sample'
        _priority_ = 99
    
        def serve(self):
           # What ever you need to do to serve stuff
           pass
    
        def stop(self):
           # What ever you need to do to stop serving stuff
           pass
    
        @Command(__help__=N_("Return a pre-defined message to the caller"))
        def hello(self, name="unknown"):
            return _("Hello %s!") % name
