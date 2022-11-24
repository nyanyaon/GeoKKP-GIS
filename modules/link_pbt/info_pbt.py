from datetime import datetime
import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from ..memo import app_state
from ..utils import readSetting, storeSetting
from ..api import endpoints
from ..models.dataset import Dataset, DataTable

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../ui/link_pbt/pbt_info.ui")
)


class InfoPBT(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Link Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, dokumen_pengukuran_id, pbt, parent=iface.mainWindow()):
        super(InfoPBT, self).__init__(parent)
        self.setupUi(self)

        self._dokumen_pengukuran_id = dokumen_pengukuran_id
        self._pbt = pbt

        self._current_parcel = ""

        self._ds_land_use = {}
        self._ds = {}

        self.dgv_new_parcels.itemSelectionChanged.connect(
            self._dgv_new_parcels_selection_changed
        )
        self.cmb_umum.currentIndexChanged.connect(self._cmb_umum_selection_changed)
        self.btn_update.clicked.connect(self._btn_update_click)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()

    def setup_workpanel(self):
        self.dgv_new_parcels.blockSignals(True)
        kantor = readSetting("kantorterpilih", {})
        if not kantor:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih lokasi kantor lebih dahulu"
            )
            return
        self._kantor_id = kantor["kantorID"]

        self._ds_land_use = readSetting("landusedata", {})
        if not self._ds_land_use:
            response_landuse = endpoints.get_landuse_data()
            self._ds_land_use = json.loads(response_landuse.content)
            storeSetting("landusedata", self._ds_land_use)
        # print(self._ds_land_use)

        self.cmb_umum.clear()
        for item in self._ds_land_use["TIPELANDGENERIK"]:
            self.cmb_umum.addItem(item["KETERANGAN"], item["TIPEUSECODE"])

        response_ds = endpoints.get_parcel_in_pbt(self._dokumen_pengukuran_id)
        self._ds = Dataset(response_ds.content)
        self._ds.render_to_qtable_widget(
            table_name="PERSIL",
            table_widget=self.dgv_new_parcels,
            hidden_index=[0, 3, 4, 5, 7],
        )
        self.dgv_new_parcels.blockSignals(False)

    def _cmb_umum_selection_changed(self):
        self._set_cmb_khusus(self.cmb_umum.currentData())

    def _set_cmb_khusus(self, landuse_id):
        self.cmb_khusus.clear()
        # print(self.cmb_umum.currentIndex(), self.cmb_umum.currentData())
        if self.cmb_umum.currentIndex() >= 0:
            selected = -1
            for index, item in enumerate(self._ds_land_use["TIPELANDUSE"]):
                if item["TIPEUSECODE"] == self.cmb_umum.currentData():
                    self.cmb_khusus.addItem(item["LANDUSENAME"], item["LANDUSEID"])
                if item["LANDUSEID"] == landuse_id:
                    selected = index
            self.cmb_khusus.setCurrentIndex(selected)

    def _dgv_new_parcels_selection_changed(self):
        selected_row = self._ds["PERSIL"].get_selected_qtable_widget()
        if not selected_row:
            self._current_parcel = ""
            return

        if self._ds["PERSIL"]:
            self._current_parcel = selected_row[0].text()
            response_pset = endpoints.get_parcel_info(self._current_parcel)
            p_set = json.loads(response_pset.content)
            # print(p_set)
            response_pp = endpoints.get_parcel_property_for_apbn(self._current_parcel)
            pp = Dataset(response_pp.content)
            if "InfoUmum" in pp:
                pp.render_to_qtable_widget(
                    table_name="InfoUmum", table_widget=self.ppt_persil
                )
            else:
                self.ppt_persil.setRowCount(0)

            self.txt_nama_jalan.setText(p_set["PERSILBARU"][0]["NAMAJALAN"])
            self.txt_nomor.setText(p_set["PERSILBARU"][0]["NOMORBANGUNAN"])
            self.txt_alamat_tambahan.setText(p_set["PERSILBARU"][0]["ALAMATTAMBAHAN"])
            self.txt_kode_pos.setText(p_set["PERSILBARU"][0]["KODEPOS"])
            self.txt_peta.setText(p_set["PERSILBARU"][0]["PETA"])
            self.txt_nomor_peta.setText(p_set["PERSILBARU"][0]["NOPETA"])

            landuse_id = p_set["PERSILBARU"][0]["GUNATANAHKHUSUSID"]

            if landuse_id:
                selected = -1
                for index, item in enumerate(self._ds_land_use["TIPELANDGENERIK"]):
                    if item["TIPEUSECODE"] == p_set["PERSILBARU"][0]["GUNATANAHUMUMID"]:
                        selected = index
                        break

                self.cmb_umum.setCurrentIndex(selected)
                self._set_cmb_khusus(landuse_id)

    def _btn_update_click(self):
        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        if not pegawai or "userId" not in pegawai or "userId" not in pegawai:
            return

        nama_jalan = self.txt_nama_jalan.text()
        penggunaan = self.cmb_khusus.currentIndex()

        # print(nama_jalan, penggunaan)
        if len(nama_jalan) < 5 or penggunaan < 0:
            QtWidgets.QMessageBox.warning(
                self, "Perhatian", "Alamat dan penggunaan harus diisi!"
            )
            return

        now = datetime.now().isoformat()

        d_set = Dataset()
        persil = d_set.add_table("PERSIL")
        persil.add_column("PERSILID", "")
        persil.add_column("WILAYAHID", "")
        persil.add_column("NOMOR", "")
        persil.add_column("ALAMATID", "")
        persil.add_column("NOPETA", "")
        persil.add_column("USERUPDATE", "")
        persil.add_column("LASTUPDATE", "")

        guna_tanah = d_set.add_table("GUNATANAH")
        guna_tanah.add_column("PENGGUNAANTANAHID", "")
        guna_tanah.add_column("PERSILID", "")
        guna_tanah.add_column("GUNATANAHKHUSUSID", "")
        guna_tanah.add_column("USERUPDATE", "")
        guna_tanah.add_column("LASTUPDATE", "")

        alamat = d_set.add_table("ALAMAT")
        alamat.add_column("ALAMATID", "")
        alamat.add_column("NAMAJALAN", "")
        alamat.add_column("NOMORBANGUNAN", "")
        alamat.add_column("ALAMATTAMBAHAN", "")
        alamat.add_column("KODEPOS", "")
        alamat.add_column("WILAYAHID", "")
        alamat.add_column("USERUPDATE", "")
        alamat.add_column("LASTUPDATE", "")

        selected_row = self._ds["PERSIL"].get_selected_qtable_widget(raw=True)

        d_row = persil.new_row()
        d_row["PERSILID"] = selected_row["PERSILID"]
        d_row["WILAYAHID"] = selected_row["WILAYAHID"]
        if len(selected_row["NOMOR"]) == 14:
            d_row["NOMOR"] = selected_row["NOMOR"][9:14]

        if selected_row["ALAMATID"]:
            d_row["ALAMATID"] = selected_row["ALAMATID"]

        d_row["NOPETA"] = self.txt_nomor_peta.text()
        d_row["USERUPDATE"] = pegawai["userId"]
        d_row["LASTUPDATE"] = now

        d_row = alamat.new_row()
        if selected_row["ALAMATID"]:
            d_row["ALAMATID"] = selected_row["ALAMATID"]
        d_row["NAMAJALAN"] = self.txt_nama_jalan.text()
        d_row["NOMORBANGUNAN"] = self.txt_nomor.text()
        d_row["KODEPOS"] = self.txt_kode_pos.text()
        d_row["USERUPDATE"] = pegawai["userId"]
        d_row["LASTUPDATE"] = now

        d_row = guna_tanah.new_row()
        d_row["PERSILID"] = selected_row["PERSILID"]
        d_row["GUNATANAHKHUSUSID"] = self.cmb_khusus.currentData()
        d_row["USERUPDATE"] = pegawai["userId"]
        d_row["LASTUPDATE"] = now

        response = endpoints.update_persil(d_set.to_json())
        response_text = response.content.decode("utf-8")
        if response_text.split(":")[0] == "OK":
            QtWidgets.QMessageBox.information(None, "GeoKKP", "Persil telah disimpan")
        else:
            QtWidgets.QMessageBox.critical(None, "GeoKKP", response_text)
