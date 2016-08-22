#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
import sys
import copy
import gettext
import getopt
from getopt import GetoptError
import getpass
#pylint: disable=W0611
from gosa.common.components import JSONServiceProxy
from gosa.common.utils import parseURL

_ = gettext.gettext


print("TODO: ES SIND DIVERSE try/catch Aufrufe auskommentiert...")


class helpDecorator(object):
    """
    A method decorator which allows to mark those methods that can be used
    as script parameters.

    e.g.
        @helpDecorator(_("Short help msg"), _("A longer help message"))

    """
    largeHelp = ""
    smallHelp = ""
    method_list = {}

    def __init__(self, smallHelp, largeHelp=""):
        self.smallHelp = smallHelp
        self.largeHelp = largeHelp

    def __call__(self, func):
        helpDecorator.method_list[func.__name__] = (self.smallHelp, self.largeHelp)
        return func


class ACLAdmin(object):
    """
    This class privides all necessary action for the 'acl-admin' script.

    All script actions will be forwarded to exported gosa commands.
    """

    proxy = None

    def __init__(self, proxy):
        self.proxy = proxy
        self.acl_scope_map = ["sub", "one", "psub", "reset"]

    def printReportHeader(self, string):
        """
        Helper method which prints a header for reports.

        =========== =============
        key         description
        =========== =============
        string      The report caption.
        =========== =============

        """
        print
        print("-" * len(string))
        print(string)
        print("-" * len(string))

    def para_missing(self, name):
        """
        Helper method that shows a warning about a missing required parameter!

        =========== =============
        key         description
        =========== =============
        name        The name of the parameter that was missing.
        =========== =============

        """
        print
        print(_("<%s> parameter is missing!") % name)
        desc = self.get_para_help(name)
        if len(desc):
            print(" %s" % desc)
        print

    def para_invalid(self, name):
        """
        Helper method which prints out a warning method that a parameter
        was passend in an invalid format.

        =========== =============
        key         description
        =========== =============
        name        The name of the parameter we want to print the invalid message for.
        =========== =============
        """

        print()
        print(_("<%s> parameter is invalid!") % name)
        desc = self.get_para_help(name)
        if len(desc):
            print(" %s" % desc)
        print()

    def get_para_help(self, para):
        """
        This method holds a description for all parameters that can be passed to this script.
        Due to the fact that we need the descriptions in several functions, i've put them
         into a single function.

        =========== =============
        key         description
        =========== =============
        para        The name of the parameter we want to get the description for.
        =========== =============
        """

        help_msgs = {
                "dn": _("The dn parameter specifies the location of an acl/role"),
                "base": _("The base parameter specifies the position acls are active for. For example: dc=example,dc=de"),
                "scope": _("The scope value specifies how the acl role influences sub-directories"
                    "\n Possible scope values are:"
                    "\n  one   - For acls that are active only for the current base"
                    "\n          this can be revoked using the 'reset' scope!"
                    "\n  sub   - For acls that are active only for the complete subtree"
                    "\n          this can be revoked using the 'reset' scope!"
                    "\n  psub  - For acls that are active only for the complete subtree"
                    "\n          this can NOT be revoked using the 'reset' scope!"
                    "\n  reset - Revokes previously defined acls, except for those with scope 'psub'"),
                "priority": _("An integer value to prioritize an acl-rule. (Lower values mean higher priority)"
                    "\n  highest priority: -100"
                    "\n  lowest priority: 100"),
                "members": _("The names of the users/clients the acl-rule should be valid for. "
                    "\n  A comma separated list:"
                    "\n   e.g.: hubert,peter,klaus"),
                "acl-definition": _("The <acl-defintion> parameter specifies what actions can be performed on a given topic."
                    "\n"
                    "\n Syntax {<topic>:<acls>:<option1>: ... :<option N>,}"
                    "\n"
                    "\n Command examples:"
                    "\n   A single definition without options:"
                    "\n       '^org\.gosa\..*:crowdsexm'"
                    "\n"
                    "\n   A single definition with options:"
                    "\n       '^org\.gosa\..*:crowdsexm:uid=user_*:tag=event'"
                    "\n"
                    "\n   A multi action defintion"
                    "\n       '^org\.gosa\.events$:crowdsexm,^org\.gosa\.factory$:rw,^org\.gosa\.something$:rw'"
                    "\n"
                    "\n <topic> "
                    "\n ========"
                    "\n The topic defines the target-action this acl includes"
                    "\n Topics are represented by reqular expressions to allow flexible acl definitions."
                    "\n"
                    "\n  e.g.: "
                    "\n   '^org\.gosa\..*'                for all topics included in org.gosa"
                    "\n   '^org\.gosa\.[^\.]*\.help$'      allows to call help methods for modules directly under org.gosa"
                    "\n"
                    "\n <acls>"
                    "\n ======"
                    "\n The acl parameter defines which operations can be executed on a given topic."
                    "\n  e.g.:"
                    "\n   rwcd    -> allows to read, write, create and delete"
                    "\n"
                    "\n  Possible values are:"
                    "\n    r - Read             w - Write           m - Move"
                    "\n    c - Create           d - Delete          s - Search - or beeing found"
                    "\n    x - Execute          e - Receive event"
                    "\n"
                    "\n <options>"
                    "\n ========="
                    "\n Options are additional checks, please read the GOsa documentation for details."
                    "\n The format is:  key:value;key:value;..."
                    "\n  e.g. (Do not forget to use quotes!)"
                    "\n   'uid:peter;eventType:start;'"),
                "rolename": _("The name of the acl role you want to set"),
                "acl-update-action": _("You can specify the upate-action for the acl."
                    "\n  Possible values are:"
                    "\n    * set-scope      Update the scope of an acl-rule"
                    "\n    * set-members    Set a new list of members for an acl-rule"
                    "\n    * set-priority   Set another priority level for the acl-rule"
                    "\n    * set-action     Set a new action for the acl"
                    "\n    * set-role       Let the acl-rule point to a role"),
                "roleacl-update-action": _("You can specify the upate-action for the role-acl."
                    "\n  Possible values are:"
                    "\n    * set-scope      Update the scope of an acl-rule"
                    "\n    * set-priority   Set another priority level for the acl-rule"
                    "\n    * set-action     Set a new action for the acl"
                    "\n    * set-role       Let the acl-rule point to a role"),
                "acl-add-action": _("You can either create acl-rule that contain direkt permissions settings"
                    " or you can use previously defined roles"
                    "\n  Possible values are:"
                    "\n    * with-actions   To directly specify the topic, acls and options this defintions includes"
                    "\n    * with-role      To use a rolename instead of defining actions directly")}

        # Return the help message, if it exists.
        if para in help_msgs:
            return(help_msgs[para])
        else:
            return(_("no help for %s ...") % para)

    def get_value_from_args(self, name, args):
        """
        This method extracts a parameter out of a given argument-list.

        (Due to the fact that we need parameter values in several functions, i've put them
         into a single function)

        =========== =============
        key         description
        =========== =============
        para        The name of the parameter we want to get the value for.
        args        The arguments-list we want to extract from.
        =========== =============
        """

        # Validate the base value
        if name in ["base", "dn"]:
            if len(args):
                base = args[0]
                del(args[0])
                return(base)
            else:
                self.para_missing(name)
                sys.exit(1)

        # Validate the scope value
        elif name == "scope":
            if len(args):
                if args[0] not in self.acl_scope_map:
                    self.para_invalid('scope')
                    sys.exit(1)
                else:
                    scope = args[0]
                    del(args[0])
                    return(scope)
            else:
                self.para_missing('scope')
                sys.exit(1)

        # Check for priority
        elif name == "priority":
            if len(args):
                try:
                    if int(args[0]) < -100 or int(args[0]) > 100:
                        self.para_invalid('priority')
                        sys.exit(1)
                except Exception:
                    self.para_invalid('priority')
                    sys.exit(1)

                prio = int(args[0])
                del(args[0])
                return(prio)
            else:
                self.para_missing('priority')
                sys.exit(1)

        # Check topic
        elif name == "topic":
            if len(args):
                topic = args[0]
                del(args[0])
                return(topic)
            else:
                self.para_missing(name)
                sys.exit(1)

        # Check topic
        elif name == "acl-definition":
            if len(args):
                defs = args[0].split(",")

                # Parse each definition
                actions = []
                for defintion in defs:
                    entries = defintion.split(":")
                    if len(entries) < 2:
                        self.para_missing(name)
                        sys.exit(1)
                    else:
                        action = {}
                        action['topic'] = entries[0]
                        action['acl'] = entries[1]
                        action['options'] = {}
                        for opt in entries[2::]:
                            opt_entries = opt.split("=")
                            if len(opt_entries) != 2:
                                self.para_missing(name)
                                sys.exit(1)
                            else:
                                oname, ovalue = opt_entries
                                action['options'][oname] = ovalue
                        actions.append(action)
                del(args[0])
                return(actions)
            else:
                self.para_missing(name)
                sys.exit(1)

        # Check members
        elif name == "members":
            if len(args):
                members = args[0]
                del(args[0])

                # Validate the found member valus
                members = members.split(",")
                m_list = []
                for member in members:
                    member = member.strip()
                    #if not re.match("^[a-zA-Z][a-zA-Z0-9\.-]*$", member):
                    #    self.para_invalid(name)
                    #    sys.exit(1)
                    m_list.append(member)
                return(m_list)
            else:
                self.para_missing(name)
                sys.exit(1)

        # Check acls
        elif name == "acls":
            if len(args):
                acls = args[0]
                del(args[0])
                return(acls)
            else:
                self.para_missing(name)
                sys.exit(1)

        # Check rolename
        elif name == "rolename":
            if len(args):
                rolename = args[0]
                del(args[0])
                return(rolename)
            else:
                self.para_missing(name)
                sys.exit(1)

        # Check for options
        elif name == "options":
            if len(args):
                options = args[0]
                if not re.match(r"^([a-z0-9]*:[^:;]*;)*$", options):
                    self.para_invalid('options')
                    sys.exit(1)

                opts = {}
                for item in options.split(";"):
                    if len(item):
                        tmp = item.split(":")
                        opts[tmp[0]] = tmp[1]

                del(args[0])
                return(opts)
            return({})

        # Check for acl-update-actions
        elif name == "acl-update-action":
            if len(args):
                action = args[0]
                if action not in ["set-scope", "set-members", "set-priority", "set-action", "set-role"]:
                    self.para_invalid(name)
                    sys.exit(1)

                del(args[0])
                return(action)
            else:
                self.para_missing(name)
                sys.exit(1)

        # Check for roleacl-update-actions
        elif name == "roleacl-update-action":
            if len(args):
                action = args[0]
                if action not in ["set-scope", "set-priority", "set-action", "set-role"]:
                    self.para_invalid(name)
                    sys.exit(1)

                del(args[0])
                return(action)
            else:
                self.para_missing(name)
                sys.exit(1)

        # Check for acl-add-actions
        elif name == "acl-add-action":
            if len(args):
                action = args[0]
                if action not in ["with-actions", "with-role"]:
                    self.para_invalid(name)
                    sys.exit(1)

                del(args[0])
                return(action)
            else:
                self.para_missing(name)
                sys.exit(1)

        else:
            raise(Exception("Unknown parameter to extract: %s" % (name,)))

    @helpDecorator(_("Adds a new acl entry to an object"), _("add acl [with-role|with-actions] <base> <priority> <members> [rolename|<scope> <topic> <acls> [options]]"))
    def add_acl(self, args):
        """
        This method creates adds a new ACL to an object
        """
        
        # Extract information from script-arguments
        action_type = self.get_value_from_args("acl-add-action", args)
        actions = rolename = scope = members = None
        base = self.get_value_from_args("base", args)

        # Try to open the target object
        #try:
        obj = self.proxy.openObject("object", base)
        #except:
        #    print("invalid base given, failed to open object!")
        #    return
            
        priority = self.get_value_from_args("priority", args)
        members = self.get_value_from_args("members", args)

        # Do we create an acl with direct actions or do we use a role.
        if action_type == "with-actions":
            scope = self.get_value_from_args("scope", args)
            actions = self.get_value_from_args("acl-definition", args)
            acl_entry = {"priority": priority, 
                        "members": members, 
                        "actions": actions, 
                        "scope": scope}

        else:
            rolename = self.get_value_from_args("rolename", args)
            acl_entry = {"priority": priority, 
                        "members": members, 
                        "rolename": rolename}

        # Check if we've to add the Acl-extension
        ext_types = obj.get_extension_types()
        if not "Acl" in ext_types:
            print("the given object does not support Acls")
            return
       
        # Add Acl-extension on demand
        if not ext_types["Acl"]:
            obj.extend("Acl")
            obj.AclSets = []

        # Update the object with the given acls
        asets = obj.AclSets
        asets.append(acl_entry)
        obj.AclSets = asets
        obj.commit()

    @helpDecorator(_("Adds a new acl entry to an existing role"), _("add roleacl [with-role|with-actions] <dn> <priority> [rolename|<scope> <topic> <acls> [options]]"))
    def add_roleacl(self, args):
        """
        Adds a new acl entry to an existing role
        """

        # Extract information from script-arguments
        action_type = self.get_value_from_args("acl-add-action", args)
        actions = rolename = scope = members = None
        obj_dn = self.get_value_from_args("dn", args)

        # Try to open the target object
        #try:
        obj = self.proxy.openObject("object", obj_dn)
        #except:
        #    print("invalid dn given, failed to open object!")
        #    return

        priority = self.get_value_from_args("priority", args)

        # Do we create an acl with direct actions or do we use a role.
        aclentry = {"priority": priority}
        if action_type == "with-actions":
            scope = self.get_value_from_args("scope", args)
            actions = self.get_value_from_args("acl-definition", args)
            aclentry["scope"] = scope
            aclentry["actions"] = actions
        else:
            use_role = self.get_value_from_args("rolename", args)
            aclentry["rolename"] = use_role

        # Update the object with the given acls
        try:
            roles = obj.AclRoles
            roles.append(aclentry)
            obj.AclRoles = roles
            obj.commit()
        except:
            print("The given DN seems not to be an acl-role!")


    @helpDecorator(_("Adds a new role"), _("add role <base> <rolename>"))
    def add_role(self, args):
        """
        This method creates a new role

        (It can be accessed via parameter 'add role')

        =========== =============
        key         description
        =========== =============
        args        The arguments-list we use as information basis
        =========== =============
        """

        base = self.get_value_from_args("base", args)
        rolename = self.get_value_from_args("rolename", args)
        #try:
        obj = self.proxy.openObject("object", base, "AclRole")
        #except:
        #    print("invalid dn given, failed to open object!")
        #    return

        obj.name = rolename
        obj.commit()

    @helpDecorator(_("Removes all acl entries from a role"), _("remove roleacl <DN>"))
    def remove_roleacls(self, args):
        """
        This method removes all defined acls from a role 
        """

        obj_dn = self.get_value_from_args("dn", args)
        #try:
        obj = self.proxy.openObject("object", obj_dn)
        #except:
        #    print("invalid dn given, failed to open object!")

        obj.AclRoles = []
        obj.commit()

    @helpDecorator(_("Removes all acl entries for a given base"), _("remove roleacl <BASE>"))
    def remove_acls(self, args):
        """
        Removes all acl entries for a given base

        =========== =============
        key         description
        =========== =============
        args        The arguments-list we use as information basis
        =========== =============
        """

        obj_dn = self.get_value_from_args("base", args)
        #try:
        obj = self.proxy.openObject("object", obj_dn)
        #except:
        #    print("invalid dn given, failed to open object!")
        #    return

        # Check if we've to add the Acl-extension
        ext_types = obj.get_extension_types()
        if not "Acl" in ext_types:
            print("the given object does not support Acls")
            return
       
        # Add Acl-extension on demand
        if not ext_types["Acl"]:
            print("the acl-extension is not activated for the given object!")
            return

        # Retract the acl extension
        obj.retract("Acl")
        obj.commit()


    @helpDecorator(_("Removes a role"), _("remove role <DN>"))
    def remove_role(self, args):
        """
        This method removes a role

        =========== =============
        key         description
        =========== =============
        args        The arguments-list we use as information basis
        =========== =============
        """
        obj_dn = self.get_value_from_args("dn", args)
        #try:
        obj = self.proxy.openObject("object", obj_dn)
        #except:
        #    print("invalid dn given, failed to open object!")
        #    return

        obj.remove()

    @helpDecorator(_("List all defined acls"))
    def list(self, args):
        """
        This method lists all defined acls.

        (It can be accessed via parameter 'list')

        =========== =============
        key         description
        =========== =============
        args        The arguments-list we use as information basis
        =========== =============
        """

        self.printReportHeader(_("Listing of active GOsa acls"))
        allSets = self.proxy.getACLs()
        if not len(allSets):
            print("   ... none")

        for base in allSets:
            print("BASE: \t\t%s" % (base))

            for acl in allSets[base]:
                print(" - ID: \t\t%s" % acl["id"])
                if "rolename" in acl:
                    print(" - MEMBERS: \t%s" % ", ".join(acl["members"]))
                    print(" - ROLE: \t%s" % acl["rolename"])
                else:
                    print(" - SCOPE: \t%s" % acl["scope"])
                    print(" - MEMBERS: \t%s" % ", ".join(acl["members"]))
                    print(" - PRIORITY: \t%s" % acl["priority"])
                    first = True
                    for action in acl['actions']:
                        if first:
                            print(" - ACTIONS:\t%s (%s)  %s" % (action['topic'], action['acls'], action['options']))
                            first = False
                        else:
                            print(" -      \t%s (%s)  %s" % (action['topic'], action['acls'], action['options']))
                print("---")
            print()

        self.printReportHeader(_("Listing of active GOsa roles"))
        allRoles = self.proxy.getACLRoles()
        if not len(allRoles):
            print("   ... none")
        for aclset in allRoles:
            print("ROLENAME: \t%s" % (aclset['name']))
            print("DN: \t\t%s" % (aclset['dn']))
            for acl in aclset['acls']:
                print(" - ID: \t\t%s" % acl["id"])
                if "rolename" in acl:
                    print(" - ROLE: \t%s" % acl["rolename"])
                else:
                    print(" - SCOPE: \t%s" % acl["scope"])
                    print(" - PRIORITY: \t%s" % acl["priority"])
                    first = True
                    for action in acl['actions']:
                        if first:
                            print(" - ACTIONS:\t%s (%s)  %s" % (action['topic'], action['acls'], action['options']))
                            first = False
                        else:
                            print(" -      \t%s (%s)  %s" % (action['topic'], action['acls'], action['options']))
                print("---")
            print()


def print_help():  # pragma: nocover
    """
    This method prints out the command-line help for this script.
    """

    # Define cli-script parameters
    print(_(
        "\nAdministrate GOsa permissions from the command line."
        "\n"
        "\n ./acl-admin [-u/--user username] [-p/--password passwort] [-s/--url service-url] <action>"
        "\n"
        "\nActions:"))

    # Add methods marked with the helpDecorator
    mlist = sorted(helpDecorator.method_list)
    for method in mlist:
        short = helpDecorator.method_list[method][0]
        long_header = helpDecorator.method_list[method][1]
        method = re.sub("_", " ", method)
        if long_header != "":
            print("  %s %s\n    %s\n" % (method.ljust(20), short, long_header))
        else:
            print("  %s %s" % (method.ljust(20), short))


def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:s", ["user=", "password=", "url="])
    except GetoptError:
        sys.exit(2)

    service_uri = ''
    username = ''
    password = ''

    for opt, arg in opts:
        if opt in ("-u", "--user"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-s", "--url"):
            service_uri = arg

    # Print out help if no args is given.
    if "-h" in sys.argv:
        print_help()
        sys.exit(0)

    # Remove the first element, username and password of my_args, we don't need it.
    my_args = sys.argv[1 + (len(opts) *2)::]

    # If no args were given print the help message and quit
    if len(my_args) == 0:
        print_help()
        sys.exit(1)

    # Check if there is a method which is using the decorator 'helpDecorator' and
    # is matching the given parameters
    method = ""
    called = False
    args_left = copy.deepcopy(my_args)
    while(len(args_left)):
        method += "_" + args_left[0]
        del(args_left[0])

        method = re.sub(r"^_", "", method)
        if method in helpDecorator.method_list:
            con = connect(service_uri, username, password)
            admin = ACLAdmin(con)
            getattr(admin, method)(args_left)
            called = True

    if not called:
        print(_("Invalid argument list: %s") % (" ".join(my_args)))
        print_help()
        sys.exit(1)


def connect(service_uri='', username='', password=''):
    """ Creates a service proxy object from the arguments. """

    # Clean arguments
    username = username.strip()
    password = password.strip()
    service_uri = service_uri.strip()

    # Test if one argument is still needed.
    if len(service_uri) <= 0:
        tmp = service_uri
        service_uri = input('Service URI: [%s]' % service_uri).strip()
        if len(service_uri) <= 0:
            service_uri = tmp

    # Chek if URL is parsable
    url = parseURL(service_uri)

    # If we have still no service host, quit, because the connect will fail
    # pylint: disable-msg=E1101
    if not url:
        print(_("Need at least a service URI!"))
        sys.exit(1)

    # TRANSLATOR: Conected to URL, i.e. https://gosa.local:8080/rpc
    print(_("Connected to %s://%s:%s/%s") %
            (url['scheme'], url['host'], url['port'], url['path']))

    # Check weather to use method parameters or the URI elements.
    # If URI username is set and the method username is not set
    if url['user']:
        username = url['user']
    # If URI password is set and the username is set and the method password is not set
    if url['password']:
        password = url['password']

    # If we have still no credentials query for them
    if len(username) <= 0:
        # TRANSLATOR: This is a prompt - Username [joe]:
        username = input(_("Username") + " [%s]: " % getpass.getuser()).strip()
        if len(username) <= 0:
            username = getpass.getuser()

    if len(password) <= 0:
        # TRANSLATOR: This is a prompt - Password:
        password = getpass.getpass(_("Password") + ': ')

    # Create service proxy
    if url['scheme'][0:4] == "http":
        connection = '%s://%s:%s/%s' % (
                url['scheme'],
                url['host'],
                url['port'],
                url['path'])

        proxy = JSONServiceProxy(connection)
    else:
        print(_("The selected protocol is not supported!"))
        sys.exit(1)

    # Try to log in
    try:
        if not proxy.login(username, password):
            print(_("Login of user '%s' failed") % username)
            sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)

    return proxy


if __name__ == '__main__':
    main()
