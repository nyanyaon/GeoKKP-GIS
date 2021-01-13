import requests
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsRectangle,
                       QgsPointXY,
                       QgsGeometry,
                       QgsVectorLayer,
                       QgsFeature)

import os

from PyQt5 import uic
from PyQt5 import QtWidgets

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/goto.ui'))


class GotoXYDialog(QtWidgets.QDialog, FORM_CLASS):
    """ the hash """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(GotoXYDialog, self).__init__(parent)
        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()