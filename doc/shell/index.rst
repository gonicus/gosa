Shell and scripting
===================

While the Clacks core is all python and you can simply script complex tasks 
directly in python, there's sometimes the need to trigger calls from
within the ordinary shell - maybe inside a *bash* script. For that reason,
there's the *gosa-shell* binary, which can assist you in this case.


Using the shell
^^^^^^^^^^^^^^^

.. automodule:: gosa.shell
   :members:

Using the API
^^^^^^^^^^^^^

Almost all parts of the API are accessible thru the command proxies or
the event methods. Please take a look at

 * the AMQP service proxy: :class:`gosa.common.components.amqp_proxy.AMQPServiceProxy`
 * the HTTP/JSONRPC proxy: :class:`gosa.common.components.jsonrpc_proxy.JSONServiceProxy`
 * :ref:`using events <events>`

for more information.
