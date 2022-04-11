import os
from osgeo import ogr


from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtWidgets import QLineEdit
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.core import QgsCoordinateReferenceSystem, QgsProject

# using utils
from .utils import (
    icon,
    logMessage,
    readSetting,
    dialogBox,
)

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/pencarian_fitur.ui")
)


class PencarianFiturDialog(QtWidgets.QDialog, FORM_CLASS):
    """Kotak Dialog Pencarian Fitur"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(PencarianFiturDialog, self).__init__(parent)
        self.setWindowIcon(icon("icon.png"))
        self.setupUi(self)
        self.project = QgsProject()

        # watching event
        self.layerAsal.layerChanged.connect(self.populateColumn)
        self.kolomLayer.fieldChanged.connect(self.populateFieldSearch)
        self.pilihFitur.clicked.connect(self.featureSelect)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def populateColumn(self):
        self.currentLayer = self.layerAsal.currentLayer()
        # print(self.currentLayer)
        self.kolomLayer.setLayer(self.currentLayer)

    def populateFieldSearch(self):
        # print(self.kolomLayer.currentField())
        fieldFilter = self.kolomLayer.currentField()
        self.cariFitur.setLayer(self.currentLayer)
        self.cariFitur.setDisplayExpression('\"'+fieldFilter+'\"')

    def featureSelect(self):
        self.currentLayer.removeSelection()
        feature = self.cariFitur.feature()
        self.currentLayer.select(feature.id())
        box = self.currentLayer.boundingBoxOfSelected()
        # print(box)
        self.iface.actionZoomToSelected().trigger()
        # self.iface.mapCanvas().setExtent(box)
        self.iface.mapCanvas().refresh()
        # self.accept()
