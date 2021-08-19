import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.core import (
    QgsProject,
    QgsSettings
)

from .utils import readSetting, storeSetting, logMessage, get_epsg_from_tm3_zone, set_project_crs_by_epsg
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
        if not self.jsonKantor or not jumlahKantor:
            return
        jumlahKantor = int(jumlahKantor)
        if jumlahKantor > 1:
            kantah = {}
            for item in self.jsonKantor:
                nama = item["nama"]
                kantah[nama] = item
            self._kantahs = kantah
            self.labelSatuKantah_3.hide()
            for n in range(int(jumlahKantor)):
                self.comboBoxKantah_3.addItems(self._kantahs.keys())
        else:
            self.labelBeberapaKantah_4.hide()
            self.comboBoxKantah_3.addItems(self.jsonKantor[0])

        self.buttonLanjut_3.clicked.connect(self.simpanKantorSettings)


    def simpanKantorSettings(self):
        index = self.comboBoxKantah_3.currentIndex()
        kantor = self.jsonKantor[index]
        namaKantorTerpilih = kantor['nama']
        idKantorTerpilih = kantor['kantorID']
        idTipeKantorTerpilih = kantor['tipeKantorId']

        storeSetting("geokkp/kantorterpilih", [idKantorTerpilih, namaKantorTerpilih])

        provinsi = self.simpanProvinsiSettings(idKantorTerpilih, idTipeKantorTerpilih)
        kabupaten = self.simpanKabupatenSettings(idKantorTerpilih, idTipeKantorTerpilih, provinsi['PROPINSIID'])
        kecamatan = self.simpanKecamatanSettings(idKantorTerpilih, idTipeKantorTerpilih, kabupaten['KABUPATENID'])
        desa = self.simpanDesaSettings(idKantorTerpilih, idTipeKantorTerpilih, kecamatan['KECAMATANID'])
        
        self.simpanSistemKoordinat(desa['ZONATM3'])
        self.simpanUserSettings()
        self.accept()

    def simpanProvinsiSettings(self, kantor_id, tipe_kantor_id):
        response = endpoints.get_provinsi_by_kantor(kantor_id, str(tipe_kantor_id))
        response_json = json.loads(response.content)
        provinsi = None
        if response_json and len(response_json['PROPINSI']):
            provinsi = response_json['PROPINSI'][0]
            storeSetting("geokkp/provinsiterpilih", provinsi)
        return provinsi
    
    def simpanKabupatenSettings(self, kantor_id, tipe_kantor_id, provinsi_id):
        response = endpoints.get_kabupaten_by_kantor(kantor_id, str(tipe_kantor_id), provinsi_id)
        response_json = json.loads(response.content)
        kabupaten = None
        print(len(response_json['KABUPATEN']))
        if response_json and len(response_json['KABUPATEN']):
            kabupaten = response_json['KABUPATEN'][0]
            storeSetting("geokkp/kabupatenterpilih", kabupaten)
        return kabupaten

    def simpanKecamatanSettings(self, kantor_id, tipe_kantor_id, kabupaten_id):
        response = endpoints.get_kecamatan_by_kantor(kantor_id, str(tipe_kantor_id), kabupaten_id)
        response_json = json.loads(response.content)
        kecamatan = None
        print(len(response_json['KECAMATAN']))
        if response_json and len(response_json['KECAMATAN']):
            kecamatan = response_json['KECAMATAN'][0]
            storeSetting("geokkp/kecamatanterpilih", kecamatan)
        return kecamatan

    def simpanDesaSettings(self, kantor_id, tipe_kantor_id, kecamatan_id):
        response = endpoints.get_desa_by_kantor(kantor_id, str(tipe_kantor_id), kecamatan_id)
        response_json = json.loads(response.content)
        desa = None
        print(len(response_json['DESA']))
        if response_json and len(response_json['DESA']):
            desa = response_json['DESA'][0]
            storeSetting("geokkp/desaterpilih", desa)
        return desa

    def simpanSistemKoordinat(self, tm3_zone):
        epsg = get_epsg_from_tm3_zone(tm3_zone)
        set_project_crs_by_epsg(epsg)

    def simpanUserSettings(self):
        username = app_state.get('username')
        kantorID = readSetting("geokkp/kantorterpilih")[0]
        response = endpoints.get_user_entity_by_username(username.value, kantorID)
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