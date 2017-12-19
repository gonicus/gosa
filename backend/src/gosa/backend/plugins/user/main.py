
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from gosa.backend.objects import ObjectProxy
from gosa.common.error import GosaErrorHandler as C, GosaException
from gosa.backend.plugins.misc.transliterate import Transliterate
from gosa.common import Environment
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.components import PluginRegistry
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_
from zope.interface import implementer
import re
import random

C.register_codes(dict(
    CONFIG_NO_FORMAT_STRING=N_("Cannot find a format_string in the configuration"),
    GROUP_ID_IS_AMBIGUOUS=N_("Multiple PosixGroups with gid '%(gid)s' found")
    ))

@implementer(IInterfaceHandler)
class User(Plugin):
    _priority_ = 0
    _target_ = "core"

    @Command(__help__=N_('Generates a uid'))
    def generateUid(self, data):

        format_string = Environment.getInstance().config.get('core.idGenerator')
        if not format_string:
            raise EnvironmentError(C.make_error('CONFIG_NO_FORMAT_STRING'))
        format_string = format_string.strip()
        if format_string.startswith('"') and format_string.endswith('"'):
            format_string = format_string[1:-1]

        result = [format_string]
        result = self.__generate_attributes(result, data)
        result = self.__generate_ids(result)

        # remove any uid that already exists
        return list(filter(lambda x: not self.uid_exists(x), result))

    @Command(__help__=N_('Create PosixGroup if it does not exists and add the user to it'))
    def createAddGroupIfNotExists(self, user_dn, user_name, gid_number):
        if user_dn is None or user_name is None or gid_number is None:
            return
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({"_type": "PosixGroup", "gidNumber": gid_number}, {"dn": 1})
        if len(res) == 0:
            # create group
            user = ObjectProxy(user_dn)
            group = ObjectProxy(user.get_adjusted_parent_dn(), "PosixGroup")
            group.cn = user_name
            group.description = N_("Group of user %s" % user_name)
            group.autoGid = False
            group.gidNumber = gid_number
            group.memberUid = [user_name]
            group.commit()
        elif len(res) == 1:
            group = ObjectProxy(res[0]["dn"])
            if user_name not in group.memberUid:
                group.memberUid.append(user_name)
                group.commit()
        else:
            raise GosaException(C.make_error('GROUP_ID_IS_AMBIGUOUS', gid=gid_number))


    def uid_exists(self, uid):
        results = PluginRegistry.getInstance("ObjectIndex").search({'uid': uid}, {'dn': 1})
        return bool(len(results))

    def __generate_attributes(self, result, data):
        parser = re.compile('(\{?%([a-z0-9]+)(\[(([0-9]+)(\-([0-9]+))?)\])?\}?)', re.IGNORECASE)
        matches = parser.findall(result[0])
        transliterator = Transliterate()

        for match in matches:
            value = transliterator.transliterate(data[match[1]])
            lower_index = match[4]
            upper_index = match[6]
            new_result = []

            for string in result:
                # both indexes given
                if upper_index:
                    lower_index = int(lower_index)
                    upper_index = int(upper_index)

                    for j in range(lower_index, upper_index):
                        new_result.append(parser.sub(value[lower_index:j+1], string, count=1))

                # just lower index given - take char at index
                elif lower_index:
                    lower_index = int(lower_index)
                    new_result.append(parser.sub(value[lower_index], string, count=1))

                # no index given - take whole value
                else:
                    new_result.append(parser.sub(value, string, count=1))

            result = new_result
        return result

    def __generate_ids(self, result):
        id_parser = re.compile('\{id(#|:|!)([0-9])+\}', re.IGNORECASE)
        for i, string in enumerate(result):
            matches = id_parser.findall(string)

            for match in matches:
                n = int(match[1])

                # random
                if match[0] == '#':
                    while True:
                        r = str(random.randrange(10**(n-1), 10**n))
                        if not self.uid_exists(id_parser.sub(r, string, count=1)):
                            break
                    result[i] = id_parser.sub(r, string, count=1)

                # next free id
                elif match[0] == ':':
                    id_count = 0
                    while self.uid_exists(id_parser.sub(str(id_count).rjust(n, '0'), string, count=1)):
                        id_count += 1
                    result[i] = id_parser.sub(str(id_count).rjust(n, '0'), string, count=1)

                # use next free id, but only if uid without the id already exists
                elif match[0] == '!':
                    if not self.uid_exists(id_parser.sub('', string, count=1)):
                        result[i] = id_parser.sub('', string, count=1)
                    else:
                        id_count = 1
                        while self.uid_exists(id_parser.sub(str(id_count).rjust(n, '0'), string, count=1)):
                            id_count += 1
                        result[i] = id_parser.sub(str(id_count).rjust(n, '0'), string, count=1)

        return result