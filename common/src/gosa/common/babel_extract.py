from json import loads, dumps, decoder

import re

import os
from lxml import etree


def extract_object_xml(fileobj, keywords, comment_tags, options):
    """Extract messages from xml object definitions files.

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """
    found = []
    xml = etree.parse(fileobj)
    namespaces = None
    if "namespaces" in options:
        namespaces = loads(options["namespaces"])
    for path in options["paths"].split(" "):
        for r in xml.xpath(path, namespaces=namespaces):
            if "translate" not in r.attrib or r.attrib["translate"] == "true":
                found.append((r.sourceline, None, r.text, []))
    return found


def extract_template_json(fileobj, keywords, comment_tags, options):
    """Extract messages from json template definitions files.

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """
    found = []
    pattern = re.compile('(tr|trc|trn|trnc|marktr)\((.*)\)')
    line_no = 0
    strings = []
    for line in fileobj:
        match = pattern.search(line.decode('utf-8'))
        if match is not None:
            try:
                method_name = match.group(1)
                # get only string arguments
                args = [x.strip()[1:-1] for x in match.group(2).split(",") if x.strip()[0:1] in ["'", '"', "\""]]
                comments = []
                if method_name in ["trc", "trnc"]:
                    comments.append(args.pop(0))
                text = [args.pop(0)]
                func_name = 'gettext'
                if method_name in ["trn", "trnc"]:
                    # plural form
                    func_name = 'ngettext'
                    text.append(args.pop(0))

                strings.extend(text)
                found.append((line_no, func_name, text, comments))
            except decoder.JSONDecodeError:
                print("Error parsing '%s' in line %s of '%s'" % (match.group(2).replace("'", '"'), line_no, fileobj.name))

        line_no += 1

    if len(strings):
        strings = sorted(strings)
        # write keymap for template
        if os.path.exists(os.path.join(os.path.dirname(fileobj.name), "i18n")):
            i18n_dir = os.path.join(os.path.dirname(fileobj.name), "i18n")
        else:
            i18n_dir = os.path.realpath(os.path.join(os.path.dirname(fileobj.name), "..", "i18n"))
        map_file = os.path.join(i18n_dir, "keymap.json")
        template_name = os.path.basename(fileobj.name).split(".")[0]
        if not os.path.exists(map_file):
            with open(map_file, "w") as f:
                f.write(dumps({template_name: strings}))
        else:
            with open(map_file, "r+") as f:
                data = loads(f.read())
                data[template_name] = strings
                f.seek(0)
                f.write(dumps(data, sort_keys=True))

    return found