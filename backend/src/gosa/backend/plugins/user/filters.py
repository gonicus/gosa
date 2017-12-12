# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import base64
import os
import shutil
from PIL import Image
from PIL import ImageOps #@UnresolvedImport
from gosa.common import Environment
from gosa.backend.objects.filter import ElementFilter
from gosa.backend.exceptions import ElementFilterException
from gosa.common.components import PluginRegistry
from gosa.common.env import make_session, declarative_base
from gosa.common.error import GosaErrorHandler as C
from gosa.common.utils import N_
from io import BytesIO
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, and_, Sequence, ForeignKey
from sqlalchemy.exc import OperationalError

Base = declarative_base()

# Register the errors handled  by us
C.register_codes(dict(
    USER_IMAGE_CACHE_BROKEN=N_("Invalid image cache"),
    USER_IMAGE_SIZE_MISSING=N_("Image sizes not specified")))


class ImageSize(Base):
    __tablename__ = 'image-sizes'

    id = Column(Integer, Sequence('size_id_seq'), primary_key=True, nullable=False)
    uuid = Column(String(36), ForeignKey('image-index.uuid'))
    size = Column(Integer)
    path = Column(String)

    def __repr__(self):  # pragma: nocover
        return "<ImageSize(uuid='%s', path='%s', size='%d')>" % (self.uuid, self.path, self.size)


class ImageIndex(Base):
    __tablename__ = 'image-index'

    uuid = Column(String(36), primary_key=True)
    attribute = Column(String(64))
    modified = Column(DateTime)
    images = relationship("ImageSize", order_by=ImageSize.size)

    def __repr__(self):  # pragma: nocover
        return "<ImageIndex(uuid='%s', attribute='%s')>" % (self.uuid, self.attribute)


Base.metadata.create_all(Environment.getInstance().getDatabaseEngine("backend-database"))


class ImageProcessor(ElementFilter):
    """
    Generate a couple of pre-sized images and place them in the cache.
    """
    def __init__(self, obj):
        super(ImageProcessor, self).__init__(obj)

        env = Environment.getInstance()
        self.__path = env.config.get("user.image-path", "/var/lib/gosa/images")

    def process(self, obj, key, valDict, *sizes):

        # Sanity check
        if len(sizes) == 0:
            raise ElementFilterException(C.make_error("USER_IMAGE_SIZE_MISSING"))
        
        with make_session() as session:
            # Do we have an attribute to process?
            if key in valDict:
    
                if valDict[key]['value']:
    
                    # Check if a cache entry exists...
                    try:
                        entry = session.query(ImageIndex).filter(and_(ImageIndex.uuid == obj.uuid, ImageIndex.attribute == key)).one_or_none()
                    except OperationalError:
                        session.rollback()
                        Base.metadata.create_all(Environment.getInstance().getDatabaseEngine("backend-database"))
                        entry = None
    
                    if entry:
    
                        # Nothing to do if it's unmodified
                        if obj.modifyTimestamp == entry.modified:
                            return key, valDict
    
                    # Create new cache entry
                    else:
                        entry = ImageIndex(uuid=obj.uuid, attribute=key)
                        session.add(entry)
    
                    # Convert all images to all requested sizes
                    entry.modified = obj.modifyTimestamp
    
                    for idx in range(0, len(valDict[key]['value'])):
                        image = BytesIO(valDict[key]['value'][idx].get())
                        try:
                            im = Image.open(image) #@UndefinedVariable
                        except IOError:
                            continue
    
                        # Check for target directory
                        wd = os.path.join(self.__path, obj.uuid, key, str(idx))
                        if os.path.exists(wd) and not os.path.isdir(wd):
                            raise ElementFilterException(C.make_error("USER_IMAGE_CACHE_BROKEN"))
                        if not os.path.exists(wd):
                            os.makedirs(wd)
    
                        for size in sizes:
                            wds = os.path.join(wd, size + ".jpg")
                            s = int(size)
                            tmp = ImageOps.fit(im, (s, s), Image.ANTIALIAS) #@UndefinedVariable
                            tmp.save(wds, "JPEG")
    
                            # Save size reference if not there yet
                            try:
                                se = session.query(ImageSize.size).filter(and_(ImageSize.uuid == obj.uuid, ImageSize.size == s)).one_or_none()
                            except OperationalError:
                                Base.metadata.create_all(Environment.getInstance().getDatabaseEngine("backend-database"))
                                se = None
                            if not se:
                                se = ImageSize(uuid=obj.uuid, size=s, path=wds)
                                session.add(se)
    
                    # Flush
                    session.commit()
    
                elif 'last_value' in valDict[key] and valDict[key]['last_value']:
    
                    # Delete from db index
                    try:
                        entry = session.query(ImageIndex).filter(and_(ImageIndex.uuid == obj.uuid, ImageIndex.attribute == key)).one_or_none()
                        if entry is not None:
                            session.delete(entry)
                    except OperationalError:
                        pass
    
                    # delete from file system
                    for idx in range(0, len(valDict[key]['last_value'])):
    
                        # Check for target directory
                        wd = os.path.join(self.__path, obj.uuid, key, str(idx))
                        if os.path.exists(wd) and os.path.isdir(wd):
                            # delete
                            shutil.rmtree(wd)
    
                    # Flush
                    session.commit()

        return key, valDict


class LoadDisplayNameState(ElementFilter):
    """
    Detects the state of the autoDisplayName attribute
    """
    def __init__(self, obj):
        super(LoadDisplayNameState, self).__init__(obj)

    def process(self, obj, key, valDict):

        # No displayName set right now
        if not(len(valDict['displayName']['value'])):
            valDict[key]['value'] = [True]
            return key, valDict

        # Check if current displayName value would match the generated one
        # We will then assume that this user wants to auto update his
        # displayName entry.
        displayName = GenerateDisplayName.generateDisplayName(valDict)
        if displayName == valDict['displayName']['value'][0]:
            valDict[key]['value'] = [True]
            return key, valDict

        # No auto displayName
        valDict[key]['value'] = [False]
        return key, valDict


class GenerateDisplayName(ElementFilter):
    """
    An object filter which automatically generates the displayName entry.
    """
    def __init__(self, obj):
        super(GenerateDisplayName, self).__init__(obj)

    def process(self, obj, key, valDict):
        """
        The out-filter that generates the new displayName value
        """
        # Only generate gecos if the the autoGECOS field is True.
        if len(valDict["autoDisplayName"]['value']) and (valDict["autoDisplayName"]['value'][0]):
            gecos = GenerateDisplayName.generateDisplayName(valDict)
            valDict["displayName"]['value'] = [gecos]

        return key, valDict

    @staticmethod
    def generateDisplayName(valDict):
        """
        This method genereates a new displayName value out of the given properties list.
        """

        sn = ""
        givenName = ""

        if len(valDict["sn"]['value']) and (valDict["sn"]['value'][0]):
            sn = valDict["sn"]['value'][0]
        if len(valDict["givenName"]['value']) and (valDict["givenName"]['value'][0]):
            givenName = valDict["givenName"]['value'][0]

        return "%s %s" % (givenName, sn)


class MarshalLogonScript(ElementFilter):
    """
    Create logon script entry from required attributes. Syntax is
    scriptName|scriptLast_scriptUserEditable|scriptPriority|script(base64 encoded)
    """

    def process(self, obj, key, valDict):
        valDict[key]["value"] = []
        for index, script in enumerate(valDict["script"]["value"]):
            valDict[key]["value"].append("%s|%s%s|%s|%s" % (
                valDict["scriptName"]["value"][index] if len(valDict["scriptName"]["value"]) > index else "",
                "O" if len(valDict["scriptUserEditable"]["value"]) > index and valDict["scriptUserEditable"]["value"][index] is True else "",
                "L" if len(valDict["scriptLast"]["value"]) > index and valDict["scriptLast"]["value"][index] is True else "",
                valDict["scriptPriority"]["value"][index] if len(valDict["scriptPriority"]["value"]) > index else "",
                base64.b64encode(script.encode("utf-8")).decode()
            ))

        return key, valDict


class UnmarshalLogonScript(ElementFilter):
    """
    Extract marshalled
    scriptName|scriptLast_scriptUserEditable|scriptPriority|script(base64 encoded)
    """

    def process(self, obj, key, valDict):
        # initialize values
        for name in ["scriptName", "scriptLast", "scriptUserEditable", "scriptPriority", "script"]:
            valDict[name]["value"] = []

        for index, logon in enumerate(valDict[key]["value"]):
            parts = logon.split("|")
            if len(parts) == 4:
                valDict["scriptName"]["value"].append(parts[0])
                valDict["scriptLast"]["value"].append("L" in parts[1])
                valDict["scriptUserEditable"]["value"].append("O" in parts[1])
                if len(parts[2]):
                    valDict["scriptPriority"]["value"].append(int(parts[2]))
                else:
                    valDict["scriptPriority"]["value"].append(0)
                if len(parts[3]):
                    valDict["script"]["value"].append(base64.b64decode(parts[3]).decode())
                else:
                    valDict["script"]["value"].append("")

        return key, valDict


class IsMemberOfAclRole(ElementFilter):
    """
    Check is a user (identified by the values in the uidAttribute) is part of the given ACLRole
    """

    def process(self, obj, key, valDict, uidAttribute, role_name):
        if uidAttribute in valDict:
            acl = PluginRegistry.getInstance("ACLResolver")
            res = []
            for uid in valDict[uidAttribute]["value"]:
                if role_name.lower() == "admin":
                    res.append(acl.isAdmin(uid))
                else:
                    res.append(acl.is_member_of_role(uid, role_name))
            valDict[key]["value"] = res
        return key, valDict


class UpdateMemberOfAclRole(ElementFilter):
    """
    Add a user to a ACLRole if the references attribute value is True or remove it if False
    """
    def process(self, obj, key, valDict, uidAttribute, role_name):
        acl = PluginRegistry.getInstance("ACLResolver")
        for idx, val in enumerate(valDict[key]["value"]):
            uid = valDict[uidAttribute]["value"][idx]
            if role_name.lower() == "admin":
                if acl.isAdmin(uid) != val:
                    acl.changeAdmin(None, uid, val)
            elif acl.is_member_of_role(uid, role_name) != val:
                if val is True:
                    acl.add_member_to_role(role_name, uid)
                else:
                    acl.remove_member_from_role(role_name, uid)
        return key, valDict