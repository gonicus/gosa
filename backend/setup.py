#!/usr/bin/env python3
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import distutils
import sys

import re
from setuptools import setup, find_packages
import os
import glob
import polib

try:
    from babel.messages import frontend as babel
except:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()

data_files = []
for path, dirs, files in os.walk("src/gosa/backend/data"):
    for f in files:
            data_files.append(os.path.join(path[17:], f))

if sys.argv[1] == "import-from-json":
    from gosa.common.gjson import loads
    # import old template translations from json files
    translations = {}
    for translation_file in glob.glob(os.path.join("src", "gosa", "backend", "data", "templates", "i18n", "*", "*.json")):
        lang = os.path.basename(translation_file).split(".")[0]
        if lang == "en":
            continue
        if lang not in translations:
            translations[lang] = {}
        with open(translation_file) as f:
            translations[lang].update(loads(f.read()))

    # write them to the PO-Files

    for lang, strings in translations.items():
        po_file = os.path.join("src", "gosa", "backend", "locale", lang, "LC_MESSAGES", "messages.po")
        if os.path.exists(po_file):
            po = polib.pofile(po_file)
            changed = False
            for key, translation in strings.items():
                if translation is None:
                    continue
                entry = po.find(key)
                if entry is not None and entry.translated() is False:
                    entry.msgstr = translation
                    changed = True

            if changed is True:
                po.save()
    sys.exit(0)

elif sys.argv[1] == "test":
    from gosa.common import Environment
    Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "configs", "test_conf")
    Environment.noargs = True
    env = Environment.getInstance()


class CollectI18nStats(distutils.cmd.Command):

    description = 'collect status information about translations in GOsa'

    user_options = [
        # The format is (long option, short option, description).
        ('detailed', None, 'print file statistics'),
    ]

    def initialize_options(self):
        """Set default values for options."""
        self.detailed = False

    def finalize_options(self):
        """Post-process options."""
        self.detailed = bool(self.detailed)

    def __process_file(self, po_file):
        po = polib.pofile(po_file)
        language = None
        if 'Language' in po.metadata:
            language = po.metadata['Language']
        elif 'X-Language' in po.metadata:
            language = po.metadata['X-Language'].split("_")[0]
        else:
            # fallback get from file name
            file_name = os.path.basename(po_file).split(".")[0]
            if len(file_name) == 2:
                language = file_name
            else:
                match = re.match(".*\/locale\/([a-z]{2})\/.*". po_file)
                if match is not None:
                    language = match.group(1)
        valid_entries = [e for e in po if not e.obsolete]

        return {
            "language": language,
            "file": po_file,
            "strings": len(valid_entries),
            "translated_percent": po.percent_translated(),
            "translated": len(po.translated_entries()),
            "untranslated": len(po.untranslated_entries()),
            "obsolete": len(po.obsolete_entries()),
            "fuzzy": len(po.fuzzy_entries()),
        }

    def __update_stats(self, file_entry, stats):
        language = file_entry["language"]
        if language not in stats:
            stats[language] = {
                "strings": 0,
                "translated": 0,
                "untranslated": 0,
                "obsolete": 0,
                "fuzzy": 0,
                "files": []
            }
        stats[language]["strings"] += file_entry["strings"]
        stats[language]["translated"] += file_entry["translated"]
        stats[language]["untranslated"] += file_entry["untranslated"]
        stats[language]["obsolete"] += file_entry["obsolete"]
        stats[language]["fuzzy"] += file_entry["fuzzy"]
        stats[language]["files"].append(file_entry)
        return stats

    def __print_language_stats(self, lang, entry):
        print("{:#<120}".format(""))
        print("Language: {}\t{:>3}% translated ({}/{})".format(
            lang,
            round(100/entry["strings"] * entry["translated"]),
            entry["translated"],
            entry["strings"])
        )
        if lang != "en" and self.detailed is True:
            print("{:-<120}".format(""))
            for file_entry in sorted(entry["files"], key=lambda k: k['file']):
                print("    {file:<90}{translated_percent:>3}% ({translated}/{strings})".format(**file_entry))
        print("{:#<120}\n".format(""))

    def run(self):
        """Run command."""
        print("collecting po files...")
        stats = {}
        for po_file in glob.glob('../**/gosa/**/*.po', recursive=True):
            if "packaging" in po_file:
                 continue
            self.__update_stats(self.__process_file(po_file), stats)

        # self.__print_language_stats("en", stats["en"])
        for lang, entry in sorted(stats.items()):
            if lang != "en":
                self.__print_language_stats(lang, entry)


setup(
    name = "gosa.backend",
    version = "3.0",
    author = "GONICUS GmbH",
    author_email = "info@gonicus.de",
    description = "Identity-, system- and configmanagement middleware",
    long_description = README + "\n\n" + CHANGES,
    keywords = "system config management ldap groupware",
    license = "GPL",
    url = "http://gosa-project.org",
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Monitoring',
    ],
    cmdclass={
        'i18nstats': CollectI18nStats,
    },

    packages = find_packages('src', exclude=['examples', 'tests']),
    package_dir={'': 'src'},
    namespace_packages = ['gosa'],

    include_package_data = True,
    package_data = {
        'gosa.backend': data_files
    },

    zip_safe = False,

    setup_requires = [
        'pytest-runner',
        'pylint',
        ],
    tests_require = [
        'coverage',
        'pytest-cov',
        'coveralls',
        'requests_toolbelt',
        'pytest',
        'line_profiler'
    ],
    install_requires = [
        'tornado',
        'babel>=2.4',
        'zope.interface>=3.5',
        'zope.event',
        'unidecode',
        'pyldap',
        'Pillow',
        'passlib',
        'cryptography',
        'psycopg2',
        'passlib',
        'paho-mqtt',
        'pyotp',
        'pyqrcode',
        'python-u2flib-server>=5.0.0',
        'pycountry',
        'tornadostreamform',
        'pycups',
        'sh',
        'pylint',
        'sqlalchemy_searchable',
        'bcrypt',
        'polib'
        ],

    entry_points = """
        [babel.extractors]
        extract_object_xml = gosa.common.babel_extract:extract_object_xml
        
        [console_scripts]
        gosa = gosa.backend.main:main

        [gosa.route]
        /events = gosa.backend.routes.sse.main:SseHandler
        /rpc = gosa.backend.components.jsonrpc_service:JsonRpcHandler
        /mqtt/auth/(?P<path>.*)? = gosa.backend.plugins.mqtt.mosquitto_auth:MosquittoAuthHandler
        /mqtt/acl = gosa.backend.plugins.mqtt.mosquitto_auth:MosquittoAclHandler
        /mqtt/superuser = gosa.backend.plugins.mqtt.mosquitto_auth:MosquittoSuperuserHandler
        /state = gosa.backend.routes.system:SystemStateReporter
        
        [gosa.backend.route]
        /images/(?P<path>.*)? = gosa.backend.routes.static.main:ImageHandler
        /static/(?P<path>.*)? = gosa.backend.routes.static.main:StaticHandler
        /uploads/(?P<uuid>.*)? = gosa.backend.plugins.upload.main:UploadHandler
        /workflow/(?P<path>.*)? = gosa.backend.routes.static.main:WorkflowHandler
        /hooks(?P<path>.*)? = gosa.backend.plugins.webhook.registry:WebhookReceiver
        /ppd/modified/(?P<path>.*)? = gosa.backend.plugins.cups.route:PPDHandler

        [gosa.plugin]
        scheduler = gosa.backend.components.scheduler:SchedulerService
        acl = gosa.backend.acl:ACLResolver
        objects = gosa.backend.objects.index:ObjectIndex
        httpd = gosa.backend.components.httpd:HTTPService
        command = gosa.backend.command:CommandRegistry
        rpc = gosa.backend.plugins.rpc.methods:RPCMethods
        mqttbackends = gosa.backend.objects.index:BackendRegistry
        two_factor = gosa.backend.plugins.two_factor.main:TwoFactorAuthManager
        foreman = gosa.backend.plugins.foreman.main:Foreman
        locales = gosa.backend.plugins.misc.locales:Locales
        password = gosa.backend.plugins.password.manager:PasswordManager
        sambaguimethods = gosa.backend.plugins.samba.domain:SambaGuiMethods
        gravatar = gosa.backend.plugins.misc.gravatar:Gravatar
        cups = gosa.backend.plugins.cups.main:CupsClient
        transliterate = gosa.backend.plugins.misc.transliterate:Transliterate
        zarafa = gosa.backend.plugins.zarafa.methods:ZarafaRPCMethods
        settings = gosa.backend.components.settings_registry:SettingsRegistry
        mail = gosa.backend.plugins.mail.main:Mail
        user = gosa.backend.plugins.user.main:User
        mqtt_connection = gosa.common.mqtt_connection_state:MQTTConnectionHandler
        
        [gosa.backend.plugin]
        workflow = gosa.backend.components.workflowregistry:WorkflowRegistry
        shells = gosa.backend.plugins.posix.shells:ShellSupport
        webhook_registry = gosa.backend.plugins.webhook.registry:WebhookRegistry
        uploads = gosa.backend.plugins.upload.main:UploadManager
        jsonrpc_om = gosa.backend.components.jsonrpc_objects:JSONRPCObjectMapper
        mqttrpc_service = gosa.backend.components.mqttrpc_service:MQTTRPCService
        ppd_proxy = gosa.backend.plugins.cups.ppd_proxy:PPDProxy

        [gosa.object.backend]
        ldap = gosa.backend.objects.backend.back_ldap:LDAP
        object_handler = gosa.backend.objects.backend.back_object:ObjectHandler
        null = gosa.backend.objects.backend.back_null:NULL
        json = gosa.backend.objects.backend.back_json:JSON
        foreman = gosa.backend.objects.backend.back_foreman:Foreman

        [gosa.object.type]
        string = gosa.backend.objects.types.base:StringAttribute
        anytype = gosa.backend.objects.types.base:AnyType
        integer = gosa.backend.objects.types.base:IntegerAttribute
        boolean = gosa.backend.objects.types.base:BooleanAttribute
        binary = gosa.backend.objects.types.base:BinaryAttribute
        unicodestring = gosa.backend.objects.types.base:UnicodeStringAttribute
        date = gosa.backend.objects.types.base:DateAttribute
        timestamp = gosa.backend.objects.types.base:TimestampAttribute
        sambalogonhours = gosa.backend.plugins.samba.logonhours:SambaLogonHoursAttribute
        aclrole = gosa.backend.objects.types.acl_roles:AclRole
        aclset = gosa.backend.objects.types.acl_set:AclSet

        [gosa.object.filter]
        concatstring = gosa.backend.objects.filter.strings:ConcatString
        joinarray = gosa.backend.objects.filter.strings:JoinArray
        splitstring = gosa.backend.objects.filter.strings:SplitString
        replace = gosa.backend.objects.filter.strings:Replace
        stringToTime = gosa.backend.objects.filter.strings:StringToTime
        stringToDate = gosa.backend.objects.filter.strings:StringToDate
        dateToString = gosa.backend.objects.filter.strings:DateToString
        timeToString = gosa.backend.objects.filter.strings:TimeToString
        integerToString = gosa.backend.objects.filter.strings:IntegerToString
        stringToInteger = gosa.backend.objects.filter.strings:StringToInteger
        idnain = gosa.backend.objects.filter.strings:IdnaToUnicode
        idnaout = gosa.backend.objects.filter.strings:UnicodeToIdna
        rename = gosa.backend.objects.filter.basic:Rename
        copyValueTo = gosa.backend.objects.filter.basic:CopyValueTo
        copyValueFrom = gosa.backend.objects.filter.basic:CopyValueFrom
        copyForeignValueTo = gosa.backend.objects.filter.basic:CopyForeignValueTo
        copyForeignValueFrom = gosa.backend.objects.filter.basic:CopyForeignValueFrom
        setbackends = gosa.backend.objects.filter.basic:SetBackends
        setvalue = gosa.backend.objects.filter.basic:SetValue
        clear = gosa.backend.objects.filter.basic:Clear
        integertobool = gosa.backend.objects.filter.basic:IntegerToBoolean
        booltointeger = gosa.backend.objects.filter.basic:BooleanToInteger
        integertodatetime = gosa.backend.objects.filter.basic:IntegerToDatetime
        datetimetointeger = gosa.backend.objects.filter.basic:DatetimeToInteger
        stringtodatetime = gosa.backend.objects.filter.basic:StringToDatetime
        datetimetostring = gosa.backend.objects.filter.basic:DatetimeToString
        sambahash = gosa.backend.plugins.samba.hash:SambaHash
        adddollar = gosa.backend.plugins.samba.dollar:SambaDollarFilterIn
        deldollar = gosa.backend.plugins.samba.dollar:SambaDollarFilterOut
        sambaacctflagsin = gosa.backend.plugins.samba.flags:SambaAcctFlagsIn
        sambaacctflagsout = gosa.backend.plugins.samba.flags:SambaAcctFlagsOut
        sambamungedialin = gosa.backend.plugins.samba.munged:SambaMungedDialIn
        sambamungedialout = gosa.backend.plugins.samba.munged:SambaMungedDialOut
        mailmodein = gosa.backend.plugins.mail.mode:MailDeliveryModeIn
        mailmodeout = gosa.backend.plugins.mail.mode:MailDeliveryModeOut
        zarafafeaturesin = gosa.backend.plugins.zarafa.main:ZarafaEnabledFeaturesIn
        zarafafeaturesout = gosa.backend.plugins.zarafa.main:ZarafaEnabledFeaturesOut
        zarafafeaturesdis = gosa.backend.plugins.zarafa.main:ZarafaDisabledFeaturesOut
        detectsambadomainnamefromsid = gosa.backend.plugins.samba.sid:DetectSambaDomainFromSID
        generatesambasid = gosa.backend.plugins.samba.sid:GenerateSambaSid
        posixgetnextid = gosa.backend.plugins.posix.filters:GetNextID
        generategecos = gosa.backend.plugins.posix.filters:GenerateGecos
        loadgecosstate = gosa.backend.plugins.posix.filters:LoadGecosState
        imagefilter = gosa.backend.plugins.user.filters:ImageProcessor
        generatedn = gosa.backend.plugins.user.filters:GenerateDisplayName
        loaddnstate = gosa.backend.plugins.user.filters:LoadDisplayNameState
        IsMemberOfAclRole = gosa.backend.plugins.user.filters:IsMemberOfAclRole
        UpdateMemberOfAclRole = gosa.backend.plugins.user.filters:UpdateMemberOfAclRole
        generateids = gosa.backend.plugins.posix.filters:GenerateIDs
        datetoshadowdays = gosa.backend.plugins.posix.shadow:DatetimeToShadowDays
        shadowdaystodate = gosa.backend.plugins.posix.shadow:ShadowDaysToDatetime
        detect_pwd_method = gosa.backend.plugins.password.filter.detect_method:DetectPasswordMethod
        password_lock = gosa.backend.plugins.password.filter.detect_locking:DetectAccountLockStatus
        addbackend = gosa.backend.objects.filter.basic:AddBackend
        securecontext = gosa.backend.plugins.two_factor.filter.detect_security:DetectSecureContext
        stringtojson = gosa.backend.objects.filter.strings:StringToJson
        jsontostring = gosa.backend.objects.filter.strings:JsonToString
        foremanstatusin = gosa.backend.plugins.foreman.filter:ForemanStatusIn
        foremanstatusout = gosa.backend.plugins.foreman.filter:ForemanStatusOut
        GetMakeModelFromPPD = gosa.backend.plugins.cups.filter:GetMakeModelFromPPD
        DeleteOldFile = gosa.backend.plugins.cups.filter:DeleteOldFile
        GetPPDUrl = gosa.backend.plugins.cups.filter:GetPPDUrl
        MarshalLogonScript = gosa.backend.plugins.user.filters:MarshalLogonScript
        UnmarshalLogonScript = gosa.backend.plugins.user.filters:UnmarshalLogonScript
        MarshalFlags = gosa.backend.objects.filter.flags:MarshalFlags
        UnmarshalFlags = gosa.backend.objects.filter.flags:UnmarshalFlags
        FilterOwnDn = gosa.backend.objects.filter.basic:FilterOwnDn
        AddOwnDnIfEmpty = gosa.backend.objects.filter.basic:AddOwnDnIfEmpty

        [gosa.object.comparator]
        like = gosa.backend.objects.comparator.strings:Like
        regex = gosa.backend.objects.comparator.strings:RegEx
        validurl = gosa.backend.objects.comparator.strings:IsValidURL
        stringlength = gosa.backend.objects.comparator.strings:stringLength
        equals = gosa.backend.objects.comparator.basic:Equals
        greater = gosa.backend.objects.comparator.basic:Greater
        smaller = gosa.backend.objects.comparator.basic:Smaller
#        isvalidzmailsrv = gosa.backend.plugins.zarafa.main:IsValidZarafaMailServer
#        isvalidzarchivesrv = gosa.backend.plugins.zarafa.main:IsValidZarafaArchiveServer
        isvalidmailaddress = gosa.backend.plugins.mail.filter_validators:IsValidMailAddress
        isvalidhostname = gosa.backend.plugins.misc.filter_validators:IsValidHostName
        isexistingdn = gosa.backend.plugins.misc.filter_validators:IsExistingDN
        objectwithpropertyexists = gosa.backend.plugins.misc.filter_validators:ObjectWithPropertyExists
        isexistingdnoftype = gosa.backend.plugins.misc.filter_validators:IsExistingDnOfType
        is_acl_role = gosa.backend.objects.comparator.acl_roles:IsAclRole
        is_acl_set = gosa.backend.objects.comparator.acl_set:IsAclSet
        isvalidsambadomainname = gosa.backend.plugins.samba.domain:IsValidSambaDomainName
        checksambasidlist = gosa.backend.plugins.samba.sid:CheckSambaSIDList
        scriptlint = gosa.backend.plugins.lint.main:ScriptLint
        pylint = gosa.backend.plugins.lint.main:PyLint
        shelllint = gosa.backend.plugins.lint.main:ShellLint
        MaxAllowedTypes = gosa.backend.plugins.misc.filter_validators:MaxAllowedTypes
        HasMemberOfType = gosa.backend.plugins.misc.filter_validators:HasMemberOfType
        CheckExtensionConditions = gosa.backend.plugins.misc.filter_validators:CheckExtensionConditions
        IsValidJson = gosa.backend.objects.comparator.strings:IsValidJson

        [gosa.object.operator]
        and = gosa.backend.objects.operator.bool:And
        or = gosa.backend.objects.operator.bool:Or
        not = gosa.backend.objects.operator.bool:Not

        [gosa.object.renderer]
        extensions = gosa.backend.objects.renderer.extensions:ExtensionRenderer
        user_photo = gosa.backend.objects.renderer.photo:UserPhotoRenderer
        host_state = gosa.backend.objects.renderer.hoststate:HostStateRenderer

        [gosa.object]
        object = gosa.backend.objects.proxy:ObjectProxy
        workflow = gosa.backend.components.workflow:Workflow

        [gosa.upload_handler]
        workflow = gosa.backend.plugins.upload.handler.workflow:WorkflowUploadHandler

        [gosa.webhook_handler]
        application/vnd.gosa.event+xml = gosa.backend.plugins.webhook.registry:WebhookEventReceiver
        application/vnd.foreman.hostevent+json = gosa.backend.plugins.foreman.main:ForemanRealmReceiver
        application/vnd.foreman.hookevent+json = gosa.backend.plugins.foreman.main:ForemanHookReceiver

        [gosa.settings_handler]
        gosa.settings = gosa.backend.components.settings_registry:SettingsHandler
        gosa.webhooks = gosa.backend.plugins.webhook.registry:WebhookSettingsHandler

        [password.methods]
        crypt_method = gosa.backend.plugins.password.crypt_password:PasswordMethodCrypt
        
        [gosa.json.datahandler]
        backend_types = gosa.backend.utils:BackendTypesEncoder
    """,
)
return_code = 0

if return_code > 0:
    # exit with error code
    sys.exit(return_code >> 8)