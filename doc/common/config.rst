Configuration handling
======================

.. automodule:: gosa.common.config
   :members:

--------

The configuration module handles a couple of default configuration values
of the ``[core]`` section:

============= =============
Key           Description
============= =============
foreground    Run in daemon mode or not
pidfile       Path to the PID file when running in daemon mode
umask         Umask when running in daemon mode
user          User to become when running in daemon mode
group         Group to become when running in daemon mode
workdir       Change to this directory when running in daemon mode
loglevel      Level where logging starts
profile       Save profiling information
log           Log target (stderr, syslog, file)
logfile       If log="file" this is the path to the logfile
id            Unique ID of this node
domain        Which domain this node will be part of
============= =============

Here is an example::

   [core]
   loglevel = DEBUG
   log = file
   logfile = /var/log/gosa/backend.log
   profile = False
   id = amqp
   user = gosa
   group = gosa
