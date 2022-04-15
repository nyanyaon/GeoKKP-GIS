import os
from .utils import (
    dialogBox,
    readSetting,
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

# ==== Defaults ====
folder_data = os.path.join(os.path.dirname(__file__), "../data/")
folder_config = os.path.join(os.path.dirname(__file__), "../config/")
folder_template = os.path.join(os.path.dirname(__file__), "../template/")


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
        self.populateKonfigurasi()
        self.populateData()
        
        self.pengaturanBasemap()
        self.pengaturanLayer()
        self.pengaturanKantor()

        self.simpanAturServer.clicked.connect(self.aturServer)
        self.editBerkasBasemap.clicked.connect(self.editBerkas)
        self.editBerkasLayer.clicked.connect(self.editLayer)
        self.editBerkasKantor.clicked.connect(self.editKantor)


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
        self.direktoriTemplate.setFilePath(folder_template)


    def populateKonfigurasi(self):
        self.direktoriKonfigurasi.setFilePath(folder_config)


    def populateData(self):
        self.direktoriBatasWilayah.setFilePath(folder_data)


    def aturServer(self):
        # store endpoint configuration
        storeSetting("pengaturan/endpoint", self.comboBoxEndpoint.currentText())
        # store directories configuration
        storeSetting("pengaturan/direktoritemplate", self.direktoriTemplate.filePath())
        storeSetting("pengaturan/direktorikonfigurasi", self.direktoriKonfigurasi.filePath())
        storeSetting("pengaturan/direktoribataswilayah", self.direktoriBatasWilayah.filePath())

    
    def pengaturanBasemap(self):
        dirkonfig = readSetting("pengaturan/direktorikonfigurasi")
        print(dirkonfig)
        if not dirkonfig:
            dirkonfig = folder_config
            logMessage("Mengambil pengaturan basemap dari folder default plugin")
        self.fileBasemap.setFilePath(dirkonfig)
        linktofile = os.path.join(dirkonfig, "basemap.json")
        text=open(linktofile).read()
        self.textEditBasemap.setPlainText(text)


    def editBerkas(self):
        filepath = self.fileBasemap.filePath()
        data = self.textEditBasemap.toPlainText()
        try:
            with open(filepath,'w') as f:
                f.write(data)
        except Exception as e:
            dialogBox("Gagal menyimpan berkas! Periksa log untuk melihat kesalahan")
            logMessage(str(e))


    def pengaturanLayer(self):
        dirkonfig = readSetting("pengaturan/direktorikonfigurasi")
        print(dirkonfig)
        if not dirkonfig:
            dirkonfig = folder_config
            logMessage("Mengambil pengaturan layer dari folder default plugin")
        self.fileLayer.setFilePath(dirkonfig)
        linktofile = os.path.join(dirkonfig, "layers.json")
        text=open(linktofile).read()
        self.textEditLayer.setPlainText(text)


    def editLayer(self):
        filepath = self.fileLayer.filePath()
        data = self.textEditLayer.toPlainText()
        try:
            with open(filepath,'w') as f:
                f.write(data)
        except Exception as e:
            dialogBox("Gagal menyimpan berkas! Periksa log untuk melihat kesalahan")
            logMessage(str(e))


    def pengaturanKantor(self):
        dirkonfig = readSetting("pengaturan/direktorikonfigurasi")
        print(dirkonfig)
        if not dirkonfig:
            dirkonfig = folder_config
            logMessage("Mengambil pengaturan kantor dari folder default plugin")
        self.fileKantor.setFilePath(dirkonfig)
        linktofile = os.path.join(dirkonfig, "daftar_kantor.json")
        text=open(linktofile).read()
        self.textEditKantor.setPlainText(text)


    def editKantor(self):
        filepath = self.fileKantor.filePath()
        data = self.textEditKantor.toPlainText()
        try:
            with open(filepath,'w') as f:
                f.write(data)
        except Exception as e:
            dialogBox("Gagal menyimpan berkas! Periksa log untuk melihat kesalahan")
            logMessage(str(e))

