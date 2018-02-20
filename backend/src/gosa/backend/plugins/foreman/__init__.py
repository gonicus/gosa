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
for the `Foreman host event` type. And another webhook for the `Foreman hook event` type. 
If you open the new webhooks you can see the informations you need to configure
the *Smart Proxy webhook realm provider* and the hook script.

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

Create the directory structure for the hooks

.. code-block:: bash

    mkdir -p /usr/share/foreman/config/hooks/host/managed/{after_destroy,after_commit}
    mkdir -p /usr/share/foreman/config/hooks/host/discovered/{after_destroy,after_commit} 
    mkdir -p /usr/share/foreman/config/hooks/hostgroup/{after_destroy,after_commit}
    mkdir -p /usr/share/foreman/config/hooks/operatingsystem/{after_destroy,after_commit}  

    # Copy the hook script
    cp backend/src/gosa/backend/plugins/foreman/gosa_integration.py /usr/share/foreman/config/hooks/
    
    # create symlinks
    ln -s /usr/share/foreman/config/hooks/gosa_integration.py /usr/share/foreman/config/hooks/host/managed/after_commit
    ln -s /usr/share/foreman/config/hooks/gosa_integration.py /usr/share/foreman/config/hooks/host/managed/after_destroy
    
    ln -s /usr/share/foreman/config/hooks/gosa_integration.py /usr/share/foreman/config/hooks/host/discovered/after_commit
    ln -s /usr/share/foreman/config/hooks/gosa_integration.py /usr/share/foreman/config/hooks/host/discovered/after_destroy
    
    ln -s /usr/share/foreman/config/hooks/gosa_integration.py /usr/share/foreman/config/hooks/hostgroup/after_commit
    ln -s /usr/share/foreman/config/hooks/gosa_integration.py /usr/share/foreman/config/hooks/hostgroup/after_destroy
    
    ln -s /usr/share/foreman/config/hooks/gosa_integration.py /usr/share/foreman/config/hooks/operatingsystem/after_commit
    ln -s /usr/share/foreman/config/hooks/gosa_integration.py /usr/share/foreman/config/hooks/operatingsystem/after_destroy
    
Open the `/usr/share/foreman/config/hooks/gosa_integration.py` script and change the setting according to the created webhook in GOsa³
for the `Foreman hook event`.

.. code-block:: python

    # Gosa settings
    GOSA_SERVER = "https://<gosa-hostname>"
    GOSA_PORT = 8000
    HTTP_X_HUB_SENDER = "foreman-hook"
    SECRET = "<your secret>"


"""