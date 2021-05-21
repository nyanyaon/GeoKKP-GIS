import os

from qgis.PyQt import QtWidgets, uic

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/login.ui'))


class LoginDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Login """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
