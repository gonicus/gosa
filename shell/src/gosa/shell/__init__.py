# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The Clacks shell can be called in different ways.

 * Interactive mode::

     $ gosa-cli
     Connected to https://gosa.example.net/rpc
     Username [cajus]:
     Password:
     GOsa service shell. Use Ctrl+D to exit.
     >>>

   You're presented a python prompt which can be used
   to get the list of commands using the *proxy* object::

     >>> gosa.help()
     createDistribution()
         Create a new distribution based on type, mirror and installation
         method

     getTimezones(self)
         Get supported time zones
     ...

   The *proxy* object acts as a proxy for the commands, so you can i.e. start
   asking for the registered Clacks clients ::

     >>> getClients()
     {u'2daf7cbf-75c2-4ea3-bfec-606fe9f07051': {
         u'received': 1313159425.0,
         u'name': u'dyn-10'},
      u'eb5e72d4-c53f-4612-81a3-602b14a8da69': {
          u'received': 1313467229.0,
          u'name': u'ws-2'},
      u'4f0dbdaa-05de-4632-bcba-b6fe8a9e2e09': {
          u'received': 1313463859.0,
          u'name': u'dyn-85'}}

   or just do simple multi-liners::

     >>> for client, info in getClients().items():
     ...   print info['name']
     ...
     dyn-10
     ws-2
     dyn-85

   You can leave the interactive mode by pressing "Ctrl+D".

"""
__import__('pkg_resources').declare_namespace(__name__)
__version__ = __import__('pkg_resources').get_distribution('gosa.shell').version
