#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import os
import copy
import ldap.schema
import logging
from argparse import ArgumentParser
from lxml import etree
from lxml.builder import ElementMaker
import json


VERSION = "1.0"
TYPE_MAP = {
    "1.3.6.1.4.1.1466.115.121.1.6": dict(
        name="Binary",
        #widget="BinaryEdit",
        condition="RegEx",
        param=[r"^'[01]*'B$"],
        index=False),
    "1.3.6.1.4.1.1466.115.121.1.7": dict(
        widget="QCheckBox",
        name="Boolean"),
    "1.3.6.1.4.1.1466.115.121.1.12": dict(
        #widget="DNChooser",
        name="UnicodeString",
        condition="IsExistingDN"),
    "1.3.6.1.4.1.1466.115.121.1.15": dict(
        name="UnicodeString",
        widget="QLineEdit"),
    "1.3.6.1.4.1.1466.115.121.1.24": dict(
        name="Timestamp",
        widget="QDateTimeEdit"),
    "1.3.6.1.4.1.1466.115.121.1.26": dict(
        name="String",
        condition="RegEx",
        param=[r"^[\x00-\x7F]*$"]),
    "1.3.6.1.4.1.1466.115.121.1.27": dict(
        name="Integer",
        widget="QSpinBox"),
    "1.3.6.1.4.1.1466.115.121.1.44": dict(
        name="UnicodeString",
        widget="QLineEdit",
        condition="RegEx",
        param=[r'^[a-zA-Z0-9"()+,./? -]+$']),
    "1.3.6.1.4.1.1466.115.121.1.53": dict(
        name="Timestamp",
        skip=True,
        widget="QDateTimeEdit"),
    "1.3.6.1.4.1.1466.115.121.1.14": dict(
        name="String",
        widget="QComboBox",
        options=["any", "mhs", "physical", "telex", "teletex", "g3fax",
            "g4fax", "ia5", "videotex", "telephone"]),
    "1.3.6.1.4.1.1466.115.121.1.50": dict(
        name="String",
        widget="QLineEdit",
        condition="RegEx",
        param=[r"^\+[0-9]{2}\s*[0-9\s]+$"]),
    "1.3.6.1.4.1.1466.115.121.1.5": dict(
        name="Binary",
	    #widget="Upload",
        index=False),
    "1.3.6.1.4.1.1466.115.121.1.25": dict(
        name="UnicodeString",
        skip=True,
        index=False),
    "1.3.6.1.4.1.1466.115.121.1.40": dict(
        name="Binary",
        #widget="Upload",
        index=False),
    "1.3.6.1.4.1.1466.115.121.1.36": dict(
        name="String",
        widget="QLineEdit",
        condition="RegEx",
        param=[r"^[0-9 ]+$"]),

    #TODO
    "1.3.6.1.4.1.1466.115.121.1.4": dict(
        name="Binary",
        index=False,
        comment="audio -> http://docs.python.org/library/sunau.html -> define object?"),
    "1.3.6.1.4.1.1466.115.121.1.8": dict(
        name="Binary",
        comment='userCertificate;binary -> define object?',
        index=False),
    "1.3.6.1.4.1.1466.115.121.1.28": dict(
        name="Binary",
        comment="jpeg-photo -> http://docs.python.org/release/2.6/library/jpeg.html -> define object?",
        index=False),
    "1.3.6.1.4.1.1466.115.121.1.23": dict(
        name="Binary",
        comment="fax image -> define object?",
        index=False),
    "1.3.6.1.4.1.1466.115.121.1.41": dict(
        name="UnicodeString",
        comment="Postal Address -> filter for $ seperated elements or object -> TODO"),
    "1.3.6.1.4.1.1466.115.121.1.51": dict(
        name="UnicodeString",
        comment="A printable string optionaly one or more parameters separed by a $ sign -> filter or object -> TODO"),
    "1.3.6.1.4.1.1466.115.121.1.52": dict(
        name="UnicodeString",
        comment="Format actual-number $ country $ answerback -> filter or object -> TODO"),
    "1.3.6.1.4.1.1466.115.121.1.22": dict(
        name="String",
        comment='''TODO: fax-number    = printablestring [ "$" faxparameters ]

      faxparameters = faxparm / ( faxparm "$" faxparameters )

      faxparm = "twoDimensional" / "fineResolution" /
                "unlimitedLength" /
                "b4Length" / "a3Width" / "b4Width" / "uncompressed"'''),
}


log = logging.getLogger("schema2xml")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def CLASS(v):  # pragma: nocover
    return {'class': v}


def list_classes(uri):  # pragma: nocover
    subschemasubentry_dn, schema = ldap.schema.urlfetch(uri)
    schema_reverse = ldap.schema.SubSchema(schema.ldap_entry())

    ocs = ldap.schema.SCHEMA_CLASS_MAPPING['objectclasses']
    for element_id in schema.listall(ocs):
        obj = schema.get_obj(ocs, element_id)
        print("%s - %s" % (obj.names[0], obj.desc or "no description"))


def gen_values(syntax):  # pragma: nocover
    res = []
    if not syntax in TYPE_MAP:
        return res

    attr = TYPE_MAP[syntax]

    if "options" in attr:
        e = ElementMaker(namespace="http://www.gonicus.de/Objects", nsmap={None: "http://www.gonicus.de/Objects"})
        for a in attr['options']:
            res.append(e.Value(a))

        res = [e.Values(*res)]

    return res


def gen_validators(syntax):  # pragma: nocover
    res = []
    if not syntax in TYPE_MAP:
        return res

    attr = TYPE_MAP[syntax]
    e = ElementMaker(namespace="http://www.gonicus.de/Objects", nsmap={None: "http://www.gonicus.de/Objects"})

    condition = attr['condition'] if 'condition' in attr else None
    if condition:
        params = []
        for param in (attr['param'] if 'param' in attr else []):
            params.append(e.Param(param))

        res.append(e.Condition(e.Name(condition), *params))

    if res:
        res = [e.Validators(*res)]

    return res


def gen_index(syntax):  # pragma: nocover
    if not syntax in TYPE_MAP:
        return []

    if 'index' in TYPE_MAP[syntax] and not TYPE_MAP[syntax]['index']:
        e = ElementMaker(namespace="http://www.gonicus.de/Objects", nsmap={None: "http://www.gonicus.de/Objects"})
        return [e.NotIndexed('true')]

    return []


def skip(syntax):  # pragma: nocover
    if not syntax in TYPE_MAP:
        return True

    return 'skip' in TYPE_MAP[syntax] and TYPE_MAP[syntax]['skip']


def dump_ui(uri, oc, outfile=None, extend=None, rdn=None, contains=None):  # pragma: nocover
    subschemasubentry_dn, schema = ldap.schema.urlfetch(uri)
    schema_reverse = ldap.schema.SubSchema(schema.ldap_entry())

    oco = schema.get_obj(ldap.schema.ObjectClass, oc)
    if oco is None:
        log.error("unknown objectclass '%s' - please use the --list option to see what's there" % oc)
        exit(1)

    # Complete attributes in case of inheritance
    if oco.kind == 0:
        r = resolve_inherited_attrs(schema, oco.sup[0])
        oco.must = list(set(list(oco.must) + r['must']))
        oco.may = list(set(list(oco.may) + r['must']))

    # Tabstop and connection collectors
    ts = []
    cs = []

    # Build resulting json dump
    children_must = generate_children(oco.must, schema)
    children_may = generate_children(oco.may, schema, len(children_must) // 2, children_must)

    template = {
        'type': 'widget',
        'class': 'qx.ui.container.Composite',
        'layout': 'qx.ui.layout.Grid',
        'extensions': {
            'tabConfig': {
                'title': oc
            }
        },
        'children': children_must + children_may
    };

    return json.dumps(template, indent=2)

def generate_children(widget_list, schema, row_start = 0, must = None):
    children = []
    z = row_start

    for mua in widget_list:
        if must and mua in must:
            continue

        attr = resolve_attribute(schema, mua)
        syntax = attr['syntax']

        if skip(syntax):
            continue
        if not 'widget' in TYPE_MAP[syntax]:
            continue
        widget_name = TYPE_MAP[syntax]['widget']

        # buddy label
        children.append({
            'class': 'gosa.ui.widgets.QLabelWidget',
            'buddyModelPath': mua,
            'addOptions': {
                'row': z,
                'column': 0
            },
            'properties': {
                'text': mua
            }
        })

        # actual widget
        children.append({
            'class': 'gosa.ui.widgets.' + widget_name + 'Widget',
            'modelPath': mua,
            'addOptions': {
                'row': z,
                'column': 1
            },
            'properties': {
                'tabIndex': z + 1
            }
        })
        z += 1

    return children


def dump_class(uri, oc, outfile=None, extend=None, rdn=None, contains=None):
    subschemasubentry_dn, schema = ldap.schema.urlfetch(uri)
    schema_reverse = ldap.schema.SubSchema(schema.ldap_entry())

    oco = schema.get_obj(ldap.schema.ObjectClass, oc)
    if oco is None:
        log.error("unknown objectclass '%s' - please use the --list option to see what's there" % oc)
        exit(1)

    # Complete attributes in case of inheritance
    if oco.kind == 0:
        r = resolve_inherited_attrs(schema, oco.sup[0])
        oco.must = list(set(list(oco.must) + r['must']))
        oco.may = list(set(list(oco.may) + r['must']))

    # Build resulting XML dump
    e = ElementMaker(namespace="http://www.gonicus.de/Objects", nsmap={None: "http://www.gonicus.de/Objects"})
    more = []
    if oco.desc:
        more.append(e.Description(oco.desc))
    more.append(e.Backend("LDAP"))
    if oco.kind == 0:
        if not rdn:
            log.error("no RDN provided - please use --rdn <value> to specify one")
            exit(1)
        more.append(e.BackendParameters(e.Backend("LDAP", objectClasses=oc, RDN=rdn)))

    if oco.kind != 0:
        more.append(e.BaseObject("false"))
    else:
        more.append(e.BaseObject("true"))

    # Build attribute set
    attrs = []
    for mua in oco.must:
        attr = resolve_attribute(schema, mua)
        syntax = attr['syntax']

        if skip(syntax):
            continue

    values = gen_values(syntax)
    values += gen_validators(syntax)
    values += gen_index(syntax)

    attrs.append(
           e.Attribute(
               e.Name(attr['name']),
               e.Description(attr['desc']),
               e.Type(attr['type']),
               e.MultiValue("true" if attr['multivalue'] else "false"),
               e.Mandatory("true"),
               *values))

    for mua in oco.may:
        attr = resolve_attribute(schema, mua)
        syntax = attr['syntax']
        if skip(syntax):
            continue
    values = gen_values(syntax)
    values += gen_validators(syntax)
    values += gen_index(syntax)
    attrs.append(
           e.Attribute(
               e.Name(attr['name']),
               e.Description(attr['desc']),
               e.Type(attr['type']),
               e.MultiValue("true" if attr['multivalue'] else "false"),
               e.Mandatory("false"),
               *values))

    more.append(e.Attributes(*attrs))

    # Add container
    if contains == None:
        c = []
        for typ in contains.split(","):
            c.append(e.Type(typ))
        more.append(e.Container(*c))

    # Maintain extension
    if extend == None:
        more.append(e.Extends(e.Value(extend)))

    res = '<?xml version="1.0" encoding="UTF-8"?>\n'
    data = e.Objects(e.Object(e.Name(oc), e.DisplayName(oc), *more))
    res += etree.tostring(data, pretty_print=True).decode('utf-8')

    return res


def resolve_type(atype):  # pragma: nocover
    if not atype in TYPE_MAP:
        log.warning("unknown mapping for %s - fallback to UnicodeString" % atype)
        return "UnicodeString"

    return TYPE_MAP[atype]['name']


def resolve_inherited_attrs(schema, oc):  # pragma: nocover
    res = {'must': [], 'may': []}
    if oc == 'top':
        return res

    noc = schema.get_obj(ldap.schema.ObjectClass, oc)
    if noc.kind == 0:
       r = resolve_inherited_attrs(schema, noc.sup[0])
       res['must'] += r['must']
       res['may'] += r['may']

    res['must'] += list(noc.must)
    res['may'] += list(noc.may)

    return res


def _resolve_attribute(schema, attr, blank=None):  # pragma: nocover
    if not blank:
        blank = ldap.schema.AttributeType()
        blank.syntax_len = None

    if attr.sup:
        sup = schema.get_obj(ldap.schema.AttributeType, attr.sup[0])
        if sup.syntax:
            blank.syntax = sup.syntax
        if sup.syntax_len:
            blank.syntax_len = sup.syntax_len
        if sup.equality:
            blank.equality = sup.equality
        if sup.substr:
            blank.substr = sup.substr
        return _resolve_attribute(schema, sup, blank)

    return blank


def resolve_attribute(schema, attr):  # pragma: nocover
    blank = {}
    attr = schema.get_obj(ldap.schema.AttributeType, attr)

    if attr.sup:
       inh = _resolve_attribute(schema, attr)
    else:
       inh = None

    blank['name'] = attr.names[0]
    blank['desc'] = attr.desc or "no description"
    blank['sup'] = inh != None
    blank['type'] = resolve_type(attr.syntax or inh.syntax)
    blank['syntax'] = attr.syntax or inh.syntax
    blank['maxlen'] = attr.syntax_len or (inh and inh.syntax_len) or None
    blank['multivalue'] = not attr.single_value
    blank['writable'] = not attr.no_user_mod
    blank['index'] = True if attr.equality or attr.substr or (inh and (inh.equality or inh.substr)) else False

    return blank


def main():  # pragma: nocover
    parser = ArgumentParser(usage="%(prog)s - GOsa schema conversion tool")
    parser.add_argument("--version", action='version', version=VERSION)

    parser.add_argument("--uri", dest="uri", default="ldapi:///",
                      help="URI of LDAP server which contains the required schema",
                      metavar="URI")
    parser.add_argument("-l", "--list", dest="list", action="store_true",
                      help="show list of available objectclasses")
    parser.add_argument("-o", "--output-file", dest="target",
                      help="write output to FILE",
                      metavar="FILE")
    parser.add_argument("-u", "--ui-output-file", dest="target_ui",
                      help="write output to FILE",
                      metavar="FILE")
    parser.add_argument("--rdn", dest="rdn", default=None,
                      help="RDN to use for primary objects",
                      metavar="RDN")
    parser.add_argument("--extend", dest="extend", default="None",
                      help="object NAME you want to extend",
                      metavar="NAME")
    parser.add_argument("--contains", dest="contains", default="None",
                      help="comma separated list of objects NAME(s) you want to extend",
                      metavar="NAME")

    parser.add_argument('oc', metavar='str', type=str, help='class to be converted', nargs='?')
    options = parser.parse_args()

    if options.list:
        list_classes(options.uri)
        exit(0)

    if not options.oc:
        log.error("please provide an objectclass to be converted")
        exit(1)

    res = dump_class(options.uri, options.oc, options.target, options.extend,
            options.rdn, options.contains)

    if options.target:
        with open(options.target, "w+") as f:
            f.write(res)
    else:
        print(res)

    res = dump_ui(options.uri, options.oc, options.target, options.extend,
            options.rdn, options.contains)
    if options.target_ui:
        with open(options.target_ui, "w+") as f:
            f.write(res)
    else:
        print(res)


if __name__ == "__main__":  # pragma: nocover
    main()
