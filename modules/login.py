import os
import re

from qgis.PyQt.QtCore import Qt, QTimer, QUrl
from qgis.gui import QgsRubberBand

from PyQt5 import uic
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.PyQt import QtGui, QtWidgets, uic

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface


#using utils
from .utils import  epsg4326


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/login.ui'))

class LoginDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Login """
    
    closingPlugin = pyqtSignal()
 
    def __init__(self, parent=None):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)  


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

        