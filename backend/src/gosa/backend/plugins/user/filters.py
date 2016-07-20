# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import os
from PIL import Image
from PIL import ImageOps #@UnresolvedImport
from gosa.common import Environment
from gosa.backend.objects.filter import ElementFilter
from gosa.backend.exceptions import ElementFilterException
from gosa.common.error import GosaErrorHandler as C
from gosa.common.utils import N_
from io import BytesIO
from sqlalchemy.ext.declarative import declarative_base
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


class ImageProcessor(ElementFilter):
    """
    Generate a couple of pre-sized images and place them in the cache.
    """
    def __init__(self, obj):
        super(ImageProcessor, self).__init__(obj)

        env = Environment.getInstance()
        self.__session = env.getDatabaseSession("backend-database")
        self.__path = env.config.get("user.image-path", "/var/lib/gosa/images")

    def process(self, obj, key, valDict, *sizes):

        # Sanity check
        if len(sizes) == 0:
            raise ElementFilterException(C.make_error("USER_IMAGE_SIZE_MISSING"))

        # Do we have an attribute to process?
        if key in valDict and valDict[key]['value']:

            # Check if a cache entry exists...
            try:
                entry = self.__session.query(ImageIndex).filter(and_(ImageIndex.uuid == obj.uuid, ImageIndex.attribute == key)).one_or_none()
            except OperationalError:
                Base.metadata.create_all(Environment.getInstance().getDatabaseEngine("backend-database"))
                entry = None

            if entry:

                # Nothing to do if it's unmodified
                if obj.modifyTimestamp == entry.modified:
                    return key, valDict

            # Create new cache entry
            else:
                entry = ImageIndex(uuid=obj.uuid, attribute=key)
                self.__session.add(entry)

            # Convert all images to all requested sizes
            entry.modified = obj.modifyTimestamp

            for idx in range(0, len(valDict[key]['value'])):
                image = BytesIO(valDict[key]['value'][idx].get())
                try:
                    im = Image.open(image) #@UndefinedVariable
                except IOError:
                    continue

                # Check for target directory
                wd = os.path.join(self.__path, obj.uuid)
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
                        se = self.__session.query(ImageSize.size).filter(and_(ImageSize.uuid == obj.uuid, ImageSize.size == s)).one_or_none()
                    except OperationalError:
                        Base.metadata.create_all(Environment.getInstance().getDatabaseEngine("backend-database"))
                        se = None
                    if not se:
                        se = ImageSize(uuid=obj.uuid, size=s, path=wds)
                        self.__session.add(se)

            # Flush
            self.__session.commit()

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
