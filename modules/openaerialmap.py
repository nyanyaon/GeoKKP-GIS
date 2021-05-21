import os

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject, QgsRasterLayer
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/openaerialmap.ui'))


class OAMDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Login """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(OAMDialog, self).__init__(parent)
        self.setupUi(self)
        self.project = QgsProject

        self._currentLink = None
        self._currentName = None
        self.LoadOAMButton.clicked.connect(self.loadWMTS)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def loadWMTS(self):
        self._currentLink = self.OAMLink.text()
        self._currentName = self.OAMLayerName.text()
        print(self._currentLink)
        self.loadXYZ(self._currentLink, self._currentName)

    def loadXYZ(self, url, name):
        rasterLyr = QgsRasterLayer("type=xyz&zmin=0&zmax=21&url=" + url, name, "wms")
        self.project.instance().addMapLayer(rasterLyr)

# uri="url=https://tiles.openaerialmap.org/5da45f5336266f000578cc3a/0/5da45f5336266f000578cc3b/{z}/{x}/{y}&zmax=19&zmin=0"  # noqa 121
