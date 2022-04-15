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
 
        self.populateEndpoint()
        self.populateTemplate()


        self.simpanAturServer.clicked.connect(self.aturServer)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


    def populateEndpoint(self):
        endpoints = ["https://geokkptraining.atrbpn.go.id/spatialapi",
                     "http://10.20.22.90:5001/spatialapi",
                    ]
        for i in endpoints:
            self.comboBoxEndpoint.addItem(i)

    def populateTemplate(self):
        folder_template = os.path.join(os.path.dirname(__file__), "../template/")
        self.direktoriTemplate.setFilePath(folder_template)

    def populateKonfigurasi(self):
        folder_config = os.path.join(os.path.dirname(__file__), "../config/")
        self.direktoriKonfigurasi.setFilePath(folder_config)

    def populateData(self):
        folder_data = os.path.join(os.path.dirname(__file__), "../data/")
        self.direktoriBatasWilayah.setFilePath(folder_data)


    def aturServer(self):
        selectedEndpoint = self.comboBoxEndpoint.currentText()
        storeSetting("pengaturan/endpoint", selectedEndpoint)
        self.accept()

    # TODO: add pengaturan direktori