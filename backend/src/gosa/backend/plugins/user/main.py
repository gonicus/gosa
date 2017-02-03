
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from gosa.backend.plugins.misc.transliterate import Transliterate
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_
from zope.interface import implementer
import re
import random


@implementer(IInterfaceHandler)
class User(Plugin):
    _priority_ = 0
    _target_ = "core"
    __last_id = 0

    def __init__(self):
        self.__parser = re.compile(
            '(\{?%([a-z0-9]+)(\[(([0-9]+)(\-([0-9]+))?)\])?\}?)',
            re.IGNORECASE)
        self.__id_parser = re.compile(
            '\{id(#|:)([0-9])+\}',
            re.IGNORECASE)
        self.__transliterator = Transliterate()

    @Command(__help__=N_('Generates a uid'))
    def generateId(self, format_string, data):
        substituted_string = self.__substitute_attributes(
            format_string,
            self.__parser.findall(format_string),
            data)
        return self.__substitute_id_annotations(
            substituted_string,
            self.__id_parser.findall(substituted_string))

    def __substitute_attributes(self, format_string, results, data):
        for result in results:
            format_string = self.__substitute_attribute(result, data, format_string)
        return format_string

    def __substitute_attribute(self, result, data, format_string):
        attribute_name = result[1]
        start_index = result[4]
        end_index = result[6]

        return self.__parser.sub(
            self.__get_substitution(
                data,
                attribute_name,
                start_index,
                end_index),
            format_string,
            count=1)

    def __get_substitution(self, data, attribute_name, start_index, end_index):
        if end_index:
            substitution = self.__get_attribute_value(data, attribute_name)[int(start_index):int(end_index)]
        elif start_index:
            substitution = self.__get_attribute_value(data, attribute_name)[int(start_index)]
        else:
            substitution = self.__get_attribute_value(data, attribute_name)
        return substitution

    def __get_attribute_value(self, data, attribute_name):
        return self.__transliterator.transliterate(data[attribute_name])

    def __substitute_id_annotations(self, format_string, results):
        for result in results:
            format_string = self.__substitute_id(format_string, result)
        return format_string

    def __substitute_id(self, format_string, result):
        take_next_id = result[0] == ':'
        take_random_id = result[0] == '#'
        n = int(result[1])
        substitution = None

        if take_next_id:
            self.__last_id += 1
            substitution = str(self.__last_id).rjust(n, '0')
        if take_random_id:
            substitution = str(random.randrange(10**(n-1), 10**n))

        if substitution:
            format_string = self.__id_parser.sub(substitution, format_string, count=1)
        return format_string
