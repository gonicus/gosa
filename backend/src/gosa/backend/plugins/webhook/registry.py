# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import logging
import uuid
import os

import pkg_resources
import zope
from lxml import objectify
from requests import HTTPError

from zope.interface import implementer
import hmac
from gosa.backend.exceptions import ACLException, WebhookException
from gosa.common import Environment
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.components import PluginRegistry
from gosa.common.gjson import loads, dumps
from gosa.common.handler import IInterfaceHandler
from gosa.common.hsts_request_handler import HSTSRequestHandler
from gosa.common.utils import N_


# Register the errors handled  by us
C.register_codes(dict(
    NO_REGISTERED_WEBHOOK_HANDLER=N_("No webhook handler for content type '%(topic)s' found")
))


@implementer(IInterfaceHandler)
class WebhookRegistry(Plugin):
    _priority_ = 0
    _target_ = "core"
    __hooks = {}
    __handlers = {}

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

        # load registered handlers
        for entry in pkg_resources.iter_entry_points("gosa.webhook_handler"):
            module = entry.load()
            self.__handlers[entry.name] = module()

    def stop(self):
        settings_file = self.env.config.get("webhooks.registry-store", "/var/lib/gosa/webhooks")
        with open(settings_file, 'w') as f:
            f.write(dumps(self.__hooks))

    def get_webhook_url(self):
        return "%s/hooks/" % PluginRegistry.getInstance("HTTPService").get_gui_uri()[0]

    @Command(needsUser=True, __help__=N_("Registers a webhook for a content type"))
    def registerWebhook(self, user, sender_name, content_type):
        topic = "%s.webhook.%s" % (self.env.domain, content_type)
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "e"):
            self.__log.debug("user '%s' has insufficient permissions to register webhook for content type %s" % (user, content_type))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic))

        if content_type not in self.__handlers:
            raise WebhookException(C.make_error('NO_REGISTERED_WEBHOOK_HANDLER', content_type))

        if content_type not in self.__hooks:
            self.__hooks[content_type] = {}

        if sender_name not in self.__hooks[content_type]:
            self.__hooks[content_type] = bytes(uuid.uuid4(), 'ascii')

        return self.get_webhook_url(), self.__hooks[content_type][sender_name]

    @Command(needsUser=True, needsSession=True, __help__=N_("Unregisters a webhook"))
    def unregisterWebhook(self, user, sender_name, content_type):
        if content_type in self.__hooks and sender_name in self.__hooks[content_type]:
            del self.__hooks[content_type][sender_name]

    def get_token(self, content_type, sender_name):
        if content_type not in self.__hooks or sender_name not in self.__hooks[content_type]:
            return None
        else:
            return self.__hooks[content_type][sender_name]

    def get_handler(self, content_type):
        """
        Get the registered handler for the given content type
        :param content_type:
        :return: found handler or none
        """
        if content_type in self.__handlers:
            return self.__handlers[content_type]
        return None


class WebhookReceiver(HSTSRequestHandler):
    """
    This is the global webhook receiver. It checks the validity of the incoming data and forwards
    it to the registered handler for the received content type.
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
        content_type = self.request.headers.get('Content-Type')

        registry = PluginRegistry.getInstance("WebhookRegistry")
        # verify content
        token = registry.get_token(content_type, self.sender)
        # no token, not allowed
        if token is None:
            raise HTTPError(401)

        # as the content is bytes the token needs to be converted to bytes to
        token = bytes(token, 'ascii')

        # wrong signature, not allowed
        if not self._verify_signature(self.request.body, token):
            raise HTTPError(401)

        # forward to the registered handler
        handler = registry.get_handler(content_type)
        if handler is None:
            raise HTTPError(401)

        handler.handleRequest(self.request)

    def _verify_signature(self, payload_body, token):
        h = hmac.new(token, msg=payload_body, digestmod="sha512")
        signature = 'sha1=' + h.hexdigest()
        return hmac.compare_digest(self.signature, signature)


class WebhookEventReceiver(object):
    """ Webhook handler for gosa events"""

    def handleRequest(self, request):
        # read and validate event
        xml = objectify.fromstring(request.body, PluginRegistry.getEventParser())
        # forward incoming event to internal event bus
        zope.event.notify(xml)
