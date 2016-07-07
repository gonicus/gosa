# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from passlib.hash import lmhash, nthash
import gettext
from pkg_resources import resource_filename #@UnresolvedImport
from datetime import date, datetime
from time import mktime
from gosa.common.utils import N_
from zope.interface import implementer
from gosa.common.components import Plugin
from gosa.common.handler import IInterfaceHandler
from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.components import Command
from gosa.backend.objects.proxy import ObjectProxy
from gosa.backend.objects.comparator import ElementComparator
from gosa.backend.exceptions import ACLException
from gosa.common.error import GosaErrorHandler as C

@implementer(IInterfaceHandler)
class SambaGuiMethods(Plugin):
    _target_ = 'gosa'
    _priority_ = 80

    def __init__(self):
        self.__log = Environment.getInstance().log


    @Command(needsUser=True, __help__=N_("Sets a new samba-password for a user"))
    def setSambaPassword(self, user, object_dn, password):
        """
        Set a new samba-password for a user
        """

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "sambaNTPassword")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):
            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "sambaLMPassword")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):
            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Set the password and commit the changes
        user = ObjectProxy(object_dn)
        user.sambaNTPassword = nthash.encrypt(password)
        user.sambaLMPassword = lmhash.encrypt(password)
        user.commit()

    @Command(needsUser=True, __help__=N_("Returns the current samba domain policy for a given user"))
    def getSambaDomainInformation(self, user, target_object, locale=None):
        print("-------> ACL check for user", user)
        print(target_object)

        # Do we have a locale?
        if locale is None:
            locale = "C"

        t = gettext.translation('messages', resource_filename('gosa.backend', "locale"),
            fallback=True, languages=[locale])

        tr = t.gettext
        trn = t.ngettext

        # Use proxy if available
        _self = target_object

        sambaMinPwdLength = "unset"
        sambaPwdHistoryLength = "unset"
        sambaLogonToChgPwd = "unset"
        sambaMaxPwdAge = "unset"
        sambaMinPwdAge = "unset"
        sambaLockoutDuration = "unset"
        sambaLockoutThreshold = "unset"
        sambaForceLogoff = "unset"
        sambaRefuseMachinePwdChange = "unset"
        sambaPwdLastSet = "unset"
        sambaLogonTime = "unset"
        sambaLogoffTime = "unset"
        sambaKickoffTime = "unset"
        sambaPwdCanChange = "unset"
        sambaPwdMustChange = "unset"
        sambaBadPasswordCount = "unset"
        sambaBadPasswordTime = "unset"

        # Domain attributes
        domain_attributes = ["sambaMinPwdLength","sambaPwdHistoryLength","sambaMaxPwdAge",
                "sambaMinPwdAge","sambaLockoutDuration","sambaRefuseMachinePwdChange",
                "sambaLogonToChgPwd","sambaLockoutThreshold","sambaForceLogoff"]

        # User attributes
        user_attributes = ["sambaBadPasswordTime","sambaPwdLastSet","sambaLogonTime","sambaLogoffTime",
                "sambaKickoffTime","sambaPwdCanChange","sambaPwdMustChange","sambaBadPasswordCount", "sambaSID"]

        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': _self.sambaDomainName}, dict(zip(domain_attributes, [1 for n in domain_attributes])))
        if not len(res):
            return("invalid domain selected")

        attrs = {}
        for item in domain_attributes:
            if item in res[0]:
                try:
                    attrs[item] = int(res[0][item][0])
                except:
                    attrs[item] = "unset"
            else:
                attrs[item] = "unset"

        for item in user_attributes:
            if getattr(_self, item):
                try:
                    if type(getattr(_self, item)) == datetime:
                        attrs[item] =  mktime(getattr(_self, item).timetuple())
                    else:
                        attrs[item] = int(getattr(_self, item))
                except Exception as e:
                    attrs[item] = "unset"
            else:
                attrs[item] = "unset"

        if attrs['sambaPwdMustChange'] and attrs['sambaPwdMustChange'] != "unset":
            attrs['sambaPwdMustChange'] = date.fromtimestamp(attrs['sambaPwdMustChange']).strftime("%d.%m.%Y")
        if attrs['sambaKickoffTime'] and attrs['sambaKickoffTime'] != "unset":
            attrs['sambaKickoffTime'] = date.fromtimestamp(attrs['sambaKickoffTime']).strftime("%d.%m.%Y")

        # sambaMinPwdLength: Password length has a default of 5
        if attrs['sambaMinPwdLength'] == "unset" or attrs['sambaMinPwdLength'] == 5:
            attrs['sambaMinPwdLength'] = "5 <i>(" + tr(N_("default")) + ")</i>"

        # sambaPwdHistoryLength: Length of Password History Entries (default: 0 => off)
        if attrs['sambaPwdHistoryLength'] == "unset" or attrs['sambaPwdHistoryLength'] == 0:
            attrs['sambaPwdHistoryLength'] = tr(N_("off")) + " <i>(" + tr(N_("default")) + ")</i>"

        # sambaLogonToChgPwd: Force Users to logon for password change (default: 0 => off, 2 => on)
        if attrs['sambaLogonToChgPwd'] == "unset" or attrs['sambaLogonToChgPwd'] == 0:
            attrs['sambaLogonToChgPwd'] = tr(N_("off")) + " <i>(" + t.gettext(N_("default")) + ")</i>"
        else:
            attrs['sambaLogonToChgPwd'] = tr(N_("on"))

        # sambaMaxPwdAge: Maximum password age, in seconds (default: -1 => never expire passwords)'
        if attrs['sambaMaxPwdAge'] == "unset" or attrs['sambaMaxPwdAge'] <= 0:
            attrs['sambaMaxPwdAge'] = tr(N_("disabled")) + " <i>(" + tr(N_("default")) + ")</i>"
        else:
            attrs['sambaMaxPwdAge'] += " " + trn(N_("second"), N_("seconds"), int(attrs['sambaMaxPwdAge']))

        # sambaMinPwdAge: Minimum password age, in seconds (default: 0 => allow immediate password change
        if attrs['sambaMinPwdAge'] == "unset" or attrs['sambaMinPwdAge'] <= 0:
            attrs['sambaMinPwdAge'] = tr(N_("disabled")) + " <i>(" + tr(N_("default")) + ")</i>"
        else:
            attrs['sambaMinPwdAge'] += " " + trn(N_("second"), N_("seconds"), int(attrs['sambaMinPwdAge']))

        # sambaLockoutDuration: Lockout duration in minutes (default: 30, -1 => forever)
        if attrs['sambaLockoutDuration'] == "unset" or attrs['sambaLockoutDuration'] == 30:
            attrs['sambaLockoutDuration'] = "30 " + tr(N_("minutes")) + " <i>(" + tr(N_("default")) + ")</i>"
        elif attrs['sambaLockoutDuration'] == -1:
            attrs['sambaLockoutDuration'] = tr(N_("unlimited"))
        else:
            attrs['sambaLockoutDuration'] += " " + trn(N_("minute"), N_("minutes"), int(attrs['sambaLockoutDuration']))

        # sambaLockoutThreshold: Lockout users after bad logon attempts (default: 0 => off
        if attrs['sambaLockoutThreshold'] == "unset" or attrs['sambaLockoutThreshold'] == 0:
            attrs['sambaLockoutThreshold'] = tr(N_("disabled")) + " <i>(" + tr(N_("default")) + ")</i>"

        # sambaForceLogoff: Disconnect Users outside logon hours (default: -1 => off, 0 => on
        if attrs['sambaForceLogoff'] == "unset" or attrs['sambaForceLogoff'] == -1:
            attrs['sambaForceLogoff'] = tr(N_("off")) + " <i>(" + tr(N_("default")) + ")</i>"
        else:
            attrs['sambaForceLogoff'] = tr(N_("on"))

        # sambaRefuseMachinePwdChange: Allow Machine Password changes (default: 0 => off
        if attrs['sambaRefuseMachinePwdChange'] == "unset" or attrs['sambaRefuseMachinePwdChange'] == 0:
            attrs['sambaRefuseMachinePwdChange'] = tr(N_("off")) + " <i>(" + tr(N_("default")) + ")</i>"
        else:
            attrs['sambaRefuseMachinePwdChange'] = tr(N_("on"))

        # sambaBadPasswordTime: Time of the last bad password attempt
        if attrs['sambaBadPasswordTime'] == "unset" or not attrs['sambaBadPasswordTime']:
            attrs['sambaBadPasswordTime'] = "<i>(" + tr(N_("not set")) + ")</i>"
        else:
            attrs['sambaBadPasswordTime'] = date.fromtimestamp(attrs['sambaBadPasswordTime']).strftime("%d.%m.%Y")

        # sambaBadPasswordCount: Bad password attempt count
        if attrs['sambaBadPasswordCount'] == "unset" or not attrs['sambaBadPasswordCount']:
            attrs['sambaBadPasswordCount'] = "<i>(" + tr(N_("not set")) + ")</i>"
        else:
            attrs['sambaBadPasswordCount'] = date.fromtimestamp(attrs['sambaBadPasswordCount']).strftime("%d.%m.%Y")

        # sambaPwdLastSet: Timestamp of the last password update
        if attrs['sambaPwdLastSet'] == "unset" or not attrs['sambaPwdLastSet']:
            attrs['sambaPwdLastSet'] = "<i>(" + tr(N_("not set")) + ")</i>"
        else:
            attrs['sambaPwdLastSet'] = date.fromtimestamp(attrs['sambaPwdLastSet']).strftime("%d.%m.%Y")

        # sambaLogonTime: Timestamp of last logon
        if attrs['sambaLogonTime'] == "unset" or not attrs['sambaLogonTime']:
            attrs['sambaLogonTime'] = "<i>(" + tr(N_("not set")) + ")</i>"
        else:
            attrs['sambaLogonTime'] = date.fromtimestamp(attrs['sambaLogonTime']).strftime("%d.%m.%Y")

        # sambaLogoffTime: Timestamp of last logoff
        if attrs['sambaLogoffTime'] == "unset" or not attrs['sambaLogoffTime']:
            attrs['sambaLogoffTime'] = "<i>(" + tr(N_("not set")) + ")</i>"
        else:
            attrs['sambaLogoffTime'] = date.fromtimestamp(attrs['sambaLogoffTime']).strftime("%d.%m.%Y")

        # sambaKickoffTime: Timestamp of when the user will be logged off automatically
        if attrs['sambaKickoffTime'] == "unset" or not attrs['sambaKickoffTime']:
            attrs['sambaKickoffTime'] = "<i>(" + tr(N_("not set")) + ")</i>"

        # sambaPwdMustChange: Timestamp of when the password will expire
        if attrs['sambaPwdMustChange'] == "unset" or not attrs['sambaPwdMustChange']:
            attrs['sambaPwdMustChange'] = "<i>(" + tr(N_("not set")) + ")</i>"

        # sambaPwdCanChange: Timestamp of when the user is allowed to update the password
        time_now = mktime(datetime.now().timetuple())
        if attrs['sambaPwdCanChange'] == "unset" or not attrs['sambaPwdCanChange']:
            attrs['sambaPwdCanChange'] = "<i>(" + tr(N_("not set")) + ")</i>"
        elif attrs['sambaPwdCanChange'] != "unset" and time_now > attrs['sambaPwdCanChange']:
            attrs['sambaPwdCanChange'] = tr(N_("immediately"))
        else:
            days = int((attrs['sambaPwdCanChange'] - time_now) / (60*60*24))
            hours = int(((attrs['sambaPwdCanChange'] - time_now) / (60*60)) % 24)
            minutes = int(((attrs['sambaPwdCanChange'] - time_now) / (60)) % 60)
            attrs['sambaPwdCanChange'] = " " + days    + " " + trn(N_("day"), N_("days"), days)
            attrs['sambaPwdCanChange']+= " " + hours   + " " + trn(N_("hour"), N_("hours"), hours)
            attrs['sambaPwdCanChange']+= " " + minutes + " " + trn(N_("minute"), N_("minutes"), minutes)

        res = "\n<div style='overflow: auto;'>" + \
            "\n<table style='width:100%;'>" + \
            "\n<tr><td><b>" + tr(N_("Domain attributes")) + "</b></td></tr>" + \
            "\n<tr><td>" + tr(N_("Minimum password length")) + ":           </td><td>" + attrs['sambaMinPwdLength'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Password history")) + ":              </td><td>" + attrs['sambaPwdHistoryLength'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Force password change")) + ":         </td><td>" + attrs['sambaLogonToChgPwd'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Maximum password age")) + ":          </td><td>" + attrs['sambaMaxPwdAge'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Minimum password age")) + ":          </td><td>" + attrs['sambaMinPwdAge'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Lockout duration")) + ":              </td><td>" + attrs['sambaLockoutDuration'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Number of bad lockout attempts")) + ":           </td><td>" + attrs['sambaLockoutThreshold'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Disconnect time")) + ":               </td><td>" + attrs['sambaForceLogoff'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Refuse machine password change")) + ":</td><td>" + attrs['sambaRefuseMachinePwdChange'] + "</td></tr>" + \
            "\n<tr><td>&nbsp;</td></tr>" + \
            "\n<tr><td><b>" + tr(N_("User attributes")) + "</b></td></tr>" + \
            "\n<tr><td>" + tr(N_("SID")) + ":                           </td><td>" + str(attrs['sambaSID']) + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Last failed login")) + ":             </td><td>" + attrs['sambaBadPasswordTime'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Log on attempts")) + ":                </td><td>"+ attrs['sambaBadPasswordCount'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Last password update")) + ":          </td><td>" + attrs['sambaPwdLastSet'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Last log on")) + ":                    </td><td>"+ attrs['sambaLogonTime'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Last log off")) + ":                   </td><td>"+ attrs['sambaLogoffTime'] + "</td></tr>" + \
            "\n<tr><td>" + tr(N_("Automatic log off")) + ":              </td><td>"+ attrs['sambaKickoffTime'] + "</td></tr>";

        return res


class IsValidSambaDomainName(ElementComparator):
    """
    Validates a given sambaDomainName.
    """

    def __init__(self, obj):
        super(IsValidSambaDomainName, self).__init__()

    def process(self, all_props, key, value):
        domain = value[0]
        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': domain},
            {'_uuid': 1})
        print(res)
        if len(res):
            return True, errors

        errors.append(dict(index=0, detail=N_("Unknown domain '%(domain)s'"), domain=value[0]))

        return False, errors
