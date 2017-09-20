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

    .. code-block: xml

        <FilterEntry>
            <Filter>
                <Name>ForemanStatusIn</Name>
            </Filter>
        </FilterEntry>
        ...

    """
    def __init__(self, obj):
        super(ForemanStatusIn, self).__init__(obj)

    def process(self, obj, key, valDict, glue=", "):
        global_status = valDict['global_status']['value'][0] if len(valDict['global_status']['value']) else None
        build_status = valDict['build_status']['value'][0] if len(valDict['build_status']['value']) else None
        if global_status is not None or build_status is not None:
            status = ForemanStatusIn.convert(global_status, build_status)
            valDict["status"]['value'] = [status]

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
