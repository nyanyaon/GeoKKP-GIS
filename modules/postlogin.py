import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.core import (
    QgsProject,
    QgsSettings
)

from .utils import readSetting, storeSetting, logMessage
from .api import endpoints
from .memo import app_state


layer_json_file = os.path.join(
    os.path.dirname(__file__), '../config/layers.json')
#basemap_json_file = os.path.join(
#    os.path.dirname(__file__), '../config/basemap.json')

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/postlogin2.ui'))


class PostLoginDock(QtWidgets.QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        """Constructor."""
        super(PostLoginDock, self).__init__(parent)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.setupUi(self)
        self.project = QgsProject
        self.settings = QgsSettings()


        # read settings: Jumlah Kantah Terdaftar atas nama user yang login
        jumlah_kantor = self.settings.value("geokkp/jumlahkantor")
        self.jsonKantor = self.settings.value("geokkp/listkantor")
        self.populateKantah(jumlah_kantor)
        self.simpanLayerSettings()


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def populateKantah(self, jumlahKantor):
        self.indexkantor = 0
        if not jsonKantor or not jumlahKantor:
            return
        if int(jumlahKantor) > 1:
            kantah = {}
            for item in self.jsonKantor:
                nama = item["nama"]
                kantah[nama] = item
            self._kantahs = kantah
            self.labelSatuKantah_3.hide()
            for n in range(jumlahKantor):
                self.comboBoxKantah_3.addItems(self._kantahs.keys())
        else:
            self.labelBeberapaKantah_4.hide()
            self.comboBoxKantah_3.addItems(self.jsonKantor[0])

        self.buttonLanjut_3.clicked.connect(self.simpanKantorSettings)

    def simpanKantorSettings(self):
        namaKantorTerpilih = self.comboBoxKantah_3.currentText()
        for i in self.jsonKantor:
            if (i["nama"] == namaKantorTerpilih):
                idKantorTerpilih = i["kantorID"]
        storeSetting("geokkp/kantorterpilih", [idKantorTerpilih, namaKantorTerpilih])
        self.simpanUserSettings()
        self.accept()
    
    def simpanUserSettings(self):
        username = app_state.get('username')
        kantorID = readSetting("geokkp/kantorterpilih")[0]
        response = endpoints.get_user_entity_by_username(username, kantorID)
        print(response)
        response_json = json.loads(response.content)
        #print(response_json[0]["nama"])
        #storeSetting("geokkp/listkantor", response_json)

    def simpanLayerSettings(self):
        f = open(layer_json_file,)
        data = json.load(f)
        for i in data['layers']:
            pass
        f.close()
        storeSetting("geokkp/layers", data['layers'])

    def simpanBasemapSettings(self):
        pass