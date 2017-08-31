import os

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
            res = cups.get_attributes_from_ppd(ppd_file, ["Manufacturer", "NickName"])

            if "Manufacturer" in res:
                if make_attribute is not None and make_attribute in valDict:
                    if len(valDict[make_attribute]['value']) == 0 or override == "true":
                        valDict[make_attribute]['value'] = [res["Manufacturer"]]

                if server_ppd_attribute is not None and server_ppd_attribute in valDict and "NickName" in res:
                    for ppd, entry in cups.getPrinterModels(res["Manufacturer"]).items():
                        if entry["value"] == res["NickName"]:
                            if len(valDict[make_attribute]['value']) == 0 or override == "true":
                                valDict[server_ppd_attribute]['value'] = [ppd]
                            break

        return key, valDict


class DeleteOldFile(ElementFilter):
    """
    Delete old file if value has changed and there is only one reference left to the file (from the current object).
    This filter should be used as OutFilter only.

     e.g.:

    .. code-block: xml

        <OutFilter>
            <FilterChain>
                ...
                <FilterEntry>
                    <Filter>
                        <Name>DeleteOldFile</Name>
                    </Filter>
                </FilterEntry>
                ...
            </FilterChain>
            ...
        </OutFilter>

    """
    def __init__(self, obj):
        super(DeleteOldFile, self).__init__(obj)

    def process(self, obj, key, valDict, *args):
        old_file = valDict[key]['orig_value'] if valDict[key]['orig_value'] != valDict[key]['value'] else None
        if old_file is not None:
            for file in old_file:
                if os.path.exists(file) and os.access(file, os.F_OK):
                    # check if there is only one remaining link left to this file (the current object)
                    index = PluginRegistry.getInstance("ObjectIndex")
                    res = index.search({key: old_file}, {"dn": 1})
                    if len(res) >= 1:
                        os.unlink(file)

        return key, valDict