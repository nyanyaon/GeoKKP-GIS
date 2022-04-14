import os
import json

from osgeo import ogr
from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject, QgsCoordinateReferenceSystem

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from ...utils import (
    dialogBox,
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
        self.list_kantor = []

        self.populateTM3()

        self.combo_kantor.currentIndexChanged.connect(self.kantor_changed)
        self.btn_simpan_area_kerja.clicked.connect(self.simpan_area_kerja)

        self.btn_simpan_zonatm3.clicked.connect(self.simpan_tm3)

        self.setup_workpanel()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()

    def read_settings(self):
        self.current_kantor = readSetting("kantorterpilih", {})
        self.list_kantor = readSetting("listkantor", [])

    def setup_workpanel(self):
        self.read_settings()
        self.populate_kantor()

    def populate_kantor(self):
        self.combo_kantor.clear()
        prev = readSetting("kantorterpilih", {})
        prev_id = prev["kantorID"] if prev else None

        current_index = 0
        for index, kantor in enumerate(self.list_kantor):
            if kantor["kantorID"] == prev_id:
                current_index = index
            self.combo_kantor.addItem(kantor["nama"])
        # hide kantor first to avoid confusion
        self.combo_kantor.setCurrentIndex(-1)

    def kantor_changed(self, index):
        self.current_kantor = self.list_kantor[index]
        self.current_kantor_id = self.current_kantor["kantorID"]
        self.current_tipe_kantor_id = self.current_kantor["tipeKantorId"]

    def simpan_area_kerja(self):
        storeSetting("kantorterpilih", self.current_kantor)
        self.get_pagawai()
        # self.set_project_crs()

    def get_pagawai(self):
        kantor_id = self.current_kantor_id
        username = app_state.get("username", None)
        if not (username and kantor_id):
            return
        response = endpoints.get_user_entity_by_username(username.value, kantor_id)
        response_json = json.loads(response.content)
        print("get_user_entity_by_username", response_json)
        app_state.set("pegawai", response_json)

        # add notif for succesful setting loaction
        if response_json["pegawaiID"]:
            QtWidgets.QMessageBox.information(
            None, "GeoKKP - Informasi", "Berhasil mengatur lokasi")

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
            iface.actionZoomToLayers().trigger()
        else:
            QtWidgets.QMessageBox.warning(
                None,
                "Perhatian",
                "Batas Desa tidak ditemukan,\nBatas desa tidak akan ditampilkan di QGIS",
            )

    def populateTM3(self):
        for i in range(46, 55):
            for j in range(2, 0, -1):
                self.combo_tm3.addItem(f"{i}.{j}")
        self.combo_tm3.setCurrentIndex(-1)

    def simpan_tm3(self):
        selectedTM3 = get_epsg_from_tm3_zone(self.combo_tm3.currentText())
        try:
            print(selectedTM3)
            set_project_crs_by_epsg(selectedTM3)
        except Exception as e:
            logMessage("pengaturan CRS Project Gagal")
            pass
        dialogBox("Berhasil mengatur CRS Project")

