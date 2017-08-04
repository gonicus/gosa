from gosa.backend.objects.filter import ElementFilter

FM_STATUS_GLOBAL_OK = 0
FM_STATUS_GLOBAL_WARNING = 1
FM_STATUS_GLOBAL_ERROR = 2

FM_STATUS_BUILD = 0
FM_STATUS_BUILD_PENDING = 1
FM_STATUS_BUILD_TOKEN_EXPIRED = 2

class ForemanStatusIn(ElementFilter):
    """
    converts foreman host status from the values in build_status and global_status

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>ForemanStatusIn</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """
    def __init__(self, obj):
        super(ForemanStatusIn, self).__init__(obj)

    def process(self, obj, key, valDict, glue=", "):
        if type(valDict[key]['value']) is not None and len(valDict[key]['value']) and valDict[key]['value'][0] != "discovered":
            global_status = valDict['global_status']['value'][0] if len(valDict['global_status']['value']) else None
            build_status = valDict['build_status']['value'][0] if len(valDict['build_status']['value']) else None
            if global_status is not None or build_status is not None:
                valDict[key]['value'] = [ForemanStatusIn.convert(global_status, build_status)]
        return key, valDict

    @staticmethod
    def convert(global_status, build_status):
        if global_status == FM_STATUS_GLOBAL_OK:
            if build_status == FM_STATUS_BUILD:
                return "ready"
            elif build_status == FM_STATUS_BUILD_PENDING:
                return "pending"
            elif build_status == FM_STATUS_BUILD_TOKEN_EXPIRED:
                return "token-expired"
            else:
                return "ready"

        elif global_status == FM_STATUS_GLOBAL_WARNING:
            return "warning"

        elif global_status == FM_STATUS_GLOBAL_ERROR:
            return "error"
        else:
            return "unknown"


class ForemanStatusOut(ElementFilter):
    """
    Converts the objects status to foremans global_status and build_status

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>ForemanStatusOut</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """
    def __init__(self, obj):
        super(ForemanStatusOut, self).__init__(obj)

    def process(self, obj, key, valDict, glue=", "):
        if type(valDict[key]['value']) is not None and len(valDict[key]['value']):
            global_status, build_status = ForemanStatusOut.convert(valDict[key]['value'][0])
            if global_status is not None:
                valDict['global_status']['value'] = [global_status]
                valDict['global_status']['skip_save'] = True
            if build_status is not None:
                valDict['build_status']['value'] = [build_status]
                valDict['build_status']['skip_save'] = True
        return key, valDict

    @staticmethod
    def convert(status):
        if status == "ready":
            return FM_STATUS_GLOBAL_OK, FM_STATUS_BUILD
        elif status == "pending":
            return FM_STATUS_GLOBAL_OK, FM_STATUS_BUILD_PENDING
        elif status == "warning":
            return FM_STATUS_GLOBAL_WARNING, FM_STATUS_BUILD
        elif status == "error":
            return FM_STATUS_GLOBAL_ERROR, FM_STATUS_BUILD
        else:
            return None, None


class ForemanHostGroupIn(ElementFilter):
    """
    just maps the incoming foreman attribute hostgroup_id into the attribute groupMembership

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>ForemanHostGroupIn</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """
    def __init__(self, obj):
        super(ForemanHostGroupIn, self).__init__(obj)

    def process(self, obj, key, valDict, glue=", "):
        if type(valDict[key]['value']) is not None and len(valDict[key]['value']):
            valDict['groupMembership']['value'] = [str(i) for i in valDict[key]['value']]
        return key, valDict


class ForemanHostGroupOut(ElementFilter):
    """
    just maps the groupMembership value to foremans attribute hostgroup_id

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>ForemanHostGroupOut</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """
    def __init__(self, obj):
        super(ForemanHostGroupOut, self).__init__(obj)

    def process(self, obj, key, valDict, glue=", "):
        if type(valDict['groupMembership']['value']) is not None and len(valDict['groupMembership']['value']):
            valDict[key]['value'] = [int(i) for i in valDict['groupMembership']['value']]
        return key, valDict