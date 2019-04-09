#!/usr/bin/env python3
"""
Foreman / GOsa3 integration to send hook events data to GOsa3
"""
import hmac
import sys
import requests
import json

#. /etc/sysconfig/foreman-gosa
# Gosa settings
GOSA_SERVER = "http://localhost"
GOSA_PORT = 8050
HTTP_X_HUB_SENDER = "foreman-hook"
SECRET = "e540f417-4c36-4e5d-b78a-4d36f51727ec"

HOOK_TEMP_DIR = "/usr/share/foreman/tmp"

# HOOK_EVENT = update, create, before_destroy etc.
# HOOK_OBJECT = to_s representation of the object, e.g. host's fqdn
HOOK_EVENT, HOOK_OBJECT = (sys.argv[1], sys.argv[2])

payload = json.loads(sys.stdin.read())

# add event + object to payload
payload = json.dumps({
    "event": HOOK_EVENT,
    "object": HOOK_OBJECT,
    "data": payload
}).encode('utf-8')

signature_hash = hmac.new(bytes(SECRET, 'ascii'), msg=payload, digestmod="sha512")
signature = 'sha1=' + signature_hash.hexdigest()

headers = {
    'Content-Type': 'application/vnd.foreman.hookevent+json',
    'HTTP_X_HUB_SENDER': HTTP_X_HUB_SENDER,
    'HTTP_X_HUB_SIGNATURE': signature
}

try:
    requests.post("%s:%s/hooks" % (GOSA_SERVER, GOSA_PORT), data=payload, headers=headers, timeout=30)
except Exception as e:
    print("Error calling hook: %s" % str(e))
