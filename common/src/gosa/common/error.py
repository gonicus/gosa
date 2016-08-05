# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import inspect
import traceback
import gettext
import uuid
import re
from datetime import datetime
from pkg_resources import resource_filename
from gosa.common.utils import N_
from gosa.common.components import Command
from gosa.common.components import Plugin


class GosaErrorHandler(Plugin):

    _target_ = "core"
    _codes = {}
    _i18n_map = {}
    _errors = {}
    _error_regex = re.compile("^<([^>]+)>.*$")

    @Command(needsUser=True, __help__=N_("Get the error message assigned to a specific ID."))
    def getError(self, user, _id, locale=None, trace=False, keep=False):
        res = None
        if _id in GosaErrorHandler._errors:
            res = GosaErrorHandler._errors[_id]
            if user is not None and res['error_owner'] is not None and user != res['error_owner']:
                # user is not the originator of this error
                return None

            if not trace and not keep:
                del res['trace']

            # Translate message if requested
            if locale:
                mod = GosaErrorHandler._i18n_map[res['code']]
                t = gettext.translation('messages',
                                        resource_filename(mod, "locale"),
                                        fallback=True,
                                        languages=[locale])
                res['text'] = t.gettext(GosaErrorHandler._codes[res['code']])
                # Process details by translating detail text
                if res['details']:
                    for detail in res['details']:
                        detail['detail'] = t.gettext(detail['detail']) % detail

            # Fill keywords
            res['text'] = res['text'] % res['kwargs']
            res['_id'] = _id

            # Remove the entry
            if not keep:
                del GosaErrorHandler._errors[_id]

        return res

    @staticmethod
    def make_error(code, topic=None, details=None, error_owner=None, status_code=None, **kwargs):

        # First, catch unconverted exceptions
        if code not in GosaErrorHandler._codes:
            return code

        # Add topic to make it usable inside of the error messages
        if not kwargs:
            kwargs = {}
        kwargs.update(dict(topic=topic))

        # Assemble message
        text = GosaErrorHandler._codes[code] % kwargs

        # Assemble error information
        data = dict(code=code, topic=topic, text=text,
                    kwargs=kwargs, trace=traceback.format_stack(),
                    details=details,
                    timestamp=datetime.now(), error_owner=error_owner,
                    status_code=status_code)

        # Save entry
        __id = str(uuid.uuid1())
        GosaErrorHandler._errors[__id] = data

        return '<%s> %s' % (__id, text)

    @staticmethod
    def register_codes(codes, module=None):
        GosaErrorHandler._codes.update(codes)
        if module is None:
            try:
                frm = inspect.stack()[1]
                mod = inspect.getmodule(frm[0])
                if mod:
                    module = ".".join(mod.__name__.split(".")[0:2])
            except:
                # fallback to old behaviour
                module = "gosa.plugin"

        # Memorize which module to get translations from
        for k in codes.keys():
            GosaErrorHandler._i18n_map[k] = module

    @staticmethod
    def get_error_id(error_string):
        m = GosaErrorHandler._error_regex.match(error_string)
        if m is not None:
            return m.group(1)
        else:
            return None


class GosaException(Exception):
    """
    Gosa base exception that converts the error to a string and
    feeds it to the database  in parallel. Errors emitted with
    GosaException can be queried by their ID later on.
    """

    def __init__(self, *args, **kwargs):
        info = GosaErrorHandler.make_error(*args, **kwargs)
        super(GosaException, self).__init__(info)


# Register basic errors
GosaErrorHandler.register_codes(dict(
    NOT_IMPLEMENTED=N_("Method %(method)s is not implemented"),
    NO_SUCH_RESOURCE=N_("Cannot read resource '%(resource)s'"),
    ))
