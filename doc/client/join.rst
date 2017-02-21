Domain join
===========

As stated in the overview of the Clacks client documentation, a client has to be
joined to the Clacks domain in order to participate in the AMQP bus functionality.
In the moment you just need a non 'machine account' to join a new client to the
domain, because ACLs are not implemented yet.

If your client has not been joined, you've to do this by starting the *gosa-join* command::

   Please enter the credentials of an administrative user to join this client.
   (Press Ctrl-C to cancel)

   User name: admin
   Password: *******

This will create an automatic client configuration, which is needed to start the
Clacks client itself.

.. note::

   The process of joining a client transfers the computers unique device-uuid
   to the server. Because it is only readable by root, it can be used later on
   to pass an initial encrypted secret to the client after a reboot happened.

----

.. autoclass:: gosa.client.plugins.join.methods.join_method
   :members:
