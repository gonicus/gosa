from json import loads

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
            found.append((r.sourceline, None, r.text, []))
    return found

