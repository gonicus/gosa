# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import base64
import hashlib
import logging
import uuid
import os
import zope
from lxml import objectify
from requests import HTTPError

from zope.interface import implementer
import hmac
from gosa.backend.exceptions import ACLException
from gosa.common import Environment
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.components import PluginRegistry
from gosa.common.gjson import loads, dumps
from gosa.common.handler import IInterfaceHandler
from gosa.common.hsts_request_handler import HSTSRequestHandler
from gosa.common.utils import N_, stripNs


@implementer(IInterfaceHandler)
class WebhookRegistry(Plugin):
    _priority_ = 0
    _target_ = "core"
    __hooks = {}

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing webhook registry")

    def serve(self):
        # load hooks
        settings_file = self.env.config.get("webhooks.registry-store", "/var/lib/gosa/webhooks")
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                self.__hooks = loads(f.read())

    def stop(self):
        settings_file = self.env.config.get("webhooks.registry-store", "/var/lib/gosa/webhooks")
        with open(settings_file, 'w') as f:
            f.write(dumps(self.__hooks))

    def get_webhook_url(self):
        return "%s/hooks/" % PluginRegistry.getInstance("HTTPService").get_gui_uri()[0]

    @Command(needsUser=True, __help__=N_("Registers a webhook for an event type"))
    def registerWebhook(self, user, sender_name, event_name):
        topic = "%s.event.%s" % (self.env.domain, event_name)
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "e"):
            self.__log.debug("user '%s' has insufficient permissions to receive events of type %s" % (user, event_name))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic))

        if event_name not in self.__hooks:
            self.__hooks[event_name] = {}

        if sender_name not in self.__hooks[event_name]:
            self.__hooks[event_name][sender_name] = bytes(uuid.uuid4(), 'ascii')

        return self.get_webhook_url(), self.__hooks[event_name][sender_name]

    @Command(needsUser=True, needsSession=True, __help__=N_("Registers a temporary upload path"))
    def unregisterWebhook(self, user, sender_name, event_name):
        if event_name in self.__hooks and sender_name in self.__hooks[event_name]:
            del self.__hooks[event_name][sender_name]

    def get_token(self, event_name, sender_name):
        if event_name not in self.__hooks or sender_name not in self.__hooks[event_name]:
            return None
        else:
            return self.__hooks[event_name][sender_name]


class WebhookReceiver(HSTSRequestHandler):
    """
    This is the single endpoint for all incoming events via webhooks
    """
    signature = None
    sender = None
    _xsrf = None

    def initialize(self):
        self.sender = self.request.headers.get('HTTP_X_HUB_SENDER')
        self.signature = self.request.headers.get('HTTP_X_HUB_SIGNATURE')

    # disable xsrf feature
    def check_xsrf_cookie(self):
        pass

    def post(self, path):
        data = self.request.body
        xml = objectify.fromstring(data, PluginRegistry.getEventParser())
        event_name = stripNs(xml.xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag)
        token = bytes(PluginRegistry.getInstance("WebhookRegistry").get_token(event_name, self.sender), 'ascii')

        # no token, not allowed
        if token is None:
            raise HTTPError(401)

        # wrong signature, not allowed
        if not self.__verify_signature(data, token):
            raise HTTPError(401)

        # forward incoming event to internal event bus
        zope.event.notify(xml)

    def __verify_signature(self, payload_body, token):
        h = hmac.new(token, msg=payload_body, digestmod="sha512")
        signature = 'sha1=' + h.hexdigest()
        return hmac.compare_digest(self.signature, signature)
