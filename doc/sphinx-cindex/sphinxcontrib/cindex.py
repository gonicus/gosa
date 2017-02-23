# -*- coding: utf-8 -*-
import os
from docutils.parsers.rst import roles, directives
from docutils import nodes, utils
from sphinx.environment import NoUri
from sphinx.locale import _
from sphinx.util.compat import Directive, make_admonition
from sphinx.util.osutil import copyfile

CSS_FILE = 'cindex.css'


class cmd_node(nodes.Admonition, nodes.Element): pass
class cmdlist(nodes.General, nodes.Element): pass

class program_output(nodes.Element): pass


class CmdlistDirective(Directive):

    has_content = True
    required_arguments = 1

    def run(self):
        node = cmdlist('')
        node.section = self.arguments[0]
        return [node]

class CmdDirective(Directive):

    # this enables content in the directive
    has_content = True
    required_arguments = 2

    option_spec = {
        'parameter': str
    }

    title_str = ""

    def run(self):
        env = self.state.document.settings.env

        # Create a target node to be able to jump to it later.
        targetid = "cmd-%d" % env.new_serialno('cmd')
        targetnode = nodes.target('', '', ids=[targetid])

        # Return target node and the node itself.
        node = cmd_node('')

        node.section_str = self.arguments[0]
        node.title_str = self.arguments[1]
        node.desc_str = "".join(self.content[0::])

        ret = [targetnode] + [node]
        return ret


def process_cmds(app, doctree):

    # collect all cmds in the environment
    env = app.builder.env
    if not hasattr(env, 'cmds_all_cmds'):
        env.cmds_all_cmds = []

    for node in doctree.traverse(cmd_node):
        try:
            targetnode = node.parent[node.parent.index(node) - 1]
            if not isinstance(targetnode, nodes.target):
                raise IndexError
        except IndexError:
            targetnode = None

        env.cmds_all_cmds.append({
            'docname': env.docname,
            'lineno': node.line,
            'cmd': node.deepcopy(),
            'section': node.section_str,
            'title': node.title_str,
            'desc': node.desc_str,
            'target': targetnode,
        })

def process_cmd_nodes(app, doctree, fromdocname):
    # Replace all cmdlist nodes with a list of the collected cmds.
    # Augment each cmd with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, 'cmds_all_cmds'):
        env.cmds_all_cmds = []

    # Sort list of commands
    l = sorted(env.cmds_all_cmds, key=lambda cmd: cmd['title'])

    # Iterate through all found cmdlist directives.
    for node in doctree.traverse(cmdlist):
        content = []
        tbody = nodes.tbody('');

        # Get the current cmdlist-section for the node.
        section = node.section

        cmds_found = 0
        for cmd_info in l:

            # Skip entries that do not match our section
            if cmd_info['section'] != section:
                continue

            cmds_found = cmds_found + 1

            # (Recursively) resolve references in the cmd content
            cmd_entry = cmd_info['cmd']
            env.resolve_references(cmd_entry, cmd_info['docname'],
                                   app.builder)

            # create the reference link to the target position
            para = nodes.paragraph()
            refnode = nodes.reference('', cmd_info['title'], internal=True)
            para += refnode
            try:
                refnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, cmd_info['docname'])
                refnode['refuri'] += '#' + cmd_info['target']['refid']
            except NoUri:
                # ignore if no URI can be determined, e.g. for LaTeX output
                pass

            # Add a new row to the table body
            t1 = para
            t2 = nodes.container('',nodes.Text(cmd_info['desc']))
            row = nodes.row('', nodes.entry('',t1),
                                nodes.entry('',t2))
            tbody+=row

        # create the resulting table
        if cmds_found != 0:
            t=nodes.table('',
                nodes.tgroup('',
                    nodes.colspec(colwidth=5,classes=['rst-raw']),
                    nodes.colspec(colwidth=5),
                    nodes.thead('',
                        nodes.row('',
                            nodes.entry('', nodes.paragraph('',_('Method'))),
                            nodes.entry('', nodes.paragraph('',_('Description'))))),
                    tbody));
            content.append(t)
        else:
            content.append(nodes.Text(_('No entries')))

        content.append(nodes.paragraph('','\n '));
        node.replace_self(content)

def purge_cmds(app, env, docname):
    if not hasattr(env, 'cmds_all_cmds'):
        return
    env.cmds_all_cmds = [cmd for cmd in env.cmds_all_cmds
                          if cmd['docname'] != docname]

def visit_cmd_node(self, node):
    self.visit_admonition(node)

def depart_cmd_node(self, node):
    self.depart_admonition(node)

def add_stylesheet(app):
    app.add_stylesheet(CSS_FILE)

def copy_stylesheet(app, exception):
    if app.builder.name != 'html' or exception:
        return
    app.info('Copying commands stylesheet... ', nonl=True)
    dest = os.path.join(app.builder.outdir, '_static', CSS_FILE)
    source = os.path.join(os.path.abspath(os.path.dirname(__file__)), CSS_FILE)
    copyfile(source, dest)
    app.info('done')

def setup(app):
    app.add_node(cmdlist)
    app.add_node(cmd_node,
                 html=(visit_cmd_node, depart_cmd_node),
                 latex=(visit_cmd_node, depart_cmd_node),
                 text=(visit_cmd_node, depart_cmd_node),
                 man=(visit_cmd_node, depart_cmd_node),
                 texinfo=(visit_cmd_node, depart_cmd_node))

    app.add_directive('command', CmdDirective)
    app.add_directive('cmdlist', CmdlistDirective)
    app.connect('doctree-read', process_cmds)
    app.connect('doctree-resolved', process_cmd_nodes)
    app.connect('env-purge-doc', purge_cmds)
    app.connect('builder-inited', add_stylesheet)
    app.connect('build-finished', copy_stylesheet)
