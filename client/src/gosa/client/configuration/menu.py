# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from colorlog import logging
from zope.interface import implementer

from gosa.common import Environment
from gosa.common.components import Plugin, PluginRegistry, Command
from gosa.common.handler import IInterfaceHandler
import shutil
import xdg.DesktopEntry
import xdg.Menu
from bs4 import BeautifulSoup

from xml.dom.minidom import getDOMImplementation
import os
import pprint
pp = pprint.PrettyPrinter()

XDG_CONFIG_DIR = "/etc/xdg/xdg-gnome"
XDG_MENU_PREFIX = "gnome-"
GLOBAL_MENU = XDG_CONFIG_DIR + '/menus/' + XDG_MENU_PREFIX + 'applications.menu'


@implementer(IInterfaceHandler)
class MenuConfiguration(Plugin):
    _priority_ = 99
    _target_ = 'session'
    add_other_menu = False
    home_dir = None
    local_menu = os.path.join(".config", "menus", XDG_MENU_PREFIX + 'applications.menu')
    local_applications = os.path.join(".local", "share", "applications")
    local_applications_scripts = os.path.join(".local", "share", "goto", "applications-scripts")
    local_icons = os.path.join(".local", "share", "icons")
    local_directories = os.path.join(".local", "share", "desktop-directories")

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    @Command()
    def configureUserMenu(self, user, user_menu):
        """ configure a users application menu """
        print("Member: %s, message: %s" % (user, user_menu))
        self.home_dir = os.path.expanduser('~%s' % user)
        self.init_directories(user_menu)
        self.init_applications(user_menu)
        self.init_menu(user_menu)

    def init_applications(self, user_menu):
        app_dir = os.path.join(self.home_dir, self.local_applications)
        scripts_dir = os.path.join(self.home_dir, self.local_applications_scripts)
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)

        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)

        shutil.rmtree(app_dir)
        os.makedirs(app_dir)

        shutil.rmtree(scripts_dir)
        os.makedirs(scripts_dir)

        def get_appname(item):
            result = []

            if 'apps' in item:
                for cn, app_entry in item['apps'].items():
                    result.append(app_entry)

            if 'menus' in item:
                for menu_entry in item['menus']:
                    result.extend(get_appname(item['menus'][menu_entry]))

            return result

        for entry in get_appname(user_menu):
            self.write_app_script(entry)
            self.write_app(entry)

    def init_directories(self, user_menu):
        loc_dir = os.path.join(self.home_dir, self.local_directories)
        icon_dir = os.path.join(self.home_dir, self.local_icons)
        if not os.path.exists(loc_dir):
            os.makedirs(loc_dir)

        if not os.path.exists(icon_dir):
            os.makedirs(icon_dir)

        shutil.rmtree(loc_dir)
        os.makedirs(loc_dir)

        def get_dirname(item, prefix=None):
            result = []

            if 'menus' in item:
                for menu_entry in item['menus']:
                    if 'menus' in item['menus'][menu_entry]:
                        if prefix is None:
                            _prefix = menu_entry + "_"
                        else:
                            _prefix = prefix + menu_entry + "_"
                        result.extend(get_dirname(item['menus'][menu_entry], prefix=_prefix))
                        result.append(menu_entry)
                    else:
                        result.append(prefix + menu_entry if prefix else menu_entry)

            return result

        for entry in get_dirname(user_menu):
            self.write_directory(entry)

    def write_directory(self, name):
        directory_entry = xdg.DesktopEntry.DesktopEntry(filename=os.path.join(self.home_dir, self.local_directories, name + '.directory'))
        directory_entry.set('Name', name)
        directory_entry.set('Icon', 'folder')
        directory_entry.set('Version', '1.0')
        directory_entry.write()

    def write_icon(self, basename, icon):
        result = ""

        icon_path = os.path.join(self.home_dir, self.local_icons, basename + ".png")

        if os.path.exists(icon_path):
            os.unlink(icon_path)

        with open(icon_path, 'wb') as icon_file:
            icon_file.write(icon)
            result = icon_path

        return result

    def write_app(self, app_entry):
        desktop_entry = xdg.DesktopEntry.DesktopEntry(filename=os.sep.join((os.path.join(self.home_dir, self.local_applications), app_entry['cn'] + '.desktop')))
        desktop_entry.set('Name', app_entry['name'])
        desktop_entry.set('Terminal', 'false')
        desktop_entry.set('Encoding', 'UTF-8')
        if 'description' in app_entry:
            desktop_entry.set('GenericName', app_entry['description'])
            desktop_entry.set('Comment', app_entry['description'])
        if 'gosaApplicationExecute' in app_entry:
            desktop_entry.set('Exec', app_entry['gosaApplicationExecute'])
        if 'gosaApplicationIcon' in app_entry:
            desktop_entry.set('Icon', self.write_icon(app_entry['cn'], app_entry['gosaApplicationIcon']))
        else:
            desktop_entry.set('Icon', app_entry['cn'])

        desktop_entry.write()

    def write_app_script(self, app_entry):
        result = ""

        if 'gotoLogonScript' in app_entry:
            script_path = os.path.join(self.home_dir, self.local_applications_scripts, app_entry['cn'])

            if os.path.exists(script_path):
                os.unlink(script_path)

            with open (script_path, 'w') as script_file:
                script_file.write(app_entry['gotoLogonScript'])
            result = script_path

        return result

    def init_menu(self, user_menu):
        menu_dir = os.path.join(self.home_dir, self.local_menu)
        if not os.path.exists(os.path.dirname(menu_dir)):
            os.makedirs(os.path.dirname(menu_dir))

        if os.path.exists(menu_dir):
            os.unlink(menu_dir)

        with open(menu_dir, 'w+') as menu:
            impl = getDOMImplementation()
            dt = impl.createDocumentType('Menu', '-//freedesktop//DTD Menu 1.0//EN', 'http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd')
            menu_document = impl.createDocument(None, "Menu", dt)
            top_element = menu_document.documentElement

            soup = BeautifulSoup(menu_document.toxml(), features='xml')
            soup.Menu.append(soup.new_tag('Name'))
            soup.Menu.Name.string='Applications'
            soup.Menu.append(soup.new_tag('Directory'))
            soup.Menu.Directory.string='Applications.directory'

            soup.Menu.append(soup.new_tag('AppDir'))
            soup.Menu.AppDir.string = os.path.join(self.home_dir, self.local_applications)

            system_apps = soup.new_tag('AppDir')
            system_apps.string='/usr/share/applications'
            soup.Menu.append(system_apps)

            soup.Menu.append(soup.new_tag('DirectoryDir'))
            soup.Menu.DirectoryDir.string = menu_dir

            # Insert Top-Level Apps
            soup.Menu.append(soup.new_tag('Include'))
            if 'apps' in user_menu:
                for cn, app_entry in user_menu['apps'].items():
                    app = soup.new_tag('Filename')
                    app.string=cn + '.desktop'
                    soup.Menu.Include.append(app)

            def get_xml_menu(item, prefix=None):
                result = []

                if 'menus' in item:
                    for menu_entry in item['menus']:
                        menu = soup.new_tag('Menu')
                        menu.append(soup.new_tag('Name'))
                        menu.Name.string=menu_entry
                        menu.append(soup.new_tag('Directory'))
                        directory_string = prefix + menu_entry if prefix else menu_entry
                        menu.Directory.string=directory_string + '.directory'
                        menu.append(soup.new_tag('Include'))
                        for app_entry in item['menus'][menu_entry]['apps']:
                            app = soup.new_tag('Filename')
                            app.string=app_entry['cn'] + '.desktop'
                            menu.Include.append(app)

                        if 'menus' in item['menus'][menu_entry]:
                            if prefix is None:
                                _prefix = menu_entry + "_"
                            else:
                                _prefix = prefix + menu_entry + "_"
                            for submenu_result in get_xml_menu(item['menus'][menu_entry], prefix=_prefix):
                                menu.append(submenu_result)

                        result.append(menu)

                return result

            for menu_entry in get_xml_menu(user_menu):
                soup.Menu.append(menu_entry)

            menu.write(str(soup))
