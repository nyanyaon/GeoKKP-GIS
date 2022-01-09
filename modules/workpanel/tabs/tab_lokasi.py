import os
import json

from osgeo import ogr
from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject, QgsCoordinateReferenceSystem

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from ...utils import (
    readSetting,
    storeSetting,
    get_tm3_zone,
    sdo_to_layer,
    get_epsg_from_tm3_zone,
    set_project_crs_by_epsg,
    logMessage,
)
from ...api import endpoints
from ...memo import app_state

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../../ui/workpanel/tab_lokasi.ui")
)
adm_district_file = os.path.join(
    os.path.dirname(__file__), "../../../data/idn_adm_lv2.json"
)

STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class TabLokasi(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabLokasi, self).__init__(parent)
        self.setupUi(self)

        self.current_kantor_id = None
        self.current_tipe_kantor_id = None
        self.current_kantor = {}
        self.current_provinsi = {}
        self.current_kabupaten = {}
        self.current_kecamatan = {}
        self.current_kelurahan = {}

        self.list_kantor = []
        self.provinsi_by_kantor = {}
        self.kabupaten_by_provinsi = {}
        self.kecamatan_by_kabupaten = {}
        self.kelurahan_by_kecamatan = {}

        self.combo_kantor.currentIndexChanged.connect(self.kantor_changed)
        self.combo_provinsi.currentIndexChanged.connect(self.provinsi_changed)
        self.combo_kabupaten.currentIndexChanged.connect(self.kabupaten_changed)
        self.combo_kecamatan.currentIndexChanged.connect(self.kecamatan_changed)
        self.combo_kelurahan.currentIndexChanged.connect(self.kelurahan_changed)
        self.btn_simpan_area_kerja.clicked.connect(self.simpan_area_kerja)

        self.setup_workpanel()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()

    def read_settings(self):
        self.current_kantor = readSetting("kantorterpilih", {})
        self.current_provinsi = readSetting("provinsiterpilih", {})
        self.current_kabupaten = readSetting("kabupatenterpilih", {})
        self.current_kecamatan = readSetting("kecamatanterpilih", {})
        self.current_kelurahan = readSetting("kelurahanterpilih", {})
        self.list_kantor = readSetting("listkantor", [])

    def setup_workpanel(self):
        self.read_settings()
        self.populate_kantor()

    def clear_combobox(self, level):
        combo = [
            self.combo_kelurahan,
            self.combo_kecamatan,
            self.combo_kabupaten,
            self.combo_provinsi,
            self.combo_kantor,
        ]
        for i in range(0, level):
            combo[i].blockSignals(True)
        for i in range(0, level):
            combo[i].clear()
        for i in range(0, level):
            combo[i].blockSignals(False)

    def populate_kantor(self):
        prev = readSetting("kantorterpilih", {})
        prev_id = prev["kantorID"] if prev else None

        self.clear_combobox(5)
        current_index = 0
        for index, kantor in enumerate(self.list_kantor):
            if kantor["kantorID"] == prev_id:
                current_index = index
            self.combo_kantor.addItem(kantor["nama"])
        self.combo_kantor.setCurrentIndex(current_index)

    def populate_provinsi(self, kantor_id, tipe_kantor_id):
        prev = readSetting("provinsiterpilih", {})
        prev_id = prev["PROPINSIID"] if prev else None

        self.clear_combobox(4)
        if (
            kantor_id in self.provinsi_by_kantor.keys()
            and self.provinsi_by_kantor[kantor_id]
        ):
            data_provinsi = self.provinsi_by_kantor[kantor_id]
        else:
            response = endpoints.get_provinsi_by_kantor(kantor_id, str(tipe_kantor_id))
            response_json = json.loads(response.content)
            if response_json and len(response_json["PROPINSI"]):
                data_provinsi = response_json["PROPINSI"]
                self.provinsi_by_kantor[kantor_id] = data_provinsi
                storeSetting("provinsibykantor", self.provinsi_by_kantor)
            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Data Provinsi",
                    "Tidak bisa membaca data provinsi dari server",
                )
                return

        current_index = 0
        for index, provinsi in enumerate(data_provinsi):
            if provinsi["PROPINSIID"] == prev_id:
                current_index = index
            self.combo_provinsi.addItem(provinsi["PROPNAMA"])
        self.combo_provinsi.setCurrentIndex(current_index)

    def populate_kabupaten(self, kantor_id, tipe_kantor_id, provinsi_id):
        prev = readSetting("kabupatenterpilih", {})
        prev_id = prev["KABUPATENID"] if prev else None

        self.clear_combobox(3)
        if (
            provinsi_id in self.kabupaten_by_provinsi.keys()
            and self.kabupaten_by_provinsi[provinsi_id]
        ):
            data_kabupaten = self.kabupaten_by_provinsi[provinsi_id]
        else:
            response = endpoints.get_kabupaten_by_kantor(
                kantor_id, str(tipe_kantor_id), provinsi_id
            )
            response_json = json.loads(response.content)
            if response_json and len(response_json["KABUPATEN"]):
                data_kabupaten = response_json["KABUPATEN"]
                self.kabupaten_by_provinsi[provinsi_id] = data_kabupaten
                storeSetting("kabupatenbyprovinsi", self.kabupaten_by_provinsi)
            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Data Kabupaten",
                    "Tidak bisa membaca data kabupaten dari server",
                )
                return

        current_index = 0
        for index, kabupaten in enumerate(data_kabupaten):
            if kabupaten["KABUPATENID"] == prev_id:
                current_index = index
            self.combo_kabupaten.addItem(kabupaten["KABUNAMA"])
        self.combo_kabupaten.setCurrentIndex(current_index)

    def populate_kecamatan(self, kantor_id, tipe_kantor_id, kabupaten_id):
        prev = readSetting("kecamatanterpilih", {})
        prev_id = prev["KECAMATANID"] if prev else None

        self.clear_combobox(2)
        if (
            kabupaten_id in self.kecamatan_by_kabupaten.keys()
            and self.kecamatan_by_kabupaten[kabupaten_id]
        ):
            data_kecamatan = self.kecamatan_by_kabupaten[kabupaten_id]
        else:
            response = endpoints.get_kecamatan_by_kantor(
                kantor_id, str(tipe_kantor_id), kabupaten_id
            )
            response_json = json.loads(response.content)
            if response_json and len(response_json["KECAMATAN"]):
                data_kecamatan = response_json["KECAMATAN"]
                self.kecamatan_by_kabupaten[kabupaten_id] = data_kecamatan
                storeSetting("kecamatanbykabupaten", self.kecamatan_by_kabupaten)

            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Data Kabupaten",
                    "Tidak bisa membaca data kabupaten dari server",
                )
                return

        current_index = 0
        for index, kecamatan in enumerate(data_kecamatan):
            if kecamatan["KECAMATANID"] == prev_id:
                current_index = index
            self.combo_kecamatan.addItem(kecamatan["KECANAMA"])
        self.combo_kecamatan.setCurrentIndex(current_index)

    def populate_kelurahan(self, kantor_id, tipe_kantor_id, kecamatan_id):
        prev = readSetting("kelurahanterpilih", {})
        prev_id = prev["DESAID"] if prev else None

        self.clear_combobox(1)
        if (
            kecamatan_id in self.kelurahan_by_kecamatan.keys()
            and self.kelurahan_by_kecamatan[kecamatan_id]
        ):
            data_kelurahan = self.kelurahan_by_kecamatan[kecamatan_id]
        else:
            response = endpoints.get_desa_by_kantor(
                kantor_id, str(tipe_kantor_id), kecamatan_id
            )
            response_json = json.loads(response.content)
            if response_json and len(response_json["DESA"]):
                data_kelurahan = response_json["DESA"]
                self.kelurahan_by_kecamatan[kecamatan_id] = data_kelurahan
                storeSetting("kelurahanbykecamatan", self.kelurahan_by_kecamatan)
            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Data Kabupaten",
                    "Tidak bisa membaca data kabupaten dari server",
                )
                return

        current_index = 0
        for index, kelurahan in enumerate(data_kelurahan):
            if kelurahan["DESAID"] == prev_id:
                current_index = index
            self.combo_kelurahan.addItem(kelurahan["DESANAMA"])
        self.combo_kelurahan.setCurrentIndex(current_index)

    def kantor_changed(self, index):
        self.current_kantor = self.list_kantor[index]
        self.current_kantor_id = self.current_kantor["kantorID"]
        self.current_tipe_kantor_id = self.current_kantor["tipeKantorId"]
        self.populate_provinsi(self.current_kantor_id, self.current_tipe_kantor_id)

    def provinsi_changed(self, index):
        if self.current_kantor_id not in self.provinsi_by_kantor.keys():
            return
        data_provinsi = self.provinsi_by_kantor[self.current_kantor_id]
        self.current_provinsi = data_provinsi[index]

        current_provinsi_id = self.current_provinsi["PROPINSIID"]
        self.populate_kabupaten(
            self.current_kantor_id, self.current_tipe_kantor_id, current_provinsi_id
        )

    def kabupaten_changed(self, index):
        current_provinsi_id = self.current_provinsi["PROPINSIID"]
        if current_provinsi_id not in self.kabupaten_by_provinsi.keys():
            return
        data_kabupaten = self.kabupaten_by_provinsi[current_provinsi_id]
        self.current_kabupaten = data_kabupaten[index]

        current_kabupaten_id = self.current_kabupaten["KABUPATENID"]
        self.populate_kecamatan(
            self.current_kantor_id, self.current_tipe_kantor_id, current_kabupaten_id
        )

    def kecamatan_changed(self, index):
        current_kabupaten_id = self.current_kabupaten["KABUPATENID"]
        if current_kabupaten_id not in self.kecamatan_by_kabupaten.keys():
            return
        data_kecamatan = self.kecamatan_by_kabupaten[current_kabupaten_id]
        self.current_kecamatan = data_kecamatan[index]

        current_kecamatan_id = self.current_kecamatan["KECAMATANID"]
        self.populate_kelurahan(
            self.current_kantor_id, self.current_tipe_kantor_id, current_kecamatan_id
        )

    def kelurahan_changed(self, index):
        current_kecamatan_id = self.current_kecamatan["KECAMATANID"]
        if current_kecamatan_id not in self.kelurahan_by_kecamatan.keys():
            return
        data_kelurahan = self.kelurahan_by_kecamatan[current_kecamatan_id]

        self.current_kelurahan = data_kelurahan[index]

    def simpan_area_kerja(self):
        storeSetting("kantorterpilih", self.current_kantor)
        storeSetting("provinsiterpilih", self.current_provinsi)
        storeSetting("kabupatenterpilih", self.current_kabupaten)
        storeSetting("kecamatanterpilih", self.current_kecamatan)
        storeSetting("kelurahanterpilih", self.current_kelurahan)
        self.get_pagawai()
        self.set_project_crs()

    def get_pagawai(self):
        kantor_id = self.current_kantor_id
        username = app_state.get("username", None)
        if not (username and kantor_id):
            return
        response = endpoints.get_user_entity_by_username(username.value, kantor_id)
        response_json = json.loads(response.content)
        print("get_user_entity_by_username", response_json)
        app_state.set("pegawai", response_json)

    def _set_crs_by_local_data(self):
        print("using local data")
        iface.mainWindow().blockSignals(True)
        driver = ogr.GetDriverByName("TopoJSON")
        dataSource = driver.Open(adm_district_file, 0)
        layer = dataSource.GetLayer()
        if not layer:
            QtWidgets.QMessageBox.warning("Gagal membaca sumber referensi TM3")

        layer.SetAttributeFilter(
            f"UPPER(WAK) = '{self.current_kabupaten['KABUNAMA'].upper()}'"
        )

        for feature in layer:
            geom = feature.GetGeometryRef()
            long = geom.Centroid().GetX()
            self.zone = get_tm3_zone(long)
        layer.ResetReading()
        try:
            epsg = get_epsg_from_tm3_zone(self.zone)
            set_project_crs_by_epsg(epsg)
        except Exception:
            logMessage("Zona TM-3 tidak ditemukan!")

    def set_project_crs(self):
        tm3_zone = (
            self.current_kelurahan["ZONATM3"]
            if self.current_kelurahan["ZONATM3"]
            else self.current_kabupaten["ZONATM3"]
        )
        if tm3_zone:
            epsg = get_epsg_from_tm3_zone(tm3_zone, False)
            set_project_crs_by_epsg(f"EPSG:{epsg}")
            self.get_batas_desa(self.current_kelurahan["DESAID"], epsg)
        else:
            self._set_crs_by_local_data()
            self.get_batas_desa(self.current_kelurahan["DESAID"], None)

    def get_batas_desa(self, wilayah_id, epsg):
        response = endpoints.get_wilayah_sdo(wilayah_id, "Desa", epsg)
        response_json = json.loads(response.content)
        epsg_string = f"EPSG:{epsg}" if epsg else None
        if response_json["status"] and len(response_json["wilayahs"]):
            layer = sdo_to_layer(response_json["wilayahs"], "Batas Desa", epsg_string)
            layer.setReadOnly(True)
            QgsProject.instance().addMapLayer(layer)
            iface.actionZoomToLayer().trigger()
        else:
            QtWidgets.QMessageBox.warning(
                None,
                "Perhatian",
                "Batas Desa tidak ditemukan,\nBatas desa tidak akan ditampilkan di QGIS",
            )
