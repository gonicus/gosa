# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import copy
import logging
import uuid
import os
import re

import pkg_resources
import shutil
import zope
from lxml import objectify
from tornado.web import HTTPError

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
    NO_REGISTERED_WEBHOOK_HANDLER=N_("No webhook handler for mime type '%(topic)s' found"),
    EXISTING_WEBHOOK_HANDLER=N_("There is already a webhook registered for mime-type '%(topic)s' with name '%(name)s'"),
    INVALID_WEBHOOK_SENDER_NAME=N_("Invalid sender name syntax: only ASCII letters and optional hyphens are allowed"),
    INVALID_WEBHOOK_MIME_TYPEE=N_("Invalid mime-type syntax: only alphanumeric, . (dot), + (plus) and / (slash) characters are allowed")
))


@implementer(IInterfaceHandler)
class WebhookRegistry(Plugin):
    _priority_ = 10
    _target_ = "core"
    __handlers = {}
    settings = None
    path_separator = '###'

    name_check = re.compile("^[a-zA-Z\-]+$")
    mime_type_check = re.compile("^[\w\.\+\/\-]+$")

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing webhook registry")

    def serve(self):
        self.settings = PluginRegistry.getInstance("SettingsRegistry").get_handler("gosa.webhooks")

        # load registered handlers
        for entry in pkg_resources.iter_entry_points("gosa.webhook_handler"):
            module = entry.load()
            self.register_handler(entry.name, module())

        # override for development mode
        monitor_key = self.env.config.get("webhooks.ldap_monitor_token")
        if monitor_key:
            path = 'application/vnd.gosa.event+xml###backend-monitor'
            self.settings.set(path, monitor_key, temporary=True)

    def register_handler(self, mime_type, handler):
        if not hasattr(handler, "type"):
            self.log.error("Handler for mime-type %s has no type attribute. Skipping registration." % mime_type)
        else:
            self.__handlers[mime_type] = handler

    def unregister_handler(self, mime_type):
        if mime_type in self.__handlers:
            del self.__handlers[mime_type]

    def stop(self):
        for clazz in self.__handlers.values():
            del clazz

    @Command(__help__=N_("Get the webhook receiver URL"))
    def getWebhookUrl(self):
        return "%s/hooks/" % PluginRegistry.getInstance("HTTPService").get_gui_uri()[0]

    @staticmethod
    def get_path(mime_type, sender_name):
        return '%s%s%s' % (mime_type, WebhookRegistry.path_separator, sender_name)

    @staticmethod
    def split_path(path):
        parts = path.split(WebhookRegistry.path_separator)
        return parts[0], parts[1]

    @Command(needsUser=True, __help__=N_("Registers a webhook for a mime-type"))
    def registerWebhook(self, user, sender_name, mime_type):
        topic = "%s.webhook.%s" % (self.env.domain, mime_type)
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "e"):
            self.log.debug("user '%s' has insufficient permissions to register webhook for mime-type %s" % (user, mime_type))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic))

        # check sender_name syntax
        if not self.name_check.match(sender_name):
            raise WebhookException(C.make_error('INVALID_WEBHOOK_SENDER_NAME'))

        # check mime-type syntax
        if not self.mime_type_check.match(mime_type):
            raise WebhookException(C.make_error('INVALID_WEBHOOK_MIME_TYPE'))

        # check for duplicates
        if mime_type not in self.__handlers:
            raise WebhookException(C.make_error('NO_REGISTERED_WEBHOOK_HANDLER', mime_type))

        path = self.get_path(mime_type, sender_name)
        if self.settings.has(path):
            raise WebhookException(C.make_error('EXISTING_WEBHOOK_HANDLER', mime_type, name=sender_name))

        self.settings.set(path, str(uuid.uuid4()))

        return self.getWebhookUrl(), self.settings.get(path)

    @Command(needsUser=True, __help__=N_("Unregisters a webhook"))
    def unregisterWebhook(self, user, sender_name, mime_type):
        path = self.get_path(mime_type, sender_name)
        if self.settings.has(path):
            self.settings.set(path, None)

    @Command(needsUser=True, __help__=N_("Shows all mime-types a webhook can be registered for"))
    def getAvailableMimeTypes(self, user):
        types = {}
        for mime_type, handler in self.__handlers.items():
            types[mime_type] = handler.type
        return types

    def get_token(self, mime_type, sender_name):
        if mime_type is None or sender_name is None:
            return None

        path = self.get_path(mime_type, sender_name)
        if self.settings.has(path):
            return self.settings.get(path)
        else:
            return None

    def get_handler(self, mime_type):
        """
        Get the registered handler for the given mime type
        :param mime_type:
        :return: found handler or none
        """
        if mime_type in self.__handlers:
            return self.__handlers[mime_type]
        return None


class WebhookSettingsHandler(object):
    """
    Handles registered webhook settings
    """
    __hooks = {}
    __temporary = []

    def __init__(self):
        self.env = Environment.getInstance()
        settings_file = self.env.config.get("webhooks.registry-store", "/var/lib/gosa/webhooks")
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                self.__hooks = loads(f.read())

    def stop(self):
        self.save()

    def save(self):
        settings_file = self.env.config.get("webhooks.registry-store", "/var/lib/gosa/webhooks")
        to_save = copy.deepcopy(self.__hooks)
        for mime_type, sender_name in self.__temporary:
            if mime_type in to_save and sender_name in to_save[mime_type]:
                del to_save[mime_type][sender_name]
                if len(to_save[mime_type].keys()) == 0:
                    del to_save[mime_type]

        # backup old file
        shutil.copyfile(settings_file, "%s.backup" % settings_file)
        with open(settings_file, 'w') as f:
            f.write(dumps(to_save))

    def set(self, path, value, temporary=False):
        mime_type, sender_name = WebhookRegistry.split_path(path)
        if value is None:
            # delete webhook
            if mime_type in self.__hooks and sender_name in self.__hooks[mime_type]:
                del self.__hooks[mime_type][sender_name]
                if len(self.__hooks[mime_type].keys()) == 0:
                    del self.__hooks[mime_type]
                    self.save()
        else:
            if mime_type not in self.__hooks:
                self.__hooks[mime_type] = {}

            self.__hooks[mime_type][sender_name] = value
            self.save()
            if temporary:
                self.__temporary.append((mime_type, sender_name))

    def has(self, path):
        mime_type, sender_name = WebhookRegistry.split_path(path)
        return mime_type in self.__hooks and sender_name in self.__hooks[mime_type]

    def get(self, path):
        mime_type, sender_name = WebhookRegistry.split_path(path)
        if mime_type in self.__hooks and sender_name in self.__hooks[mime_type]:
            return self.__hooks[mime_type][sender_name]
        else:
            return None

    def get_config(self):
        return {"read_only": True, "name": N_("Webhooks")}

    def get_item_infos(self):
        """
        Returns all configurable items including information about type etc.
        :return dict:
        """
        infos = {}
        for mime_type in self.__hooks:
            for sender_name in self.__hooks[mime_type]:
                infos[WebhookRegistry.get_path(mime_type, sender_name)] = {
                    "type": "string",
                    "title": sender_name,
                    "value": self.__hooks[mime_type][sender_name]
                }
        return infos


class WebhookReceiver(HSTSRequestHandler):
    """
    This is the global webhook receiver. It checks the validity of the incoming data and forwards
    it to the registered handler for the received mime type.
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
        mime_type = self.request.headers.get('Content-Type')

        registry = PluginRegistry.getInstance("WebhookRegistry")
        # verify content
        token = registry.get_token(mime_type, self.sender)
        # no token, not allowed
        if token is None:
            raise HTTPError(401)

        # as the content is bytes the token needs to be converted to bytes to
        token = bytes(token, 'ascii')

        # wrong signature, not allowed
        if not self._verify_signature(self.request.body, token):
            raise HTTPError(401)

        # forward to the registered handler
        handler = registry.get_handler(mime_type)
        if handler is None:
            # usually this code is unreachable because if there is no registered handler, there is no token
            raise HTTPError(401)

        handler.handle_request(self)

    def _verify_signature(self, payload_body, token):
        if self.signature is None:
            return False

        h = hmac.new(token, msg=payload_body, digestmod="sha512")
        signature = 'sha1=' + h.hexdigest()
        return hmac.compare_digest(self.signature, signature)


class WebhookEventReceiver(object):
    """ Webhook handler for gosa events (Content-Type: application/vnd.gosa.event+xml) """

    def __init__(self):
        self.type = N_("GOsa events")
        self.log = logging.getLogger(__name__)

    def handle_request(self, requestHandler):
        # read and validate event
        self.log.debug('Received event via webhook: %s' % requestHandler.request.body)
        xml = objectify.fromstring(requestHandler.request.body, PluginRegistry.getEventParser())
        # forward incoming event to internal event bus
        zope.event.notify(xml)
