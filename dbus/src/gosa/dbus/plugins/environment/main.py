# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _dbus-cups:

GOsa D-Bus Environment Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This plugin allows to configure a user environment (e.g. application menu).

"""
import glob
import logging
import subprocess

import dbus.service
import pwd
import stat

from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.components.jsonrpc_utils import Binary
from gosa.common.gjson import loads
from gosa.dbus import get_system_bus
import shutil
import xdg.DesktopEntry
import xdg.Menu
from bs4 import BeautifulSoup

from xml.dom.minidom import getDOMImplementation
import os

XDG_CONFIG_DIR = "/etc/xdg/xdg-gnome"
XDG_MENU_PREFIX = "gnome-"
GLOBAL_MENU = XDG_CONFIG_DIR + '/menus/' + XDG_MENU_PREFIX + 'applications.menu'

class DBusEnvironmentHandler(dbus.service.Object, Plugin):
    """
    This dbus plugin is able to configure a users environment.

    """
    add_other_menu = False
    home_dir = None
    username = None
    local_menu = os.path.join(".config", "menus", XDG_MENU_PREFIX + 'applications.menu')
    local_applications = os.path.join(".local", "share", "applications")
    local_application_scripts = os.path.join(".local", "share", "goto", "applications")
    local_application_scripts_log = os.path.join(".local", "share", "goto", "log", "applications")
    local_icons = os.path.join(".local", "share", "icons")
    local_directories = os.path.join(".local", "share", "desktop-directories")
    __initialized_dirs = []

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/gosa/environment')
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def query_output(self, user):
        result = None
        cmd = ['sudo', '-n', '-u', user, 'DISPLAY=:0', 'xrandr', '-q']
        try:
            p = subprocess.Popen(
                cmd,
                shell=False,
                bufsize=-1,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True
            )

            stdout, stderr = p.communicate()
            stdout = stdout.decode('utf-8')
            stderr = stderr.decode('utf-8')

            if p.returncode != 0:
                self.log.error("{} was terminated by signal {}: {}".format(" ".join(cmd), p.returncode, stderr))
            else:
                self.log.debug("{} returned {}: {}".format(" ".join(cmd), p.returncode, stdout))

        except OSError as e:
            self.log.error("%s execution failed: %s" % (" ".join(cmd), str(e)))

        monitor = None
        resulution = None

        for line in [x for x in stdout.split('\n')]:
            if " connected " in line:
                [monitor, x1, x2, resolution, x3] = line.split(" ", 4)
                [resolution, x_offset, y_offset] = resolution.split('+')
                result = [monitor, resolution]

        self.log.debug("Current resolution for {}: {} @ {}".format(user, monitor, resolution))
        return result


    def set_resolution(self, user, monitor, width, height):
        result = False
        cmd = ['sudo', '-n', '-u', user, 'DISPLAY=:0', 'xrandr', '--output', monitor, '--mode', str(height) + 'x' + str(width)]
        try:
            p = subprocess.Popen(
                cmd,
                shell=False,
                bufsize=-1,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True
            )

            stdout, stderr = p.communicate()
            stdout = stdout.decode('utf-8')
            stderr = stderr.decode('utf-8')
            result = True
            if p.returncode != 0:
                self.log.error("{} was terminated by signal {}: {}".format(" ".join(cmd), p.returncode, stderr))
            else:
                self.log.debug("{} returned {}: {}".format(" ".join(cmd), p.returncode, stdout))

        except OSError as e:
            self.log.error("%s execution failed: %s" % (" ".join(cmd), str(e)))


    @dbus.service.method('org.gosa', in_signature='sii', out_signature='')
    def configureUserScreen(self, user, height, width):
        # Run command as user using sudo
        current = self.query_output(user)
        if current is not None:
            [monitor, resolution] = current
            if monitor is not None and resolution.split != str(height) + "x" + str(width):
                if self.set_resolution(user, monitor, width, height):
                    self.log.info("configured %s screen resolution to %sx%s: done" % (user, width, height))
            else:
                self.log.info("configured %s screen resolution to %sx%s: already configured" % (user, width, height))


    @dbus.service.method('org.gosa', in_signature='ss', out_signature='')
    def configureUserMenu(self, user, user_menu):
        """ configure a users application menu """
        user_menu = loads(user_menu)
        pw_ent = pwd.getpwnam(user)
        uid = pw_ent.pw_uid
        gid = pw_ent.pw_gid

        self.__initialized_dirs = []
        self.home_dir = os.path.expanduser('~%s' % user)
        self.username = user
        self.init_directories(user_menu)
        scripts = self.init_applications(user_menu)
        self.init_menu(user_menu)
        self.chown_dirs(uid, gid)
        if len(scripts) > 0:
            # script files need to be chowned to user always
            for script in scripts:
                self.__chown(script['path'], uid, gid)
                os.chmod(script['path'], stat.S_IRUSR | stat.S_IXUSR)

        for script in scripts:
            # Write gosaApplicationParameter values in execution environment
            environment = {}
            for env_entry in script['environment']:
               environment.update(env_entry)

            script_log = os.path.join(self.home_dir, self.local_application_scripts_log, os.path.basename(script['path']) + '.log')
            # Run command as user using sudo
            cmd = ['sudo', '-n', '-u', user, '"DISPLAY=:0"', '-i', script['path']]
            self.log.debug("executing {script} as {user}, logging to {log}".format(script=" ".join(cmd), user=pw_ent.pw_name, log=script_log))
            try:
                with open(script_log, 'w+') as logfile:
                    p = subprocess.Popen(
                        cmd,
                        shell=False,
                        env=environment,
                        bufsize=-1,
                        stdout=logfile,
                        stderr=logfile,
                        close_fds=True
                    )

                    returncode = p.wait()
                    if returncode != 0:
                        self.log.error("{} was terminated by signal {}: check {}".format(script['path'], returncode, script_log))
                    else:
                        self.log.info("{} returned {}".format(script['path'], returncode))
            except OSError as e:
                self.log.error("%s execution failed: %s" % (script['path'], str(e)))
            finally:
                if os.path.exists(script_log):
                    self.__chown(script_log, uid, gid)

    def chown_dirs(self, user, primary_group):
        self.log.debug("chown %s dirs to %s:%s" % (self.__initialized_dirs, user, primary_group))
        for dir in self.__initialized_dirs:
            self.__chown(dir, user, primary_group)

    def __chown(self, path, user, group):
        os.chown(path, user, group)
        for item in glob.glob(path+'/*'):
            cur_path = os.path.join(path, item)
            if os.path.isdir(item):
                self.__chown(cur_path, user, group)
            else:
                os.chown(cur_path, user, group)

    def __chmod(self, path, mode):
        if os.path.exists(path):
            os.chmod(path, mode)

    def init_dir(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.rmtree(dir)
        os.makedirs(dir)

        self.__initialized_dirs.append(dir)

    def init_applications(self, user_menu):
        app_dir = os.path.join(self.home_dir, self.local_applications)
        self.init_dir(app_dir)

        scripts_dir = os.path.join(self.home_dir, self.local_application_scripts)
        self.init_dir(scripts_dir)

        script_logs_dir = os.path.join(self.home_dir, self.local_application_scripts_log)
        self.init_dir(script_logs_dir)

        scripts = []

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
            file = self.write_app_script(entry)
            if file is not None:
                scripts.append(file)
            self.write_app(entry)

        return scripts

    def init_directories(self, user_menu):
        loc_dir = os.path.join(self.home_dir, self.local_directories)
        self.init_dir(loc_dir)

        icon_dir = os.path.join(self.home_dir, self.local_icons)
        self.init_dir(icon_dir)

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
        if isinstance(icon, Binary):
            icon = icon.get()

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
        result = None

        if 'gotoLogonScript' in app_entry and app_entry['gotoLogonScript'] is not None:
            script_path = os.path.join(self.home_dir, self.local_application_scripts, app_entry['cn'])

            if os.path.exists(script_path):
                os.unlink(script_path)

            with open(script_path, 'w+') as script_file:
                script = app_entry['gotoLogonScript'].replace('\r\n', '\n')
                script_file.write(script)

            result = {'path': script_path, 'environment': app_entry.get('gosaApplicationParameter', [])}

        return result

    def init_menu(self, user_menu):
        menu_dir = os.path.join(self.home_dir, self.local_menu)
        self.__initialized_dirs.append(os.path.dirname(menu_dir))
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
                            app.string=app_entry + '.desktop'
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



