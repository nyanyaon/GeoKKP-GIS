import os
import re

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.gui import QgsRubberBand

from qgis.core import (
    QgsCoordinateTransform,
    QgsRectangle,
    QgsPoint,
    QgsPointXY,
    QgsGeometry,
    QgsWkbTypes,
    QgsProject)
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

# using utils
from .utils import icon

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/coordtrans.ui'))


class CoordinateTransformDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for coordinate transformation. """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(CoordinateTransformDialog, self).__init__(parent)
        self.setWindowIcon(icon("icon.png"))

        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
