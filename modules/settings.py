import os
from .utils import (
    storeSetting, 
    get_epsg_from_tm3_zone, 
    logMessage,
    set_project_crs_by_epsg,
) 

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/pengaturan.ui")
)


class SettingsDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for GeoKKP Settings"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(SettingsDialog, self).__init__(parent)

        self.setupUi(self)

        self.populateTM3()
        self.populateEndpoint()

        self.simpanAturServer.clicked.connect(self.aturServer)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


    def populateEndpoint(self):
        endpoints = ["https://geokkptraining.atrbpn.go.id/spatialapi",
                     "https://10.20.22.90:5001/spatialapi",
                    ]
        for i in endpoints:
            self.comboBoxEndpoint.addItem(i)

    def populateTM3(self):
        for i in range(46, 55):
            for j in range(2, 0, -1):
                self.comboBoxZonaTM3.addItem(f"{i}.{j}")

    def aturServer(self):
        selectedEndpoint = self.comboBoxEndpoint.currentText()
        selectedTM3 = self.comboBoxZonaTM3.currentText()
        storeSetting("pengaturan/endpoint", selectedEndpoint)
        storeSetting("pengaturan/zonatm3", selectedTM3)

        set_project_crs_by_epsg(selectedTM3)



        self.accept()