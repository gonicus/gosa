# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.plugins.password.interface import PasswordMethod
import crypt
import random
import string
import re


class PasswordMethodCrypt(PasswordMethod):
    """
    Crypt password method.  It support the following hashing-methods:

       * crypt/standard-des
       * crypt/enhanced-des
       * crypt/md5
       * crypt/blowfish
    """

    hash_name = "CRYPT"

    def isLockable(self, hash_value):
        """
        See PasswordMethod Interface for details
        """
        if not hash_value:
            return False

        return not self.is_locked(hash_value)

    def isUnlockable(self, hash_value):
        """
        See PasswordMethod Interface for details
        """
        if not hash_value:
            return False

        return self.is_locked(hash_value)

    def is_responsible_for_password_hash(self, password_hash):
        """
        See PasswordMethod Interface for details
        """
        if re.match("^\{%s\}" % self.hash_name, password_hash.decode()):
            return True
        return False

    def detect_hash_method(self, password_hash):
        """
        See PasswordMethod Interface for details
        """
        if not self.is_responsible_for_password_hash(password_hash):
            return None

        password_hash = re.sub('^{[^}]+}!?', '', password_hash.decode())
        if re.match(r'^[a-zA-Z0-9.\\/][a-zA-Z0-9.\\/]', password_hash):
            return crypt.METHOD_CRYPT

        if re.match(r'^\$5\$', password_hash):
            return crypt.METHOD_SHA256

        if re.match(r'^\$6\$', password_hash):
            return crypt.METHOD_SHA512

        if re.match(r'^\$1\$', password_hash):
            return crypt.METHOD_MD5

        return None

    def is_locked(self, password_hash):
        """
        See PasswordMethod Interface for details
        """
        return re.match("\{[^\}]*\}!", password_hash) is not None

    def lock_account(self, password_hash):
        """
        See PasswordMethod Interface for details
        """
        return re.sub("\{([^\}]*)\}!?", "{\\1}!", password_hash)

    def unlock_account(self, password_hash):
        """
        See PasswordMethod Interface for details
        """
        return re.sub("\{([^\}]*)\}!?", "{\\1}", password_hash)

    def get_hash_names(self):
        """
        See PasswordMethod Interface for details
        """
        return crypt.methods

    def generate_password_hash(self, new_password, method=None):
        """
        See PasswordMethod Interface for details
        """
        return u"{%s}%s" % (self.hash_name, crypt.crypt(new_password, crypt.mksalt(method)))
