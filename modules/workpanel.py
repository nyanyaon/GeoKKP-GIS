import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from .login import LoginDialog

# using utils
from .utils import (
    icon,
    readSetting,
    storeSetting,
    get_epsg_from_tm3_zone,
    set_project_crs_by_epsg,
    sdo_to_layer
)
from .api import endpoints

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/panel_kerjav2.ui'))


STACKWIDGET_RUTIN = 1


class Workpanel(QtWidgets.QDockWidget, FORM_CLASS):
    """ Dialog for Peta Bidang """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(Workpanel, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(icon("icon.png"))
        self.stackedWidget.setCurrentIndex(0)
        self.project = QgsProject

        self.loginaction = LoginDialog()

        self.current_kantor_id = None
        self.current_tipe_kantor_id = None
        self.current_provinsi_id = None
        self.current_kabupaten_id = None
        self.current_kecamatan_id = None
        self.current_kelurahan_id = None

        self.mulaiGeokkp.clicked.connect(self.login_geokkp)
        self.btn_simpan_area_kerja.clicked.connect(self.simpan_area_kerja)
        self.stackedWidget.currentChanged.connect(self.setup_workpanel)

        self.combo_kantor.currentIndexChanged.connect(self.kantor_changed)
        self.combo_provinsi.currentIndexChanged.connect(self.provinsi_changed)
        self.combo_kabupaten.currentIndexChanged.connect(self.kabupaten_changed)
        self.combo_kecamatan.currentIndexChanged.connect(self.kecamatan_changed)
        self.combo_kelurahan.currentIndexChanged.connect(self.kelurahan_changed)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()

    def login_geokkp(self):
        if self.loginaction is None:
            self.loginaction = LoginDialog()
        self.loginaction.show()

    def show_workpanel(self):
        workspace = readSetting("workspace_terpilih", "rutin")
        widget = getattr(self, workspace, self.rutin)
        self.stackedWidget.setCurrentWidget(widget)

    def switch_panel(self, page):
        self.stackedWidget.setCurrentIndex(page)

    def setup_workpanel(self, index):
        if index == STACKWIDGET_RUTIN:
            self.setup_workspace_rutin()

    # Workspace Rutin
    def setup_workspace_rutin(self):
        self.populate_kantor()

    def kantor_changed(self, index):
        data_kantor = readSetting("listkantor", [])
        kantor = data_kantor[index]
        self.current_kantor_id = kantor["kantorID"]
        self.current_tipe_kantor_id = kantor["tipeKantorId"]
        storeSetting("kantorterpilih", kantor)
        self.populate_provinsi(self.current_kantor_id, self.current_tipe_kantor_id)

    def provinsi_changed(self, index):
        data_provinsi = readSetting("listprovinsi", [])
        provinsi = data_provinsi[index]
        self.current_provinsi_id = provinsi["PROPINSIID"]
        storeSetting("provinsiterpilih", provinsi)
        self.populate_kabupaten(self.current_kantor_id, self.current_tipe_kantor_id, self.current_provinsi_id)

    def kabupaten_changed(self, index):
        data_kabupaten = readSetting("listkabupaten", [])
        kabupaten = data_kabupaten[index]
        self.current_kabupaten_id = kabupaten["KABUPATENID"]
        storeSetting("kabupatenterpilih", kabupaten)
        self.populate_kecamatan(self.current_kantor_id, self.current_tipe_kantor_id, self.current_kabupaten_id)

    def kecamatan_changed(self, index):
        data_kecamatan = readSetting("listkecamatan", [])
        kecamatan = data_kecamatan[index]
        self.current_kecamatan_id = kecamatan["KECAMATANID"]
        storeSetting("kecamatanterpilih", kecamatan)
        self.populate_kelurahan(self.current_kantor_id, self.current_tipe_kantor_id, self.current_kecamatan_id)

    def kelurahan_changed(self, index):
        data_kelurahan = readSetting("listkelurahan", [])
        kelurahan = data_kelurahan[index]
        self.current_kelurahan_id = kelurahan["DESAID"]
        storeSetting("kelurahanterpilih", kelurahan)

    def populate_kantor(self):
        self.combo_kantor.clear()
        data_kantor = readSetting("listkantor", [])
        for kantor in data_kantor:
            self.combo_kantor.addItem(kantor["nama"])

    def populate_provinsi(self, kantor_id, tipe_kantor_id):
        self.combo_provinsi.clear()
        response = endpoints.get_provinsi_by_kantor(kantor_id, str(tipe_kantor_id))
        response_json = json.loads(response.content)
        if response_json and len(response_json['PROPINSI']):
            data_provinsi = response_json['PROPINSI']
            storeSetting("listprovinsi", data_provinsi)
            for provinsi in data_provinsi:
                self.combo_provinsi.addItem(provinsi["PROPNAMA"])

    def populate_kabupaten(self, kantor_id, tipe_kantor_id, provinsi_id):
        self.combo_kabupaten.clear()
        response = endpoints.get_kabupaten_by_kantor(kantor_id, str(tipe_kantor_id), provinsi_id)
        response_json = json.loads(response.content)
        if response_json and len(response_json['KABUPATEN']):
            data_kabupaten = response_json['KABUPATEN']
            storeSetting("listkabupaten", data_kabupaten)
            for kabupaten in data_kabupaten:
                self.combo_kabupaten.addItem(kabupaten["KABUNAMA"])

    def populate_kecamatan(self, kantor_id, tipe_kantor_id, kabupaten_id):
        self.combo_kecamatan.clear()
        response = endpoints.get_kecamatan_by_kantor(kantor_id, str(tipe_kantor_id), kabupaten_id)
        response_json = json.loads(response.content)
        if response_json and len(response_json['KECAMATAN']):
            data_kecamatan = response_json['KECAMATAN']
            storeSetting("listkecamatan", data_kecamatan)
            for kecamatan in data_kecamatan:
                self.combo_kecamatan.addItem(kecamatan["KECANAMA"])

    def populate_kelurahan(self, kantor_id, tipe_kantor_id, kecamatan_id):
        self.combo_kelurahan.clear()
        response = endpoints.get_desa_by_kantor(kantor_id, str(tipe_kantor_id), kecamatan_id)
        response_json = json.loads(response.content)
        if response_json and len(response_json['DESA']):
            data_kelurahan = response_json['DESA']
            storeSetting("listkelurahan", data_kelurahan)
            for kelurahan in data_kelurahan:
                self.combo_kelurahan.addItem(kelurahan["DESANAMA"])

    def simpan_area_kerja(self):
        kabupaten = readSetting("kabupatenterpilih")
        kelurahan = readSetting("kelurahanterpilih")
        tm3_zone = kelurahan['ZONATM3'] if kelurahan['ZONATM3'] else kabupaten['ZONATM3']
        if tm3_zone:
            epsg = get_epsg_from_tm3_zone(tm3_zone, False)
            self.set_project_crs(epsg)
            self.get_batas_desa(kelurahan["DESAID"], epsg)
        else:
            QtWidgets.QMessageBox.critical(None, 'Error', 'Zona TM3 Tidak tersedia di server')

    def set_project_crs(self, epsg):
        set_project_crs_by_epsg(f'EPSG:{epsg}')

    def get_batas_desa(self, wilayah_id, epsg):
        response = endpoints.get_wilayah_sdo(wilayah_id, 'Desa', epsg)
        response_json = json.loads(response.content)
        if response_json["status"] and len(response_json["wilayahs"]):
            layer = sdo_to_layer(response_json["wilayahs"], "Batas Desa", f"EPSG:{epsg}")
            layer.setReadOnly(True)
            QgsProject.instance().addMapLayer(layer)
        else:
            QtWidgets.QMessageBox.critical(None, 'Error', 'Desa tidak ditemukan')
