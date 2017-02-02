# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from gosa.common.error import GosaErrorHandler as C


class PasswordMethod(object):  # pragma: nocover
    """
    The interface all password-methods should use.
    """
    hash_name = None

    def isLockable(self, hash_value):
        """
        Tells whether the password hash can be locked or not
        """
        return False

    def isUnlockable(self, hash_value):
        """
        Tells whether the password hash can be unlocked or not
        """
        return False

    def is_locked(self, hash_value):
        """
        Checks whether the account is locked or not.
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="is_locked"))

    def lock_account(self, hash_value):
        """
        Locks the given account.
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="lock_account"))

    def unlock_account(self, hash_value):
        """
        Unlocks the given account.
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="unlock_account"))

    def get_hash_names(self):
        """
        Returns a list of hashing-mechanisms that are supported by the password method.
        """
        return [self.hash_name]

    def is_responsible_for_password_hash(self, password_hash):
        """
        Checks whether this class is responsible for this kind of password hashes or not.
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="is_responsible_for_password_hash"))

    def generate_password_hash(self, new_password, method=None):
        """
        Generates a password hash for the given password and method
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="generate_password_hash"))

    def compare_hash(self, new_password, complete_hash):
        """
        Checks whether the given new_password is the same as the encrypted one
        """
        raise NotImplementedError(C.make_error('NOT_IMPLEMENTED', method="compare_hash"))