import os
import json
from queue import Empty

from osgeo import ogr
from qgis.PyQt import QtWidgets, uic, QtGui
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
from qgis.gui import QgsTableWidgetItem
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from ...utils import (
    dialogBox,
    get_project_crs,
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
        self.project = QgsProject()

        # initialize epsg
        self.epsg = "EPSG:4326"
        self.crs = QgsCoordinateReferenceSystem(self.epsg)
        self.project.instance().crsChanged.connect(self.set_epsg)

        self.current_kantor_id = None
        self.current_tipe_kantor_id = None
        self.current_kantor = {}
        self.list_kantor = []

        self.populateTM3()

        self.combo_kantor.currentIndexChanged.connect(self.kantor_changed)
        self.btn_simpan_area_kerja.clicked.connect(self.simpan_area_kerja)
        self.btn_simpan_zonatm3.clicked.connect(self.simpan_tm3)

        self.setup_workpanel()

        # setup tabel rekap
        self.tabelRekapitulasi.setRowCount(3)
        self.tabelRekapitulasi.setColumnCount(2)

        header = self.tabelRekapitulasi.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

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
        self.populateRekapitulasi()

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
        self.populateRekapitulasi()
        # self.set_project_crs()

    def get_pagawai(self):
        kantor_id = self.current_kantor_id
        username = app_state.get("username", None)
        if not (username and kantor_id):
            return
        response = endpoints.get_user_entity_by_username(username.value, kantor_id)
        response_json = json.loads(response.content)
        # print("get_user_entity_by_username", response_json)
        app_state.set("pegawai", response_json)
        print(response_json,"response_jsonr")
        # add notif for succesful setting loaction
        if response_json["pegawaiID"]:
            QtWidgets.QMessageBox.information(
            None, "GeoKKP - Informasi", "Berhasil mengatur lokasi")

    def _set_crs_by_local_data(self):
        # print("using local data")
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

    def populateTM3(self):
        for i in range(23830, 23846):
            tm3code = QgsCoordinateReferenceSystem(i).description().split(" zone ")[1]
            self.combo_tm3.addItem(tm3code)
        self.combo_tm3.setCurrentIndex(-1)
        """
        for i in range(46, 55):
            for j in range(2, 0, -1):
                self.combo_tm3.addItem(f"{i}.{j}")
        """

    def simpan_tm3(self):
        selectedTM3 = get_epsg_from_tm3_zone(self.combo_tm3.currentText())
        try:
            # print(selectedTM3)
            set_project_crs_by_epsg(selectedTM3)
        except Exception as e:
            logMessage("pengaturan CRS Project Gagal", str(e))
            pass
        dialogBox("Berhasil mengatur CRS Project")
        self.populateRekapitulasi()

    def set_epsg(self):
        self.epsg = self.project.instance().crs().authid()
        self.crs = QgsCoordinateReferenceSystem(self.epsg)
        self.populateRekapitulasi()

    def populateRekapitulasi(self):
        username_not_done = True
        kantor_not_done = True
        crs_not_done = True

        # username
        login_state = app_state.get("logged_in")
        if not login_state.value:
            str_username = "Anda belum melakukan login ke aplikasi GeoKKP"
        else:
            username = str(app_state.get("username"))
            str_username = username
            username_not_done = False
        # print("str", str_username)
        item = QgsTableWidgetItem(str_username)
        # print(item)
        self.tabelRekapitulasi.setItem(0, 0, QgsTableWidgetItem("Pengguna GeoKKP"))
        self.tabelRekapitulasi.setItem(0, 1, item)
        if username_not_done:
            item.setBackground(QtGui.QColor(255,0,0))
        else:
            item.setBackground(QtGui.QColor(0,255,0))

        # kantor
        kantor = readSetting("kantorterpilih", {})
        try:
            kantor = kantor['nama']
        except:
            str_kantor = "Anda belum memilih lokasi kantor"
        else:
            str_kantor = kantor
            kantor_not_done = False
        item = QgsTableWidgetItem(str_kantor)
        self.tabelRekapitulasi.setItem(1, 0, QgsTableWidgetItem("Kantor Terpilih"))
        self.tabelRekapitulasi.setItem(1, 1, item)
        if kantor_not_done:
            item.setBackground(QtGui.QColor(255, 0, 0))
        else:
            item.setBackground(QtGui.QColor(0, 255, 0))

        # CRS
        epsg_no = int(self.epsg.split(":")[1])
        if epsg_no not in range(23830, 23846):
            str_crs = "Anda belum mengatur sistem koordinat TM-3"
            self.combo_tm3.setCurrentIndex(-1)
        else:
            self.combo_tm3.setCurrentIndex(epsg_no - 23830)
            str_crs = self.crs.description()
            crs_not_done = False
        item = QgsTableWidgetItem(str_crs)
        self.tabelRekapitulasi.setItem(2, 0, QgsTableWidgetItem("Sistem Proyeksi"))
        self.tabelRekapitulasi.setItem(2, 1, item)
        if crs_not_done:
            item.setBackground(QtGui.QColor(255,0,0))
        else:
            item.setBackground(QtGui.QColor(0,255,0))
