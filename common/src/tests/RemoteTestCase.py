# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
from tornado.testing import AsyncHTTPTestCase
from gosa.common.gjson import dumps
from tornado.web import decode_signed_value


class RemoteTestCase(AsyncHTTPTestCase):

    def setUp(self):
        super(RemoteTestCase, self).setUp()
        self.__cookies = ''
        self._xsrf = None
        self.session_id = None

    def _update_cookies(self, headers):
        try:
            raw = headers['Set-Cookie']
            # remove expires + path
            raw = re.sub(r"; expires=[^;]+;", "", raw)
            raw = re.sub(r";? Path=[^,]+,", ";", raw)
            # last path
            raw = re.sub(r";? Path=[^,]$", "", raw)
            for cookie in raw.split(";"):
                (key, value) = cookie.split("=", 1)
                if key == "_xsrf":
                    self._xsrf = value
                elif key == "REMOTE_SESSION":
                    tmp = decode_signed_value('TecloigJink4', 'REMOTE_SESSION', value)
                    self.session_id = tmp.decode('ascii') if tmp else None
            self.__cookies = raw
        except KeyError:
            return

    def fetch(self, url, **kw):
        headers = kw.pop('headers', {})
        if self.__cookies != '':
            headers['Cookie'] = self.__cookies
        if self._xsrf:
            headers['X-XSRFToken'] = self._xsrf
            if len(headers['Cookie'])>0 and '_xsrf' not in headers['Cookie']:
                headers['Cookie'] = "%s;%s=%s" % (headers['Cookie'], '_xsrf', self._xsrf)
        # if 'body' in kw:
        #     print("URL: {}, Body: {}, Headers: {}".format(url, kw['body'] , headers))
        # else:
        #     print("URL: {}, Headers: {}".format(url, headers))
        resp = AsyncHTTPTestCase.fetch(self, url, headers=headers, **kw)
        self._update_cookies(resp.headers)
        return resp

    def fetch_async(self, url, **kw):
        header = kw.pop('headers', {})
        if self.__cookies != '':
            header['Cookie'] = self.__cookies
        if self._xsrf:
            header['X-XSRFToken'] = self._xsrf
            if len(header['Cookie'])>0 and '_xsrf' not in header['Cookie']:
                header['Cookie'] = "%s;%s=%s" % (header['Cookie'], '_xsrf', self._xsrf)
        # if 'body' in kw:
        #     print("URL: {}, Body: {}, Headers: {}".format(url, kw['body'] , header))
        # else:
        #     print("URL: {}, Headers: {}".format(url, header))
        return self.http_client.fetch(url, self.stop, headers=header, **kw)

    def login(self):
        # fetch the xsrf cookie
        self.fetch('/rpc', method='GET')
        data = dumps({
            "id": 0,
            "method": "login",
            "params": ["admin", "tester"]
        })
        # login
        return self.fetch('/rpc',
                          method='POST',
                          body=data
                          )
