Event handling
==============

.. _events:

Clacks utilizes the XML queue of *QPID*, which enables us to send and
filter XML encoded events. Using *XQuery*, we can filter for special
properties inside of the event description.

The following two examples show how to create a standalone sender
and receiver for a simple phone status notification - that may be used
for whatever you can imagine.

First, you need to define an event description in XML-schema style and
place it in ``clacks/common/data/events``:


.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <schema targetNamespace="http://www.gonicus.de/Events" elementFormDefault="qualified" 
            xmlns="http://www.w3.org/2001/XMLSchema" xmlns:e="http://www.gonicus.de/Events">
      <complexType name="PhoneStatus">
        <annotation>
          <documentation>
            The PhoneStatus event is emitted when the asterisk AMI
            listener detects a status change.
          </documentation>
        </annotation>
        <all>
          <element name="CallerId" type="string"></element>
          <element name="ReceiverId" type="string"></element>
          <element name="Status" type="string"></element>
        </all>
      </complexType>
      <element name="PhoneStatus" type="e:PhoneStatus"></element>
    </schema>

After this has been done, the Clacks agent needs to be restarted in the
moment to reload the XSD information. Now we'll write a receiver for
that::

	#!/usr/bin/env python
	# -*- coding: utf-8 -*-
	
	from clacks.common.components import AMQPEventConsumer
	from lxml import etree
	
	# Event callback
	def process(data):
	    print(etree.tostring(data, pretty_print=True))
	
	# Create event consumer
	consumer = AMQPEventConsumer("amqps://admin:secret@localhost/org.clacks",
	            xquery="""
	                declare namespace f='http://www.gonicus.de/Events';
	                let $e := ./f:Event
	                return $e/f:PhoneStatus
	            """,
	            callback=process)
	
	# Main loop, process threads
	try:
	    while True:
	        consumer.join()
	
	except KeyboardInterrupt:
	    del consumer
	    exit(0)

This one will connect to the AMQP service and call the ``process`` callback
if there's something interesting. Just start that one on one shell and
open another one to send a signal using :meth:`gosa.backend.command.CommandRegistry.sendEvent`::

	from clacks.common.components import AMQPServiceProxy
	from clacks.common.event import EventMaker
	from lxml import etree
	
	# Connect to AMQP bus
	proxy = AMQPServiceProxy('amqp://admin:secret@localhost/org.clacks')
	
	# Example of building event without direct strings...
	e = EventMaker()
	status = e.Event(
	    e.PhoneStatus(
	        e.CallerId("012345"),
	        e.ReceiverId("12343424"),
	        e.Status("busy")
	    )
	)
	
	# ... which in turn needs to be converted to a string
	status = etree.tostring(status, pretty_print=True)
	
	# Send it
	proxy.sendEvent(status)

If you start that script you can receive the message using the
receiver.

.. note::

   Events are just one way, fire and forget. If there is no one who's
   listening for that event, it's lost.


Available events
================

Clacks comes with a set of predefined events and modules itself can
provide new events. Here's a short overview:

+---------------------+-----------+------------------------------------------------------------+
|Event name           |Module     |Description                                                 |
+=====================+===========+============================================================+
|AsteriskNotification |Asterisk   |Sends information about queue usage, allows status tracking.|
+---------------------+-----------+------------------------------------------------------------+
|ClientAnnounce       |GOto       |Sent when a client is coming up, contains information about |
|                     |           |the client and it's methods.                                |
+---------------------+-----------+------------------------------------------------------------+
|ClientLeave          |GOto       |Sent when a client is about to shut down.                   |
+---------------------+-----------+------------------------------------------------------------+
|ClientPoll           |Core       |Sent by the agent if it's "alone" and has no way to find    |
|                     |           |it's assigned clients. All clients reply with a newly sent  |
|                     |           |ClientAnnounce to this event.                               |
+---------------------+-----------+------------------------------------------------------------+
|CollectD             |CollectD   |Experimental collectd event.                                |
+---------------------+-----------+------------------------------------------------------------+
|NodeAnnounce         |Core       |Sent by an agent when starting up.                          |
+---------------------+-----------+------------------------------------------------------------+
|NodeCapabilities     |Core       |Sent by an agent when starting up, containing a brief       |
|                     |           |list of information about the agent itself.                 |
+---------------------+-----------+------------------------------------------------------------+
|NodeLeave            |Core       |Sent by an agent when shutting down.                        |
+---------------------+-----------+------------------------------------------------------------+
|NodeStatus           |Core       |Sent regulary by an agent in order to do pseudo load        |
|                     |           |balancing for HTTP connections.                             |
+---------------------+-----------+------------------------------------------------------------+
|UserSession          |GOto       |Sent if a user logs onto the client.                        |
+---------------------+-----------+------------------------------------------------------------+
|PuppetReport         |libinst    |Sent after a client puppet run.                             |
+---------------------+-----------+------------------------------------------------------------+
