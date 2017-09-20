# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging

from gosa.backend.objects.filter import ElementFilter
from gosa.backend.objects.factory import ObjectFactory
import time
import datetime

from gosa.common.components import PluginRegistry


class Rename(ElementFilter):
    """
    This filter renames the attribute.
    e.g.::

      <FilterEntry>
       <Filter>
        <Name>Rename</Name>
        <Param>passwordMethod</Param>
       </Filter>
      </FilterEntry>
    """
    def __init__(self, obj):
        super(Rename, self).__init__(obj)

    def process(self, obj, key, valDict, new_key):
        """
        Rename an attribute

        :param obj: current object
        :param key: attribute name this filter is defined for
        :param valDict: complete attribute dictionary of this object
        :param new_key: target attribute this attribute should be renames to
        :return:
        """
        if key != new_key:
            valDict[new_key] = valDict[key]
            del(valDict[key])
            obj.attributesInSaveOrder.remove(key)
        return new_key, valDict


class CopyValueTo(ElementFilter):
    """
     This filter copies the value from this attribute to another attribute.
     e.g.::

       <FilterEntry>
        <Filter>
         <Name>CopyValueTo</Name>
         <Param>cn</Param>
        </Filter>
       </FilterEntry>
     """
    def __init__(self, obj):
        super(CopyValueTo, self).__init__(obj)
        import logging
        self.log = logging.getLogger(__name__)

    def process(self, obj, key, valDict, target_key):
        if type(valDict[key]['value']) is not None and len(valDict[key]['value']):
            valDict[target_key]['value'] = valDict[key]['value']
        return key, valDict


class CopyForeignValueTo(ElementFilter):
    """
     This filter copies the value from a foreign objects attribute that is somehow related, to another attribute.
     e.g.::

    .. code-block:: xml

        <FilterEntry>
            <Filter>
                <Name>CopyForeignValueTo</Name>
                <Param>ForemanHostGroup</Param><!-- related object type -->
                <Param>foremanGroupId</Param><!-- ID attribute of related object -->
                <Param>dn</Param><!-- content that should be written to the target attribute -->
                <Param>groupMembership</Param><!-- local target attribute the value should be copied to -->
            </Filter>
       </FilterEntry>
     """

    def process(self, obj, key, valDict, object_type, id_attribute, content_attribute, target_attribute):
        index = PluginRegistry.getInstance("ObjectIndex")
        valDict[target_attribute]['value'] = []
        log = logging.getLogger(__name__)
        if type(valDict[key]['value']) is not None and len(valDict[key]['value']):
            for val in valDict[key]['value']:
                res = index.search({"or_": {"_type": object_type, 'extension': object_type}, id_attribute: val}, {content_attribute: 1})
                if len(res):
                    log.debug("adding %s to %s" % (res[0][content_attribute], target_attribute))
                    if isinstance(res[0][content_attribute], list):
                        valDict[target_attribute]['value'].extend(res[0][content_attribute])
                    else:
                        valDict[target_attribute]['value'].append(res[0][content_attribute])

        return key, valDict


class CopyForeignValueFrom(ElementFilter):
    """
     This filter copies the value from a foreign objects attribute that is related by a source_attribute to the current
     attribute
     e.g.::

    .. code-block:: xml

        <FilterEntry>
            <Filter>
                <Name>CopyForeignValueFrom</Name>
                <Param>ForemanHostGroup</Param><!-- related object type -->
                <Param>foremanGroupId</Param><!-- ID attribute of related object -->
                <Param>dn</Param><!-- type of content in the source attribute -->
                <Param>groupMembership</Param><!-- local source attribute the value should be copied from -->
            </Filter>
        </FilterEntry>

    You can read the parameters like:
    I want to copy the ``foremanGroupId`` of a ``ForemanHostGroup``, which is identified by a ``dn`` in ``groupMembership``.

     """

    def process(self, obj, key, valDict, object_type, id_attribute, source_content, source_attribute):
        index = PluginRegistry.getInstance("ObjectIndex")
        valDict[key]['value'] = []
        log = logging.getLogger(__name__)
        if type(valDict[source_attribute]['value']) is not None and len(valDict[source_attribute]['value']):
            for val in valDict[source_attribute]['value']:
                res = index.search({"or_": {"_type": object_type, 'extension': object_type}, source_content: val}, {id_attribute: 1})
                if len(res) and res[0][id_attribute] is not None:
                    log.debug("adding %s from %s to %s" % (res[0][id_attribute], source_attribute, key))
                    if isinstance(res[0][id_attribute], list):
                        valDict[key]['value'].extend(res[0][id_attribute])
                    else:
                        valDict[key]['value'].append(res[0][id_attribute])

        return key, valDict


class CopyValueFrom(ElementFilter):
    """
     This filter copies the value from another attribute to this attribute
     e.g.::

       <FilterEntry>
        <Filter>
         <Name>CopyValueFrom</Name>
         <Param>cn</Param>
        </Filter>
       </FilterEntry>
     """
    def __init__(self, obj):
        super(CopyValueFrom, self).__init__(obj)

    def process(self, obj, key, valDict, source_key):
        if type(valDict[source_key]['value']) is not None and len(valDict[source_key]['value']):
            valDict[key]['value'] = valDict[source_key]['value']
        return key, valDict


class SetBackends(ElementFilter):
    """
    This filter allows to change the target backend of an attribute.
    It also allows to specify a various amount of backends, see example below.
    e.g.::

      <FilterEntry>
       <Filter>
        <Name>SetBackends</Name>
        <Param>LDAP</Param>
        <Param>NULL</Param>
        <Param>...</Param>
       </Filter>
      </FilterEntry>
    """
    def __init__(self, obj):
        super(SetBackends, self).__init__(obj)

    def process(self, obj, key, valDict, *new_backends):
        valDict[key]['backend'] = list(new_backends)
        return key, valDict


class AddBackend(ElementFilter):
    """
    Add another backend to the existing ones.
    """
    def __init__(self, obj):
        super(AddBackend, self).__init__(obj)

    def process(self, obj, key, valDict, new_backend):
        valDict[key]['backend'].append(new_backend)
        return key, valDict


class SetValue(ElementFilter):
    """
    This filter allows to change the value of an attrbiute.
    e.g.::

      <FilterEntry>
       <Filter>
        <Name>SetValue</Name>
        <Param>Hallo mein name ist Peter</Param>
       </Filter>
      </FilterEntry>
    """
    def __init__(self, obj):
        super(SetValue, self).__init__(obj)

    def process(self, obj, key, valDict, value):
        types = ObjectFactory.getInstance().getAttributeTypes()
        valDict[key]['value'] = types['String'].convert_to(valDict[key]['type'], [value])
        return key, valDict


class Clear(ElementFilter):
    """
    This filter clears the value of an attribute.
    """
    def __init__(self, obj):
        super(Clear, self).__init__(obj)

    def process(self, obj, key, valDict):
        types = ObjectFactory.getInstance().getAttributeTypes()
        valDict[key]['value'] = types['String'].convert_to(valDict[key]['type'], [''])
        return key, valDict


class IntegerToDatetime(ElementFilter):
    """
    Converts an integer object into a datetime.datetime object..

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>IntegerToDatetime</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(IntegerToDatetime, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = list(map(lambda x: datetime.datetime.fromtimestamp(x), valDict[key]['value']))
        valDict[key]['backend_type'] = 'Timestamp'
        return key, valDict


class DatetimeToInteger(ElementFilter):
    """
    Converts a timestamp object into an integer value ...

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>DatetimeToInteger</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(DatetimeToInteger, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = list(map(lambda x: int(time.mktime(x.timetuple())), valDict[key]['value']))
        valDict[key]['backend_type'] = 'Integer'
        return key, valDict


class StringToDatetime(ElementFilter):
    """
    Converts a string object into a datetime.datetime object..

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>StringToDatetime</Name>
    >>>   <Param>%%Y-%%m-%%d</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(StringToDatetime, self).__init__(obj)

    def process(self, obj, key, valDict, fmt):
        valDict[key]['value'] = list(map(lambda x: datetime.datetime.strptime(x, fmt), valDict[key]['value']))
        valDict[key]['backend_type'] = 'Timestamp'
        return key, valDict


class DatetimeToString(ElementFilter):
    """
    Converts a timestamp object into an string value of the given format...

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>DatetimeToString</Name>
    >>>   <Param>%%Y-%%m-%%d</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(DatetimeToString, self).__init__(obj)

    def process(self, obj, key, valDict, fmt):
        valDict[key]['value'] = list(map(lambda x: x.strftime(fmt), valDict[key]['value']))
        valDict[key]['backend_type'] = 'String'
        return key, valDict


class IntegerToBoolean(ElementFilter):
    """
    Converts an integer object into a boolean object..

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>IntegerToBoolean</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(IntegerToBoolean, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = list(map(lambda x: bool(x), valDict[key]['value']))
        valDict[key]['backend_type'] = 'Boolean'
        return key, valDict


class BooleanToInteger(ElementFilter):
    """
    Converts a boolean object into an integer value ...

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>BooleanToInteger</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(BooleanToInteger, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = list(map(lambda x: int(x), valDict[key]['value']))
        valDict[key]['backend_type'] = 'Integer'
        return key, valDict


class FilterOwnDn(ElementFilter):
    """ remove own DN from values"""

    def process(self, obj, key, valDict):
        valDict[key]['value'] = [x for x in valDict[key]['value'] if x != obj.get_final_dn()]
        return key, valDict


class AddOwnDnIfEmpty(ElementFilter):
    """ add own DN to attribute if is has no values """

    def process(self, obj, key, valDict):
        if len(valDict[key]['value']) == 0:
            valDict[key]['value'].append(obj.get_final_dn())
        return key, valDict
