from gosa.backend.objects.filter import ElementFilter
from gosa.common.components import PluginRegistry


class GetMakeModelFromPPD(ElementFilter):
    """
    read the make and model values from an PPD file and adds it to the

    e.g.:

    .. code-block: xml

        <FilterEntry>
            <Filter>
                <Name>GetMakeModelFromPPD</Name>
                <param>make_attribute</param>
                <param>server_ppd_attribute</param>
            </Filter>
        </FilterEntry>
        ...

    """
    def __init__(self, obj):
        super(GetMakeModelFromPPD, self).__init__(obj)

    def process(self, obj, key, valDict, make_attribute=None, server_ppd_attribute=None, override=False):
        ppd_file = valDict[key]['value'][0] if len(valDict[key]['value']) else None
        if ppd_file is not None:
            cups = PluginRegistry.getInstance("CupsClient")
            res = cups.get_attributes_from_ppd(ppd_file, ["Manufacturer",  "NickName"])
            if make_attribute is not None and make_attribute in valDict:
                if len(valDict[make_attribute]['value']) == 0 or override == "true":
                    valDict[make_attribute]['value'] = [res["Manufacturer"]]

            if server_ppd_attribute is not None and server_ppd_attribute in valDict:
                for ppd, entry in cups.getPrinterModels(res["Manufacturer"]).items():
                    if entry["value"] == res["NickName"]:
                        if len(valDict[make_attribute]['value']) == 0 or override == "true":
                            valDict[server_ppd_attribute]['value'] = [ppd]
                        break

        return key, valDict

