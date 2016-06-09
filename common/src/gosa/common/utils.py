# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The utility module is a collection of smaller functions that
make the life of plugin programming easier.
"""
import re
import os
import time
import tempfile
import lxml
import urllib.request as urllib2
from tokenize import generate_tokens
from token import STRING
from subprocess import Popen, PIPE
from urllib.parse import urlparse
from datetime import datetime
from io import StringIO


_is_uuid = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')


def stripNs(data):
    """
    **stripNS** removes the namespace from a plain XML string.

    ========= ============
    Parameter Description
    ========= ============
    data      XML string to be namespace stripped
    ========= ============

    ``Return``: string without namespace
    """
    p = re.compile(r'^\{[^\}]+\}(.*)$')
    return p.match(data).group(1)


def makeAuthURL(url, user, password):
    """
    **makeAuthURL** assembles a typical authentication URL from
    the plain URL and user/password strings::

        http://user:secret@example.net:8080/somewhere

    ========= ============
    Parameter Description
    ========= ============
    data      XML string to be namespace stripped
    ========= ============

    ``Return``: string without namespace
    """
    o = urlparse(url)
    #pylint: disable=E1101
    return "%s://%s:%s@%s%s" % (o.scheme, user, password, o.netloc, o.path)


def parseURL(url):
    """
    **parseURL** parses an URL string using :func:`urlparse.urlparse` and gathers
    extra (partly default) settings.

    ========= ============
    Parameter Description
    ========= ============
    URL       URL string
    ========= ============

    ``Return``: dictionary
    """
    if not url:
        return None

    # Eventually encode URL
    if type(url) == unicode:
        url = url.encode('utf-8')

    source = url
    url = urlparse(url)

    # Load parts and extend if not provided
    # pylint: disable=E1101
    scheme, user, password, host, port, path = url.scheme, url.username, url.password, url.hostname, url.port, url.path[1:]
    if scheme == 'http':
        port = 80 if not port else port
    else:
        port = 443 if not port else port

    path = 'rpc' if path == "" else path
    url = '%s://%s:%s@%s:%s/%s' % (scheme, user, password, host, port, path)
    ssl = 'tcp+ssl' if scheme[-1] == 's' else 'tcp'

    return {'source': source,
        'scheme': scheme,
        'user': user,
        'password': password,
        'host': host,
        'port': int(port),
        'path': path,
        'transport': ssl,
        'url': url}


def N_(message):
    """
    Function to be used for deferred translations. Mark strings that should
    exist as a translation, but not be translated in the moment as N_('text').

    ========== ============
    Parameter  Description
    ========== ============
    message    Text to be marked as a translation
    ========== ============

    ``Return``: Target XML schema processed by stylesheet as string.
    """
    return message


def is_uuid(uuid):
    return bool(_is_uuid.match(uuid))


def get_timezone_delta():
    """
    Function to estimate the local timezone shift.

    ``Return``: String in the format [+-]hours:minutes
    """
    timestamp = time.mktime(datetime.now().timetuple())
    timeDelta = datetime.fromtimestamp(timestamp) - datetime.utcfromtimestamp(timestamp)
    seconds = timeDelta.seconds
    return "%s%02d:%02d" % ("-" if seconds < 0 else "+", abs(seconds // 3600), abs(seconds % 60))


def locate(program):
    """
    Function to emulate UNIX 'which' behavior.

    ========== ============
    Parameter  Description
    ========== ============
    program    Name of the executable to find in the PATH.
    ========== ============

    ``Return``: Full path of the executable or None
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath = os.path.dirname(program)
    if fpath and is_exe(program):
        return program

    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def dmi_system(item, data=None):
    """
    Function to retrieve information via DMI.

    ========== ============
    Parameter  Description
    ========== ============
    item       Path to the item to decode.
    data       Optional external data to parse.
    ========== ============

    ``Return``: String
    """
    return None

# Re-define dmi_system depending on capabilites
try:
    import dmidecode
    dmidecode.clear_warnings() #@UndefinedVariable

    def dmi_system(item, data=None):
        if not data:
            data = dmidecode.system() #@UndefinedVariable
            dmidecode.clear_warnings() #@UndefinedVariable

        item = item.lower()

        for key, value in data.iteritems():
            if item == key.lower():
                return value
            if isinstance(value, dict) and value:
                value = dmi_system(item, value)
                if value:
                    return value

        return None

except ImportError:

    for ext in ["dmidecode", "dmidecode.exe"]:
        if locate(ext):
            #pylint: disable=E0102
            def dmi_system(item, data=None):
                cmd = [ext, '-s', 'system-uuid']
                p = Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout = p.communicate()[0]
                return "".join(stdout).strip()

            break


def f_print(data):
    if not isinstance(data, basestring):
        return data[0] % tuple(data[1:])
    else:
        return data


def repr2json(string):
    g = generate_tokens(StringIO(string).readline)

    result = ""
    for toknum, tokval, _, _, _ in g:
        if toknum == STRING:
            tokval = '"' + tokval[1:-1].replace('"', r'\"') + '"'

        result += tokval

    return result


def downloadFile(url, download_dir=None, use_filename=False):
    """
    Download file to a local (temporary or preset) path and return the
    resulting local path for further usage.

    ============ ============
    Parameter    Description
    ============ ============
    url          URL of file to be downloaded.
    download_dir Directory where to place the downloaded file.
    use_filename use the original filename or a temporary?
    ============ ============

    ``Return``: local file name
    """
    result = None
    o = None

    if not url:
        raise ValueError(N_("URL is mandatory!"))

    try:
        o = urlparse(url)
    except:
        raise ValueError(N_("Invalid url specified: %s"), url)

    #pylint: disable=E1101
    if o.scheme in ('http', 'https', 'ftp'):
        try:
            if use_filename:
                if not download_dir:
                    download_dir = tempfile.mkdtemp()

                f = os.sep.join((download_dir, os.path.basename(o.path)))

            else:
                if download_dir:
                    f = tempfile.NamedTemporaryFile(delete=False, dir=download_dir).name
                else:
                    f = tempfile.NamedTemporaryFile(delete=False).name

            request = urllib2.Request(url)
            dfile = urllib2.urlopen(request)
            local_file = open(f, "w")
            local_file.write(dfile.read())
            local_file.close()
            result = f

        except urllib2.HTTPError as e:
            result = None
            raise e

        except urllib2.URLError as e:
            result = None
            raise e

        except:
            raise
    else:
        #pylint: disable=E1101
        raise ValueError(N_("Unsupported URL scheme %s!"), o.scheme)

    return result


def xml2dict(node):
    """
    Recursive operation which returns a tree formated
    as dicts and lists.
    Decision to add a list is to find the 'List' word
    in the actual parent tag.
    """
    ret = {}

    for k, v in node.__dict__.items():
        if isinstance(v, str):
            ret[k] = v
        elif isinstance(v, lxml.objectify.StringElement):
            ret[k] = v.text
        elif isinstance(v, lxml.objectify.IntElement):
            ret[k] = v.text
        elif isinstance(v, lxml.objectify.ObjectifiedElement):
            if v.__len__ > 1:
                tmp = []
                for el in v:
                    tmp.append(xml2dict(el))

                ret.update({k: tmp})

            else:
                ret.update({k: xml2dict(v)})
        else:
            raise Exception("Cannot convert type %s" % type(v))

    return ret


class SystemLoad:
    """
    The *SystemLoad* class allows to measure the current system load
    on Linux style systems.
    """
    __timeList1 = [1, 1, 1, 1, 1, 1, 1, 1, 1]

    def getLoad(self):
        """
        Get current nodes CPU load.

        ``Return:`` load level
        """

        def getTimeList():
            with file("/proc/stat", "r") as f:
                cpuStats = f.readline()
            columns = cpuStats.replace("cpu", "").split(" ")
            return map(int, filter(None, columns))

        timeList2 = getTimeList()
        dt = list([(t2 - t1) for t1, t2 in zip(self.__timeList1, timeList2)])

        idle_time = float(dt[3])
        total_time = sum(dt)
        load = 0.0
        if total_time != 0.0:
            load = 1 - (idle_time / total_time)
            # Set old time delta to current
            self.__timeList1 = timeList2

        return round(load, 2)
