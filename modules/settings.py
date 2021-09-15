import os

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
from .utils import icon, parse_raw_coordinate

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/settings.ui'))


class SettingsDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Zoom to Location """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(SettingsDialog, self).__init__(parent)

        self.setupUi(self)
