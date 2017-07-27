# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

__import__('pkg_resources').declare_namespace(__name__)

"""
Foreman integration
===================

Prerequisites
-------------

* Foreman installation with following plugins installed
  * Smarty Proxy - Webhook realm provider (https://github.com/gonicus/smart_proxy_realm_webhook)
  * foreman_hooks (https://github.com/theforeman/foreman_hooks)
* A special user account in Foreman for GOsa³ 

Configuration
-------------

**In GOsa³**
You have to create a webhook with a sender name of your choice (e.g. `foreman` or `foreman-sp`) 
for the `Foreman host event` type. If you open the new webhook you see the informations you need to configure
the *Smart Proxy webhook realm provider*

GOsa³ needs credentials to access the foreman API. Please add these credentials to you GOsa³ config file in the *foreman*-section
and restart GOsa³ afterwards.

.. code-block:: ini
    
    [foreman]
    host = https://<foreman-host>/api
    user = <foreman-username>
    password = <foreman-password>


**In Foreman**
Use the configuration settings shown in GOsa³ to configure the smart proxy plugin. You can find the configurations file here:
*/etc/foreman-proxy/settings.d/realm_webhook.yml*. Restart the *foreman-proxy* service.

.. TODO::

    Describe how to install the foreman hooks for hosts and hostgroups.


"""