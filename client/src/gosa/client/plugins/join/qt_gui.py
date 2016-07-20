# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import os
import gettext
from clacks.client import __version__ as VERSION
from clacks.client.plugins.join.methods import join_method
from clacks.common.components.zeroconf_client import ZeroconfClient
from pkg_resources import resource_filename #@UnresolvedImport

# Include locales
t = gettext.translation('messages', resource_filename("clacks.client", "locale"), fallback=True)
_ = t.ugettext
supported = False

if os.getenv("DISPLAY"):
    # Import PySide classes if available
    try:
        from PySide.QtCore import QApplication, QEvent, Qt, QTimer, SIGNAL, QCoreApplication  # @UnresolvedImport
        from PySide.QtGui import QDialogButtonBox, QLabel, QLineEdit, QMessageBox, QPixmap, QFormLayout, QGridLayout, QHBoxLayout, QVBoxLayout  # @UnresolvedImport
        supported = True

    except Exception as e:
        pass


if not supported:
    class QObject():
        pass

    class QWidget():
        pass

    class QFrame():
        pass


class CuteGUI(join_method):
    priority = 10

    def __init__(self, parent=None):
        self.app = QApplication([])
        super(CuteGUI, self).__init__()

    def join_dialog(self):
        key = None

        while not key:
            mwin = MainWindow()
            mwin.show()
            self.app.exec_()
            key = self.join(str(mwin.userEdit.text()), str(mwin.passwordEdit.text()))

    def end_gui(self):
        self.app.quit()

    def show_error(self, error):
        err = QMessageBox()
        err.setWindowTitle("Join error")
        err.setText(error)
        err.setIcon(QMessageBox.Critical)
        err.setModal(True)
        err.exec_()

    @staticmethod
    def available():
        global supported
        return supported

    def discover(self):
        mwin = WaitForServiceProvider()
        mwin.show()

        QTimer.singleShot(1000, self.zdiscover)
        self.app.exec_()

        return self.url

    def zdiscover(self):
        self.url = ZeroconfClient.discover(self.domain, direct=True)[0]
        self.app.quit()


class FocusNextOnReturn(QObject):

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
            obj.focusNextChild()
            return True
        else:
            # standard event processing
            return QObject.eventFilter(self, obj, event)


class AcceptOnReturn(QObject):

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
            obj.parentWidget().accept()
            return True
        else:
            # standard event processing
            return QObject.eventFilter(self, obj, event)


class MainWindow(QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Global form layout
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)

        # Header box containing label and icon
        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        header.setStyleSheet("QWidget { background-color: white; color: black;}")

        header_text = QLabel("<b>" + _("Clacks Infrastructure") + "</b><br>" + "v%s" % VERSION)
        header_text.setStyleSheet("QWidget { background-color: white; color: black; border: 0; margin: 0; padding: 3;}")
        header_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        hbox.addWidget(header_text, 1)

        header_image = QLabel()
        header_image.setStyleSheet("QWidget { background-color: white; color: black; border: 0; margin: 0; padding: 0;}")
        header_image.setAlignment(Qt.AlignRight | Qt.AlignTop)

        bg = QPixmap(resource_filename("clacks.client", "data/secure-card.png"))
        header_image.setPixmap(bg)
        hbox.addWidget(header_image)
        header.setLayout(hbox)

        form.addRow(header)

        # Dialog headline
        headline = QLabel(_("Please enter the credentials of an administrative user to join this client."))
        headline.setWordWrap(True)
        headline.setStyleSheet("QLabel { padding: 3; }")
        form.addRow(headline)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form.addRow(line)

        # Input fields for user and password
        ll = QGridLayout()
        userLabel = QLabel("User name")
        self.userEdit = QLineEdit(self)
        passwordLabel = QLabel("Password")
        self.passwordEdit = QLineEdit(self)
        self.passwordEdit.setEchoMode(QLineEdit.Password)

        # Add focus key handler for line edits
        kpe = FocusNextOnReturn(self)
        self.userEdit.installEventFilter(kpe)
        aor = AcceptOnReturn(self)
        self.passwordEdit.installEventFilter(aor)

        # Place widgets in layout
        ll.addWidget(userLabel, 0, 0)
        ll.addWidget(self.userEdit, 0, 1)
        ll.addWidget(passwordLabel, 1, 0)
        ll.addWidget(self.passwordEdit, 1, 1)
        ll.setContentsMargins(3, 3, 3, 3)
        form.addRow(ll)

        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        form.addRow(line2)

        # OK button
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        form.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)

        # Finalize the window
        self.setLayout(form)
        self.setMinimumSize(400, 150)
        self.setWindowTitle('Join client')

        self.setGeometry((QApplication.desktop().width() - self.sizeHint().width()) / 2,
            (QApplication.desktop().height() - self.sizeHint().height()) / 2,
            self.sizeHint().width(), self.sizeHint().height())

        # Disable close
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.Window | Qt.WindowTitleHint)

    def accept(self):
        if self.userEdit.text() == "" or self.passwordEdit.text() == "":
            if self.userEdit.text() == "":
                self.userEdit.setFocus()
            else:
                self.passwordEdit.setFocus()

            # meldung ausgeben, dass das doof ist so
            err = QMessageBox()
            err.setWindowTitle(_("Please provide credentials"))
            err.setText(_("You need to enter a user name and a password!"))
            err.setIcon(QMessageBox.Critical)
            err.setModal(True)
            err.exec_()

        else:
            QCoreApplication.quit()


class WaitForServiceProvider(QFrame):

    def __init__(self, parent=None):
        super(WaitForServiceProvider, self).__init__(parent)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

        # Global horizontal layout
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)

        def get_res(f):
            return resource_filename("clacks.client", "data/%s" % f)

        self.pixmaps = [QPixmap(get_res("network-wireless-connected-00.png")),
                QPixmap(get_res("network-wireless-connected-25.png")),
                QPixmap(get_res("network-wireless-connected-50.png")),
                QPixmap(get_res("network-wireless-connected-75.png")),
                QPixmap(get_res("network-wireless.png"))]
        self.pixmap_index = -1
        self.rotate_image()
        vbox.addWidget(self.image)

        label = QLabel(_("Searching service provider..."))
        self.setStyleSheet("QWidget { background-color: #F0F0F0; color: black; padding: 5;}")
        label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(label)

        # Finalize the window
        self.setLayout(vbox)
        self.setMinimumSize(300, 150)
        self.setWindowTitle(_("Searching for service provider"))

        # Disable close
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

        self.setGeometry((QApplication.desktop().width() - 300) / 2,
            (QApplication.desktop().height() - self.sizeHint().height()) / 2,
            300, self.sizeHint().height())

        # Start animation
        timer = QTimer(self)
        self.connect(timer, SIGNAL("timeout()"), self.rotate_image)
        timer.start(500)

    def rotate_image(self):
        self.pixmap_index = self.pixmap_index + 1
        if self.pixmap_index >= len(self.pixmaps):
            self.pixmap_index = 0

        self.image.setPixmap(self.pixmaps[self.pixmap_index])
