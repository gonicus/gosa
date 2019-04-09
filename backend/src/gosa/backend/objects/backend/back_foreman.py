# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import datetime
import json
import threading

from threading import Thread
import logging
import requests
from requests.auth import HTTPBasicAuth

from gosa.backend.routes.sse.main import SseHandler
from gosa.common.event import EventMaker
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C

from gosa.backend.objects.backend import ObjectBackend
from gosa.common import Environment
from logging import getLogger

from gosa.common.gjson import dumps
from gosa.backend.exceptions import ObjectException


"""
Backend Attributes:
-------------------

* `type`: object type in foreman (e.g. hosts, hostgroups) 
* `mapping`: maps foreman attribute names to GOsa attribute names

.. code-block: xml
    :caption: Example configuration for foreman host objects

    <Backend type="hosts" _uuidAttribute="cn" _uuidSourceAttribute="name" needs="status">Foreman</Backend>

The Foreman backend needs to now the object type and the id to identify an object.
``_uuidSourceAttribute`` is optional and specifies the attribute name where the ID value can be found
in the foreman API response. If not specified the backend assumes that ``_uuidSourceAttribute == _uuidAttribute``.
These two settings are used to generate the API URL to access the object in foreman.
In this example the URL for HTTP-requests would be <foreman-host>/api/hosts/<cn>.

``needs`` is optional and defines attribute names which values the backend needs to know to perform its task.

*Example:*

    The ForemanHost needs to know the value of the status attribute. If status="discovered" the backend needs to talk to the API
    endpoint "discovered_hosts" instead of "hosts". 
"""

# Register the errors handled  by us
C.register_codes(dict(
    FOREMAN_OBJECT_NOT_FOUND=N_("The requested foreman object does not exist: '%(topic)s'"),
    FOREMAN_COMMUNICATION_ERROR=N_("Foreman communication error type: '%(topic)s'")
))


class Foreman(ObjectBackend):
    modifier = None

    @classmethod
    def set_modifier(cls, val):
        cls.modifier = val

    @classmethod
    def get_modifier(cls):
        return cls.modifier

    def __init__(self):
        # Initialize environment and logger
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)
        self.client = ForemanClient()
        self.e = EventMaker()

    def load(self, uuid, info, back_attrs=None, data=None, needed=None):
        """
        Loading attribute values from foreman API

        :param uuid: Unique identifier in foreman (usually the id)
        :param info: dict of all object attributes that are related to foreman {<name>: <type>}
        :param back_attrs: backend configuration from object definition
        :param data: use this data instead of querying the backend
        :param needed: optional dict with attribute_name: value needed by this backend
        :return: results returned from foreman API
        """
        self.log.debug("load: %s, %s, %s, %s" % (uuid, info, back_attrs, data))
        if data is None:
            try:
                data = self.client.get(self.get_foreman_type(needed, back_attrs), object_id=uuid)
            except ForemanBackendException as e:
                # something when wrong
                self.log.error("Error requesting foreman backend: %s" % e.message)
                data = {}
                raise e
        return self.process_data(data, info)

    def identify(self, dn, params, fixed_rdn=None):
        self.log.debug("identify: %s, %s, %s" % (dn, params, fixed_rdn))
        return False

    def identify_by_uuid(self, uuid, params):
        self.log.debug("identify_by_uuid: %s, %s" % (uuid, params))
        return False

    def exists(self, misc, needed=None):
        self.log.debug("exists: %s" % misc)
        return False

    def remove(self, uuid, data, params, needed=None, user=None):
        self.log.debug("remove: %s, %s, %s" % (uuid, data, params))
        if Foreman.modifier != "foreman":

            def runner():
                try:
                    self.client.delete(self.get_foreman_type(needed, params), uuid)
                except ForemanBackendException as ex:
                    ForemanClient.error_notify_user(ex, user)
                    raise ex

            # some changes (e.g. creating a host) trigger requests from foreman to gosa
            # so we need to run this request in a non blocking thread
            thread = Thread(target=runner)
            thread.start()

        else:
            self.log.info("skipping deletion request as the change is coming from the foreman backend")
        return True

    def retract(self, uuid, data, params, needed=None, user=None):
        self.remove(uuid, data, params, needed=needed, user=user)

    def get_foreman_type(self, data, params):
        if data is not None and "status" in data and data["status"] == "discovered":
            return "discovered_hosts"
        else:
            return params["type"]

    def extend(self, uuid, data, params, foreign_keys, dn=None, needed=None, user=None):
        """ Called when a base object is extended with a foreman object (e.g. device->foremanHost)"""
        self.log.debug("extend: %s, %s, %s, %s" % (uuid, data, params, foreign_keys))
        if Foreman.modifier != "foreman":
            object_type = self.get_foreman_type(needed, params)
            payload = self.__collect_data(data, params, object_type=object_type[:-1])

            # finally send the update to foreman
            self.log.debug("creating '%s' with '%s' to foreman" % (params["type"], payload))

            def runner():
                try:
                    result = self.client.post(type, data=payload)
                    self.log.debug("Response: %s" % result)
                except ForemanBackendException as ex:
                    ForemanClient.error_notify_user(ex, user)
                    raise ex

            # some changes (e.g. creating a host) trigger requests from foreman to gosa
            # so we need to run this request in a non blocking thread
            thread = Thread(target=runner)
            thread.start()

        else:
            self.log.info("skipping extend request as the change is coming from the foreman backend")
        return None

    def move_extension(self, uuid, new_base):
        self.log.debug("move_extension: %s, %s" % (uuid, new_base))
        pass

    def move(self, uuid, new_base, needed=None, user=None):
        self.log.debug("move: %s, %s" % (uuid, new_base))
        return True

    def create(self, base, data, params, foreign_keys=None, needed=None, user=None):
        self.log.debug("create: %s, %s, %s, %s" % (base, data, params, foreign_keys))
        return None

    def update(self, uuid, data, params, dn=None, needed=None, user=None):
        self.log.debug("update: '%s', '%s', '%s'" % (uuid, data, params))
        if Foreman.modifier != "foreman":
            object_type = self.get_foreman_type(needed, params)
            payload = self.__collect_data(data, params, object_type=object_type[:-1])
            restart = False
            # check special reboot attribute
            if object_type == "hosts" and "reboot" in payload["host"]:
                if "build" in payload["host"] and payload["host"]["build"] is True and payload["host"]["reboot"] is True:
                    # restart host after commit
                    restart = True

                del payload["host"]["reboot"]

            # finally send the update to foreman
            self.log.debug("sending update '%s' to foreman" % payload)

            def runner():
                try:
                    result = self.client.put(object_type, uuid, data=payload)
                    self.log.debug("Response: %s" % result)
                    if restart is True:
                        self.log.info("Restarting host to trigger the build")
                        self.client.put("hosts/%s" % uuid, "power", {"power_action": "reset"})
                except ForemanBackendException as ex:
                    ForemanClient.error_notify_user(ex, user)
                    raise ex

            # some changes (e.g. changing the hostgroup) trigger requests from foreman to gosa
            # so we need to run this request in a non blocking thread
            thread = Thread(target=runner)
            thread.start()
        else:
            self.log.info("skipping update request as the change is coming from the foreman backend")

    def is_uniq(self, attr, value, at_type):
        self.log.debug("is_uniq: %s, %s, %s" % (attr, value, at_type))
        return False

    def query(self, base, scope, params, fixed_rdn=None):
        self.log.debug("query: %s, %s, %s, %s" % (base, scope, params, fixed_rdn))
        return []

    def uuid2dn(self, uuid):  # pragma: nocover
        return None

    def dn2uuid(self, dn):  # pragma: nocover
        return None

    @staticmethod
    def extract_mapping(attrs):
        result = {}
        if 'mapping' in attrs:
            for key_value in attrs['mapping'].split(","):
                key, value = key_value.split(":")
                result[key] = value

        return result

    def __collect_data(self, data, params, object_type=None):
        # collect data
        if object_type is None:
            object_type = params["type"][:-1]
        payload = {
            object_type: {}
        }
        for name, settings in data.items():
            if len(settings["value"]):
                payload[object_type][name] = settings["value"][0]
            else:
                # unset value
                payload[object_type][name] = None

        return payload


class ForemanClientCache(object):
    __cache = {}
    lock = threading.Lock()

    @classmethod
    def get_cache(cls, method_name, object_type, object_id=None):
        if method_name == "get":
            cache_id = object_type
            if object_id is not None:
                cache_id += "/%s" % object_id
            if cache_id in cls.__cache:
                if cls.__cache[cache_id]["expires"] > datetime.datetime.now():
                    return cls.__cache[cache_id]["data"]
                else:
                    with cls.lock:
                        del cls.__cache[cache_id]
        return None

    @classmethod
    def add_to_cache(cls, method_name, object_type, response, object_id=None):
        if method_name == "get":
            cache_id = object_type
            if object_id is not None:
                cache_id += "/%s" % object_id
            with cls.lock:
                cls.__cache[cache_id] = {
                    "expires": datetime.datetime.now() + datetime.timedelta(hours=1),
                    "data": response
                }

    @classmethod
    def delete_cache(cls, object_type, object_id=None):
        cache_id = object_type
        if object_id is not None:
            cache_id += "/%s" % object_id
        if cache_id in cls.__cache:
            with cls.lock:
                del cls.__cache[cache_id]


class ForemanClient(object):
    """Client for the Foreman REST-API v2"""
    headers = {'Accept': 'version=2,application/json', 'Content-type': 'application/json'}
    __cookies = None
    __cache = {}

    def __init__(self, url=None):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.foreman_host = self.env.config.get("foreman.host") if url is None else url

    def __authenticate(self, method, url, kwargs):
        kwargs["auth"] = HTTPBasicAuth(self.env.config.get("foreman.user"), self.env.config.get("foreman.password"))
        response = method(url, **kwargs)
        self.__cookies = response.cookies
        return response

    def __request(self, method_name, object_type, object_id=None, data=None):
        if self.foreman_host is None:
            return {}

        cached = ForemanClientCache.get_cache(method_name, object_type, object_id=object_id)
        if cached is not None:
            self.log.debug("using cached response for %s request of %s" % (method_name, object_type))
            return cached

        url = "%s/%s" % (self.foreman_host, object_type)
        if object_id is not None:
            url += "/%s" % object_id

        method = getattr(requests, method_name)
        data = dumps(data) if data is not None else None
        self.log.debug("sending %s request with %s to %s" % (method_name, data, url))
        kwargs = {
            "headers": self.headers,
            "verify": self.env.config.get("foreman.verify", "true") == "true",
            "data": data,
            "cookies": self.__cookies,
            "timeout": 30
        }
        try:
            if self.__cookies is None:
                response = self.__authenticate(method, url, kwargs)
            else:
                response = method(url, **kwargs)
        except Exception as e:
            self.log.error("Error during foreman API request: %s" % str(e))
            raise e

        if response.status_code == 401 and self.__cookies is not None:
            # try to re-authenticate session might be timed out
            response = self.__authenticate(method, url, kwargs)

        if response.ok:
            data = response.json()
            self.log.debug("response %s" % data)
            # check for error
            if "error" in data:
                raise ForemanBackendException(response, method=method_name)
            else:
                ForemanClientCache.add_to_cache(method_name, object_type, data, object_id=object_id)
            return data
        else:
            self.log.error("%s request with %s to %s failed: %s" % (method_name, data, url, str(response.content)))
            raise ForemanBackendException(response, method=method_name)

    def check_backend(self):
        """ check if foreman backend is reachable """
        try:
            response = self.__request("get", "status")
            return response["result"] == "ok"
        except:
            return False

    def get(self, object_type, object_id=None):
        return self.__request("get", object_type, object_id=object_id)

    def delete(self, object_type, object_id):
        return self.__request("delete", object_type, object_id=object_id)

    def put(self, object_type, object_id, data):
        return self.__request("put", object_type, object_id=object_id, data=data)

    def post(self, object_type, object_id=None, data=None):
        return self.__request("post", object_type, object_id=object_id, data=data)

    def set_common_parameter(self, name, value, host=None, replace=True):
        foreman_type = "common_parameter" if host is None else "parameter"
        payload = {
            foreman_type: {
                "name": name,
                "value": value
            }
        }
        path = "common_parameters" if host is None else "hosts/%s/parameters" % host
        try:
            response = self.get(path, object_id=name)
        except ForemanBackendException as e:
            if e.response.status_code == 404:
                # create parameter
                self.post(path, data=payload)
        else:
            if 'value' not in response or (response["value"] != payload[foreman_type]["value"] and replace is False):
                # update parameter
                self.put(path, object_id=name, data=payload)

    @classmethod
    def error_notify_user(cls, ex, user=None):
        SseHandler.error_notify_user("Foreman backend error", ex, user=user)


class ForemanBackendException(ObjectException):

    def __init__(self, response=None, exception=None, method=None):
        self.exception = exception
        self.response = response
        self.method = method if method is not None else ""

        if response.status_code == 404:
            self.message = C.make_error('FOREMAN_OBJECT_NOT_FOUND', response.url)
        else:
            try:
                data = response.json()
            except json.decoder.JSONDecodeError as e:
                self.message = C.make_error('FOREMAN_COMMUNICATION_ERROR', response.status_code)
            else:
                if "error" in data:
                    if "message" in data["error"]:
                        self.message = C.make_error('FOREMAN_COMMUNICATION_ERROR', data["error"]["message"])
                    else:
                        self.message = ", ".join(data["error"]["full_messages"]) if "full_messages" in data["error"] else str(data["error"])
                else:
                    self.message = C.make_error('FOREMAN_COMMUNICATION_ERROR', response.status_code)

    def __str__(self):
        return self.message
