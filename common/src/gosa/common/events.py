# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import zope.event.classhandler


class ZopeEventConsumer(object):

    def __init__(self, callback=None, type=None):
        self.__callback = callback
        self.__type = type

        zope.event.classhandler.handler(Event, self.__process_event)

    def __process_event(self, event):
        if self.__type is None or self.__get_type(event) == self.__type:
            self.__callback(event.get_data())

    def __get_type(self, event):
        tag = event.get_data().getchildren()[0].tag
        if tag.find("}") >= 0:
            # strip namespace
            return tag[tag.find("}")+1:]
        else:
            return event.get_data().getchildren()[0].tag


class Event(object):

    def __init__(self, data=None, emitter=None):
        self.__data = data
        self.__emitter = emitter

    def get_data(self):
        return self.__data

    def get_emitter(self):
        return self.__emitter


class EventNotAuthorized(Exception):
    pass