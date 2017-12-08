import logging
import os

from tornado import gen

from gosa.backend.components.httpd import get_server_url
from gosa.backend.objects.filter import ElementFilter
from gosa.backend.plugins.cups.main import get_local_ppd_path
from gosa.common.components import PluginRegistry


class PPDFilters(ElementFilter):

    def __init__(self, obj):
        super(PPDFilters, self).__init__(obj)
        self.log = logging.getLogger(__name__)

    def get_ppd_type(self, url):
        """
        Determines the PPD type from its URL. Can be either:
        1. Remote URL (points to a foreign server)
        2. Lokal URL (points to the local CUPS server)
        """
        server_url = get_server_url()
        return "local" if url[0:len(server_url)] == server_url else "remote"

    def get_local_ppd_path(self, url):
        if self.get_ppd_type(url) == "local":
            # remove server path
            http_part = "%s/ppd/modified/" % get_server_url()
            return url[len(http_part):]

        return None


class GetMakeModelFromPPD(PPDFilters):
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

    def process(self, obj, key, valDict, make_attribute=None, server_ppd_attribute=None, override="false"):
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


class DeleteOldFile(PPDFilters):
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

    def process(self, obj, key, valDict, *args):
        old_file = valDict[key]['orig_value'] if valDict[key]['orig_value'] != valDict[key]['value'] else None
        if old_file is not None:
            for file in old_file:
                path = get_local_ppd_path(file)
                if path is not None and os.path.exists(path) and os.access(path, os.F_OK):
                    # check if there is only one remaining link left to this file (the current object)
                    index = PluginRegistry.getInstance("ObjectIndex")
                    res = index.search({key: old_file}, {"dn": 1})
                    if len(res) <= 1:
                        self.log.debug("deleting old PPD file: %s" % path)
                        os.unlink(path)

        return key, valDict


class GetPPDUrl(PPDFilters):
    """ Create an URL to a PPD depending on the current configuration state"""

    def process(self, obj, key, valDict, *args):
        if True not in valDict["configured"]["value"]:
            # a customized URL has not been written -> get the server PPD and write that one
            client = PluginRegistry.getInstance("CupsClient")
            res = client.writePPD(valDict["cn"]["value"][0], valDict["serverPPD"]["value"][0], None, {})
            valDict[key]["value"] = res["gotoPrinterPPD"]
            self.log.debug("default PPD written to %s" % res["gotoPrinterPPD"])

        return key, valDict