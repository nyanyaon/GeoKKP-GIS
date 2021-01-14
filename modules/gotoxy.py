import os
import re

from PyQt5 import uic
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsRectangle,
                       QgsPointXY,
                       QgsGeometry,
                       QgsVectorLayer,
                       QgsFeature)
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal


#using utils
from .utils import zoomTo


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/goto.ui'))


class GotoXYDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Zoom to Location """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(GotoXYDialog, self).__init__(parent)
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.zoomtoxy)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def zoomtoxy(self):
        text = self.mLineEditXY.text().strip()
        try:
            coords = re.split(r'[\s,;:]+', text, 1)
            lat = float(coords[0])
            lon = float(coords[1])
            print("lat:", lat, " long:", lon)
            pt = zoomTo(epsg4326, lat, lon)
            
        except Exception:
            pass
        

    