import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from .api import endpoints
from .utils import (
    get_layer_config,
    sdo_to_layer,
    get_epsg_from_tm3_zone,
    readSetting
)

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/import_wilayah_admin.ui")
)


class ImportWilayahAdmin(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(ImportWilayahAdmin, self).__init__(parent)
        self.setupUi(self)

        self._srid_code = [
            23830,
            23831,
            23832,
            23833,
            23834,
            23835,
            23836,
            23837,
            23838,
            23839,
            23840,
            23841,
            23842,
            23843,
            23844,
            23845
        ]
        self._kantor_id = ""
        self._tipe_kantor_id = ""

        self.cmb_propinsi.currentIndexChanged.connect(self._cmb_propinsi_selected_index_changed)
        self.cmb_kabupaten.currentIndexChanged.connect(self._cmb_kabupaten_selected_index_changed)
        self.cmb_kecamatan.currentIndexChanged.connect(self._cmb_kecamatan_selected_index_changed)
        self.btn_download_propinsi_terpilih.clicked.connect(self._download_propinsi_terpilih_click)
        self.btn_download_kabupaten_terpilih.clicked.connect(self._download_kabupaten_terpilih_click)
        self.btn_download_kecamatan_terpilih.clicked.connect(self._download_kecamatan_terpilih_click)
        self.btn_download_desa_terpilih.clicked.connect(self._download_desa_terpilih_click)
        self.btn_download_kabupatens.clicked.connect(self._btn_download_kabupatens_click)
        self.btn_download_kecamatans.clicked.connect(self._btn_download_kecamatans_click)
        self.btn_download_desas.clicked.connect(self._btn_download_desas_click)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setup_workpanel(self):
        kantor = readSetting("kantorterpilih", {})
        if not kantor:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih lokasi kantor lebih dahulu"
            )
            self.close()
            return

        self._kantor_id = kantor["kantorID"]
        self._tipe_kantor_id = str(kantor["tipeKantorId"])

        self.cmb_coordinate_system.clear()
        self.cmb_coordinate_system.addItem("46.2")
        self.cmb_coordinate_system.addItem("47.1")
        self.cmb_coordinate_system.addItem("47.2")
        self.cmb_coordinate_system.addItem("48.1")
        self.cmb_coordinate_system.addItem("48.2")
        self.cmb_coordinate_system.addItem("49.1")
        self.cmb_coordinate_system.addItem("49.2")
        self.cmb_coordinate_system.addItem("50.1")
        self.cmb_coordinate_system.addItem("50.2")
        self.cmb_coordinate_system.addItem("51.1")
        self.cmb_coordinate_system.addItem("51.2")
        self.cmb_coordinate_system.addItem("52.1")
        self.cmb_coordinate_system.addItem("52.2")
        self.cmb_coordinate_system.addItem("53.1")
        self.cmb_coordinate_system.addItem("53.2")
        self.cmb_coordinate_system.addItem("54.1")

        self._set_cmb_propinsi()

    def _cmb_propinsi_selected_index_changed(self):
        self._set_cmb_kabupaten()

    def _cmb_kabupaten_selected_index_changed(self):
        self._set_cmb_kecamatan()

    def _cmb_kecamatan_selected_index_changed(self):
        self._set_cmb_desa()

    def _set_cmb_propinsi(self):
        response = endpoints.get_provinsi_by_kantor(
            self._kantor_id, self._tipe_kantor_id
        )
        prop_dataset = json.loads(response.content)

        self.cmb_propinsi.clear()
        for prop in prop_dataset["PROPINSI"]:
            self.cmb_propinsi.addItem(prop["PROPNAMA"], prop["PROPINSIID"])

    def _set_cmb_kabupaten(self):
        selected_prov = self.cmb_propinsi.currentData()
        response = endpoints.get_kabupaten_by_kantor(
            self._kantor_id, self._tipe_kantor_id, selected_prov
        )
        kabu_dataset = json.loads(response.content)

        self.cmb_kabupaten.clear()
        for kab in kabu_dataset["KABUPATEN"]:
            self.cmb_kabupaten.addItem(kab["KABUNAMA"], kab["KABUPATENID"])

    def _set_cmb_kecamatan(self):
        selected_kab = self.cmb_kabupaten.currentData()
        response = endpoints.get_kecamatan_by_kantor(
            self._kantor_id, self._tipe_kantor_id, selected_kab
        )
        keca_dataset = json.loads(response.content)

        self.cmb_kecamatan.clear()
        for kec in keca_dataset["KECAMATAN"]:
            self.cmb_kecamatan.addItem(kec["KECANAMA"], kec["KECAMATANID"])

    def _set_cmb_desa(self):
        selected_kec = self.cmb_kecamatan.currentData()
        response = endpoints.get_desa_by_kantor(
            self._kantor_id, self._tipe_kantor_id, selected_kec
        )
        desa_dataset = json.loads(response.content)

        self.cmb_desa.clear()
        for des in desa_dataset["DESA"]:
            self.cmb_desa.addItem(des["DESANAMA"], des["DESAID"])

    def _download_propinsi_terpilih_click(self):
        wilayah_id = self.cmb_propinsi.currentData()
        srid = self.cmb_coordinate_system.currentIndex()
        srs = str(self._srid_code[srid])
        response = endpoints.unduh_wilayah_sdo(wilayah_id, srs, "Propinsi")
        response_json = json.loads(response.content)

        zone = srs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)
        layer_config = get_layer_config("010200")
        if response_json["wilayahs"]:
            sdo_to_layer(
                response_json["wilayahs"],
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )

    def _download_kabupaten_terpilih_click(self):
        wilayah_id = self.cmb_kabupaten.currentData()
        srid = self.cmb_coordinate_system.currentIndex()
        srs = str(self._srid_code[srid])
        response = endpoints.unduh_wilayah_sdo(wilayah_id, srs, "Kabupaten")
        response_json = json.loads(response.content)
        # print(response_json)

        zone = srs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)
        layer_config = get_layer_config("010300")
        if response_json["wilayahs"]:
            sdo_to_layer(
                response_json["wilayahs"],
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )

    def _download_kecamatan_terpilih_click(self):
        wilayah_id = self.cmb_kecamatan.currentData()
        srid = self.cmb_coordinate_system.currentIndex()
        srs = str(self._srid_code[srid])
        response = endpoints.unduh_wilayah_sdo(wilayah_id, srs, "Kecamatan")
        response_json = json.loads(response.content)

        zone = srs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)
        layer_config = get_layer_config("010400")
        if response_json["wilayahs"]:
            sdo_to_layer(
                response_json["wilayahs"],
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )

    def _download_desa_terpilih_click(self):
        wilayah_id = self.cmb_desa.currentData()
        srid = self.cmb_coordinate_system.currentIndex()
        srs = str(self._srid_code[srid])
        response = endpoints.unduh_wilayah_sdo(wilayah_id, srs, "Desa")
        response_json = json.loads(response.content)

        zone = srs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)
        layer_config = get_layer_config("010500")
        if response_json["wilayahs"]:
            sdo_to_layer(
                response_json["wilayahs"],
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )

    def _btn_download_kabupatens_click(self):
        wilayah_ids = [self.cmb_kabupaten.itemData(i) for i in range(self.cmb_kabupaten.count())]
        srid = self.cmb_coordinate_system.currentIndex()
        srs = str(self._srid_code[srid])

        sdos = []
        for wilayah_id in wilayah_ids:
            response = endpoints.unduh_wilayah_sdo(wilayah_id, srs, "Kabupaten")
            response_json = json.loads(response.content)
            sdos += response_json["wilayahs"]

        zone = srs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)
        layer_config = get_layer_config("010300")
        if sdos:
            sdo_to_layer(
                sdos,
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )

    def _btn_download_kecamatans_click(self):
        wilayah_ids = [self.cmb_kecamatan.itemData(i) for i in range(self.cmb_kecamatan.count())]
        srid = self.cmb_coordinate_system.currentIndex()
        srs = str(self._srid_code[srid])

        sdos = []
        for wilayah_id in wilayah_ids:
            response = endpoints.unduh_wilayah_sdo(wilayah_id, srs, "Kecamatan")
            response_json = json.loads(response.content)
            sdos += response_json["wilayahs"]

        zone = srs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)
        layer_config = get_layer_config("010400")
        if sdos:
            sdo_to_layer(
                sdos,
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )

    def _btn_download_desas_click(self):
        wilayah_ids = [self.cmb_desa.itemData(i) for i in range(self.cmb_desa.count())]
        srid = self.cmb_coordinate_system.currentIndex()
        srs = str(self._srid_code[srid])

        sdos = []
        for wilayah_id in wilayah_ids:
            response = endpoints.unduh_wilayah_sdo(wilayah_id, srs, "Desa")
            response_json = json.loads(response.content)
            sdos += response_json["wilayahs"]

        zone = srs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)
        layer_config = get_layer_config("010500")
        if sdos:
            sdo_to_layer(
                sdos,
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )
