# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.objects.filter import ElementFilter


class MarshalFlags(ElementFilter):
    """
    Compose a flag string from a list of boolean attributes

    .. code-block:: xml

        <Filter>
            <Name>MarshalFlags</Name>
            <Param>G,O,L,D,M</Param>
            <Param>execForGroupmembers,overwriteConfig,placeOnKicker,placeOnDesktop,placeInStartmenu</Param>
        </Filter>

    creates `GLD` if `execForGroupmembers`, `placeOnKicker` and `placeOnDesktop` are true
    """

    def process(self, obj, key, valDict, flags, targets):
        flag_ids = flags.split(",")
        target_attributes = targets.split(",")

        flag_string = []
        for i, attribute in enumerate(target_attributes):
            for index, value in enumerate(valDict[attribute]["value"]):
                if len(flag_string) <= index:
                    flag_string.append("")
                if value is True:
                    flag_string[index] += flag_ids[i]

        valDict[key]["value"] = flag_string
        return key, valDict


class UnmarshalFlags(ElementFilter):
    """
    Extract boolean values from a list of flags depending if the flag ID in in the value string
    e.g.

    .. code-block:: xml

        <Filter>
            <Name>UnmarshalFlags</Name>
            <Param>G,O,L,D,M</Param>
            <Param>execForGroupmembers,overwriteConfig,placeOnKicker,placeOnDesktop,placeInStartmenu</Param>
        </Filter>

    sets `execForGroupmembers`, `placeOnKicker` and `placeOnDesktop` to true if attribute string is `GLD`
    """

    def process(self, obj, key, valDict, flags, targets):
        flag_ids = flags.split(",")
        target_attributes = targets.split(",")

        # initialize values
        for name in target_attributes:
            valDict[name]["value"] = []

        for index, value in enumerate(valDict[key]["value"]):
            for i, flag in enumerate(flag_ids):
                valDict[target_attributes[i]]["value"].append(flag in value)

        return key, valDict