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
                <param>model_attribute</param>
            </Filter>
        </FilterEntry>
        ...

    """
    def __init__(self, obj):
        super(GetMakeModelFromPPD, self).__init__(obj)

    def process(self, obj, key, valDict, make_attribute, model_attribute):
        ppd_file = valDict[key]['value'][0] if len(valDict[key]['value']) else None
        if ppd_file is not None:
            cups = PluginRegistry.getInstance("CupsClient")
            res = cups.get_attributes_from_ppd(ppd_file, ["Manufacturer", "ModelName"])
            if make_attribute in valDict:
                valDict[make_attribute] = res["Manufacturer"]
            if model_attribute in valDict:
                valDict[model_attribute] = res["ModelName"]

        return key, valDict

