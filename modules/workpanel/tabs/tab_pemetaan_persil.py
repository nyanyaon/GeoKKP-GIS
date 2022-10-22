import math
import os
import json
import hashlib
import re
import processing

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject, QgsMapLayer
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl, Qt
from qgis.utils import iface

from qgis.PyQt.QtWidgets import QAction

from ...memo import app_state
from ...api import endpoints
from ...utils import add_bintang, readSetting, select_layer_by_regex, storeSetting
from ...utils.geometry import get_sdo_point, get_sdo_polygon
from ...models.dataset import Dataset

from ...pemetaan_persil_masif import UploadPersilMasif

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(
        os.path.dirname(__file__), "../../../ui/workpanel/tab_pemetaan_persil.ui"
    )
)


class TabPemetaanPersil(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabPemetaanPersil, self).__init__(parent)
        self.setupUi(self)

        self._iface = iface
        # self._current_layer = self._iface.activeLayer()
        # self._canvas = self._iface.mapCanvas()

        self._current_layer = None
        self._txt = None
        
        # TODO: refactor current layer use, maybe can be clear in the end of function

        self._srid_code = [
            23838,
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
        self._pp = {}

        self.cmb_propinsi.currentIndexChanged.connect(self._cmb_propinsi_selected_index_changed)
        self.cmb_kabupaten.currentIndexChanged.connect(self._cmb_kabupaten_selected_index_changed)
        self.cmb_kecamatan.currentIndexChanged.connect(self._cmb_kecamatan_selected_index_changed)
        self.cmb_desa.currentIndexChanged.connect(self._cmb_desa_selected_index_changed)
        self.cmb_nib.currentIndexChanged.connect(self._cmb_nib_selected_index_changed)
        self.chb_per_kabupaten.stateChanged.connect(self._chb_per_kabupaten_state_changed)
        self.cmb_coordinate_system.currentIndexChanged.connect(self._cmb_coordinate_system_selected_index_changed)

        self.toolbar_pick.clicked.connect(self._pick_text)
        self.toolbar_import_bidang.clicked.connect(self._do_update)
        self.toolbar_new_bidang.clicked.connect(self._do_create_persil)
        self.toolbar_import_masif.clicked.connect(self._multi_upload)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        self._unlisten_layer_change()
        event.accept()

    def setup_workpanel(self):
        kantor = readSetting("kantorterpilih", {})
        if not kantor:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih lokasi kantor lebih dahulu"
            )
            return

        self._kantor_id = kantor["kantorID"]
        self._tipe_kantor_id = str(kantor["tipeKantorId"])

        self._current_layer = self._iface.activeLayer()
        self._canvas = self._iface.mapCanvas()

        try:
            if self._current_layer and self._current_layer.name().startswith("(080201)") or self._current_layer.name().startswith("(080202)") or self._current_layer.name().startswith("(080203)"):
                self._txt = self._current_layer
            else:
                self._txt = None
        except Exception as e:
            pass

        self._set_cmb_propinsi()

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

        # TODO: set default cmb coordinate system based on qgis crs

    def _cmb_propinsi_selected_index_changed(self):
        self._set_cmb_kabupaten()

    def _cmb_kabupaten_selected_index_changed(self):
        self._set_cmb_kecamatan()

    def _cmb_kecamatan_selected_index_changed(self):
        self._set_cmb_desa()

    def _cmb_propinsi_selected_index_changed(self):
        self._set_cmb_kabupaten()

    def _cmb_desa_selected_index_changed(self):
        if self._txt:
            layer_name = self._txt.name()
            features = self._txt.selectedFeatures()
            if not features:
                return

            text = features[0].attribute("label")
            if layer_name.startswith("(080201)") or layer_name.startswith("(080202)") or layer_name.startswith("(080203)"):
                if layer_name.startswith("(080201)"):
                    self._detect_nib(text)
                elif layer_name.startswith("(080202)"):
                    self._detect_su(text)
                elif layer_name.startswith("(080203)"):
                    self._detect_hak(text)

                if self.cmb_nib.currentData():
                    self.toolbar_import_bidang.setDisabled(False)
                else:
                    self.toolbar_import_bidang.setDisabled(True)

    def _cmb_nib_selected_index_changed(self):
        self._detect_nib(self.cmb_nib.currentData(), True)

    def _chb_per_kabupaten_state_changed(self):
        checked = self.chb_per_kabupaten.isChecked()
        if checked:
            self.cmb_desa.setHidden(True)
            self.cmb_kecamatan.setHidden(True)
            self.lbl_wilayah.setHidden(True)
            self.lbl_wilayah_induk.setHidden(True)
        else:
            self.cmb_desa.setHidden(False)
            self.cmb_kecamatan.setHidden(False)
            self.lbl_wilayah.setHidden(False)
            self.lbl_wilayah_induk.setHidden(False)

    def _set_cmb_propinsi(self):
        try:
            prop_dataset = readSetting(f"{self._kantor_id}_provinsi")
            if(prop_dataset is None):
                response = endpoints.get_provinsi_by_kantor(
                    self._kantor_id, self._tipe_kantor_id
                )
                prop_dataset = json.loads(response.content)
                storeSetting(f"{self._kantor_id}_provinsi",prop_dataset)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Gagal mendapatkan data provinsi dari server"
            )
            return

        self.cmb_propinsi.clear()
        for prop in prop_dataset["PROPINSI"]:
            self.cmb_propinsi.addItem(prop["PROPNAMA"], prop["PROPINSIID"])

    def _set_cmb_kabupaten(self):
        try:
            selected_prov = self.cmb_propinsi.currentData()
            kabu_dataset = readSetting(f"{self._kantor_id}_kabupaten_{selected_prov}")
            if(kabu_dataset is None):
                response = endpoints.get_kabupaten_by_kantor(
                    self._kantor_id, self._tipe_kantor_id, selected_prov
                )
                kabu_dataset = json.loads(response.content)
                storeSetting(f"{self._kantor_id}_kabupaten_{selected_prov}",kabu_dataset)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Gagal mendapatkan data kabupaten dari server"
            )
            return

        self.cmb_kabupaten.clear()
        for kab in kabu_dataset["KABUPATEN"]:
            self.cmb_kabupaten.addItem(kab["KABUNAMA"], kab["KABUPATENID"])

    def _set_cmb_kecamatan(self):
        try:
            selected_kab = self.cmb_kabupaten.currentData()
            keca_dataset = readSetting(f"{self._kantor_id}_kecamatan_{selected_kab}")
            if(keca_dataset is None):
                response = endpoints.get_kecamatan_by_kantor(
                    self._kantor_id, self._tipe_kantor_id, selected_kab
                )
                keca_dataset = json.loads(response.content)
                storeSetting(f"{self._kantor_id}_kecamatan_{selected_kab}",keca_dataset)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Gagal mendapatkan data kecamatan dari server"
            )
            return

        self.cmb_kecamatan.clear()
        for kec in keca_dataset["KECAMATAN"]:
            self.cmb_kecamatan.addItem(kec["KECANAMA"], kec["KECAMATANID"])

    def _set_cmb_desa(self):
        try:
            selected_kec = self.cmb_kecamatan.currentData()
            desa_dataset = readSetting(f"{self._kantor_id}_desa_{selected_kec}")
            if(desa_dataset is None):
                response = endpoints.get_desa_by_kantor(
                    self._kantor_id, self._tipe_kantor_id, selected_kec
                )
                desa_dataset = json.loads(response.content)
                storeSetting(f"{self._kantor_id}_desa_{selected_kec}",desa_dataset)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Gagal mendapatkan data desa dari server"
            )
            return

        self.cmb_desa.clear()
        for des in desa_dataset["DESA"]:
            self.cmb_desa.addItem(des["DESANAMA"], des["DESAID"])

    def _detect_nib(self, value, is_persil_id=False):
        print("detect NIB")
        wilayah_id = ""
        if self.chb_per_kabupaten.isChecked():
            wilayah_id = self.cmb_kabupaten.currentData()
        else:
            wilayah_id = self.cmb_desa.currentData()

        try:
            if is_persil_id:
                response = endpoints.get_detail_map_info_by_persil_id(value)
            else:
                response = endpoints.get_detail_map_info(wilayah_id, value)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Gagal mendapatkan data nib"
            )
            return

        print(json.loads(response.content))
        d_set = Dataset(response.content)

        if not is_persil_id:
            self.cmb_nib.clear()
            if d_set["PERSIL"].rows:
                for row in d_set["PERSIL"].rows:
                    print(row.keys())
                    print(row)
                    self.cmb_nib.addItem(row["NOMOR"], row["PERSILID"])

                selected_persil = self.cmb_nib.currentData(
                ) if self.cmb_nib.currentData() else d_set["PERSIL"].rows[0]["PERSILID"]
                selected_data = [p for p in d_set["PERSIL"].rows if p["PERSILID"] == selected_persil]
                if selected_data:
                    text_luas = f"{selected_data[0]['LUASTERTULIS']} (Luas Peta: {selected_data[0]['LUASTERHITUNG']})"
                    self.txt_luas.setText(text_luas)

                    text_alamat = ""
                    if selected_data[0]['NAMAJALAN']:
                        text_alamat += selected_data[0]['NAMAJALAN']
                    if selected_data[0]['NOMORBANGUNAN']:
                        text_alamat += " " + selected_data[0]['NOMORBANGUNAN']
                    if selected_data[0]['ALAMATTAMBAHAN']:
                        text_alamat += " " + selected_data[0]['ALAMATTAMBAHAN']
                    self.txt_alamat.setText(text_alamat)

                    text_validator = selected_data[0]["VALIDATOR"]
                    self.txt_validator.setText(text_validator)
            else:
                self.txt_luas.setText("")
                self.txt_alamat.setText("")
                self.txt_validator.setText("")

        print(d_set.keys())
        if "SERTIPIKAT" in d_set and d_set["SERTIPIKAT"].rows:
            self.cmb_hak.clear()
            for row in d_set["SERTIPIKAT"].rows:
                self.cmb_hak.addItem(row["NOMOR"], row["DOKUMENHAKID"])

            text_hak = f"{d_set['SERTIPIKAT'].rows[0]['VALIDSEJAK']} - {d_set['SERTIPIKAT'].rows[0]['VALIDSAMPAI']}"
            self.txt_berlaku_hak.setText(text_hak)

            self.dgv_pemilik.setRowCount(0)
            if "PEMILIK" in d_set and d_set["PEMILIK"].rows:
                d_set.render_to_qtable_widget(
                    table_name="PEMILIK",
                    table_widget=self.dgv_pemilik,
                    hidden_index=[0, 1, 4]
                )
        else:
            self.cmb_hak.clear()
            self.dgv_pemilik.setRowCount(0)
            self.txt_berlaku_hak.setText("")

        if "SURATUKUR" in d_set and d_set["SURATUKUR"].rows:
            for row in d_set["SURATUKUR"].rows:
                self.cmb_surat_ukur.addItem(row["NOMOR"], row["DOKUMENPENGUKURANID"])

            text_su = f"{d_set['SURATUKUR'].rows[0]['VALIDSEJAK']} - {d_set['SURATUKUR'].rows[0]['VALIDSAMPAI']}"
            self.txt_berlaku_surat_ukur.setText(text_su)
        else:
            self.cmb_surat_ukur.clear()
            self.txt_berlaku_surat_ukur.setText("")

    def _detect_su(self, txt_su):
        print("detect SU")
        str_array = txt_su.split(".")
        print(str_array)
        if len(str_array) != 2:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", "Penulisan text gu/su tidak benar"
            )
            return

        d = {
            "SU": "SU",
            "GS": "GS",
            "SUS": "SUS",
            "PLL": "PLL",
            "GT": "GT"
        }

        if str_array[0] not in d:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", "Penulisan kode gu/su tidak benar"
            )
            return

        str_array_2 = str_array[1].split("/")
        if len(str_array_2) != 2:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", "Penulisan text gu/su tidak benar"
            )
            return

        r = re.match(r"^([0-9]{1,5})*$", str_array_2[0])
        if not r:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", "Nomor SU tidak benar"
            )
            return

        if str_array_2[0] in ("00000", "0000", "000", "00", "0"):
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", f"Nomor SU tidak boleh {str_array_2[0]}"
            )
            return

        r2 = re.match(r"^([0-9]{1,4})*$", str_array_2[1])
        if not r2:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", "Tahun SU tidak benar"
            )
            return

        wilayah_id = ""
        if self.chb_per_kabupaten.isChecked():
            wilayah_id = self.cmb_kabupaten.currentData()
        else:
            wilayah_id = self.cmb_desa.currentData()

        try:
            response = endpoints.get_detail_map_info_2(
                wilayah_id,
                str_array[0],
                str_array_2[0],
                str_array_2[1]
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Gagal mendapatkan data surat ukur"
            )
            return

        d_set = Dataset(response.content)
        print(response.content)

        # TODO: check response then refactor the if d_set:

        self.cmb_nib.clear()
        if d_set["PERSIL"].rows:
            for row in d_set["PERSIL"].rows:
                self.cmb_nib.addItem(row["NOMOR"], row["PRESILID"])

            selected_persil = self.cmb_nib.currentData(
            ) if self.cmb_nib.currentData() else d_set["PERSIL"].rows[0]["PERSILID"]
            selected_data = [p for p in d_set["PERSIL"].rows if p["PERSILID"] == selected_persil]
            if selected_data:
                text_luas = f"{selected_data[0]['LUASTERTULIS']} (Luas Peta: {selected_data[0]['LUASTERHITUNG']})"
                self.txt_luas.setText(text_luas)

                text_alamat = ""
                if selected_data[0]['NAMAJALAN']:
                    text_alamat += selected_data[0]['NAMAJALAN']
                if selected_data[0]['NOMORBANGUNAN']:
                    text_alamat += " " + selected_data[0]['NOMORBANGUNAN']
                if selected_data[0]['ALAMATTAMBAHAN']:
                    text_alamat += " " + selected_data[0]['ALAMATTAMBAHAN']
                self.txt_alamat.setText(text_alamat)

                text_validator = selected_data[0]["VALIDATOR"]
                self.txt_validator.setText(text_validator)
        else:
            self.txt_luas.setText("")
            self.txt_alamat.setText("")
            self.txt_validator.setText("")

        if "SERTIPIKAT" in d_set and d_set["SERTIPIKAT"].rows:
            self.cmb_hak.clear()
            for row in d_set["SERTIPIKAT"].rows:
                self.cmb_hak.addItem(row["NOMOR"], row["DOKUMENHAKID"])

            text_hak = f"{d_set['SERTIPIKAT'].rows[0]['VALIDSEJAK']} - {d_set['SERTIPIKAT'].rows[0]['VALIDSAMPAI']}"
            self.txt_berlaku_hak.setText(text_hak)

            self.dgv_pemilik.setRowCount(0)
            if "PEMILIK" in d_set and d_set["PEMILIK"].rows:
                d_set.render_to_qtable_widget(
                    table_name="PEMILIK",
                    table_widget=self.dgv_pemilik,
                    hidden_index=[0, 1, 4]
                )
        else:
            self.cmb_hak.clear()
            self.dgv_pemilik.setRowCount(0)
            self.txt_berlaku_hak.setText("")

        if "SURATUKUR" in d_set and d_set["SURATUKUR"].rows:
            for row in d_set["SURATUKUR"].rows:
                self.cmb_surat_ukur.addItem(row["NOMOR"], row["DOKUMENPENGUKURANID"])

            text_su = f"{d_set['SURATUKUR'].rows[0]['VALIDSEJAK']} - {d_set['SURATUKUR'].rows[0]['VALIDSAMPAI']}"
            self.txt_berlaku_surat_ukur.setText(text_su)
        else:
            self.cmb_surat_ukur.clear()
            self.txt_berlaku_surat_ukur.setText("")

    def _detect_hak(self, txt_hak):
        str_array = txt_hak.split(".")
        if len(str_array) != 2:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", "Format penulisan text hak tidak benar"
            )
            return

        d = {
            "M": "1",
            "U": "2",
            "B": "3",
            "P": "4",
            "L": "5",
            "W": "8"
        }

        if str_array[0] not in d:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", "Format kode hak tidak benar"
            )
            return

        r = re.match(r"^([0-9]{1,5})*$", str_array[1])
        if not r:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", "Nomor hak tidak benar"
            )
            return

        if str_array[1] in ("00000", "0000", "000", "00", "0"):
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP Web", f"Nomor hak tidak boleh {str_array[1]}"
            )
            return

        wilayah_id = ""
        if self.chb_per_kabupaten.isChecked():
            wilayah_id = self.cmb_kabupaten.currentData()
        else:
            wilayah_id = self.cmb_desa.currentData()

        try:
            response = endpoints.get_detail_map_info_1(
                wilayah_id,
                d[str_array[0]],
                str_array[1].trim().zfill(5)
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Gagal mendapatkan data hak tanah"
            )
            return

        d_set = Dataset(response.content)

        self.cmb_nib.clear()
        if d_set["PERSIL"].rows:
            for row in d_set["PERSIL"].rows:
                self.cmb_nib.addItem(row["NOMOR"], row["PRESILID"])

            selected_persil = self.cmb_nib.currentData(
            ) if self.cmb_nib.currentData() else d_set["PERSIL"].rows[0]["PERSILID"]
            selected_data = [p for p in d_set["PERSIL"].rows if p["PERSILID"] == selected_persil]
            if selected_data:
                text_luas = f"{selected_data[0]['LUASTERTULIS']} (Luas Peta: {selected_data[0]['LUASTERHITUNG']})"
                self.txt_luas.setText(text_luas)

                text_alamat = ""
                if selected_data[0]['NAMAJALAN']:
                    text_alamat += selected_data[0]['NAMAJALAN']
                if selected_data[0]['NOMORBANGUNAN']:
                    text_alamat += " " + selected_data[0]['NOMORBANGUNAN']
                if selected_data[0]['ALAMATTAMBAHAN']:
                    text_alamat += " " + selected_data[0]['ALAMATTAMBAHAN']
                self.txt_alamat.setText(text_alamat)

                text_validator = selected_data[0]["VALIDATOR"]
                self.txt_validator.setText(text_validator)
        else:
            self.txt_luas.setText("")
            self.txt_alamat.setText("")
            self.txt_validator.setText("")

        if d_set["SERTIPIKAT"].rows:
            self.cmb_hak.clear()
            for row in d_set["SERTIPIKAT"].rows:
                self.cmb_hak.addItem(row["NOMOR"], row["DOKUMENHAKID"])

            text_hak = f"{d_set['SERTIPIKAT'].rows[0]['VALIDSEJAK']} - {d_set['SERTIPIKAT'].rows[0]['VALIDSAMPAI']}"
            self.txt_berlaku_hak.setText(text_hak)

            self.dgv_pemilik.setRowCount(0)
            if "PEMILIK" in d_set and d_set["PEMILIK"].rows:
                d_set.render_to_qtable_widget(
                    table_name="PEMILIK",
                    table_widget=self.dgv_pemilik,
                    hidden_index=[0, 1, 4]
                )
        else:
            self.cmb_hak.clear()
            self.dgv_pemilik.setRowCount(0)
            self.txt_berlaku_hak.setText("")

        if d_set["SURATUKUR"].rows:
            for row in d_set["SURATUKUR"].rows:
                self.cmb_surat_ukur.addItem(row["NOMOR"], row["DOKUMENPENGUKURANID"])

            text_su = f"{d_set['SURATUKUR'].rows[0]['VALIDSEJAK']} - {d_set['SURATUKUR'].rows[0]['VALIDSAMPAI']}"
            self.txt_berlaku_surat_ukur.setText(text_su)
        else:
            self.cmb_surat_ukur.clear()
            self.txt_berlaku_surat_ukur.setText("")
    
    def _pick_text(self):
        # TODO: add cancel pick text mode

        self._clear_all_selections()

        self._current_layer = self._iface.activeLayer()
        self._txt = None

        if self._current_layer.type() != QgsMapLayer.VectorLayer:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Layer aktif harus bertipe vektor"
            )
            return

        if self._current_layer.name().startswith("(080201)") or self._current_layer.name().startswith("(080202)") or self._current_layer.name().startswith("(080203)"):
            self._txt = self._current_layer

        self._iface.actionSelect().trigger()
        self._toggle_select_feature(True)

    def _toggle_select_feature(self, active):
        if active:
            self._listen_layer_change()
            self._listen_feature_select()
        else:
            self._unlisten_layer_change()
            self._unlisten_feature_select()

    def _listen_layer_change(self):
        try:
            self._iface.currentLayerChanged.connect(self._handle_layer_change)
        except:
            pass

    def _unlisten_layer_change(self):
        try:
            self._iface.currentLayerChanged.disconnect()
        except:
            pass

    def _handle_layer_change(self):
        # self._clear_selections()
        self._current_layer = self._iface.activeLayer()
        layer_name = self._current_layer.name()
        if layer_name.startswith("(080201)") or layer_name.startswith("(080202)") or layer_name.startswith("(080203)"):
            self._txt = self._current_layer
        else:
            self._txt = None
        print("current:",self._current_layer,"txt:",self._txt)

    def _listen_feature_select(self):
        if not self._current_layer:
            return
        try:
            self._current_layer.selectionChanged.connect(self._handle_feature_select, Qt.UniqueConnection)
        except TypeError:
            pass

    def _unlisten_feature_select(self):
        if not self._current_layer:
            return
        try:
            self._current_layer.selectionChanged.disconnect(self._handle_feature_select)
        except TypeError:
            pass

    def _handle_feature_select(self):
        if self._current_layer.type() != QgsMapLayer.VectorLayer:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Layer aktif harus bertipe vektor"
            )
            self._toggle_select_feature(False)
            return
            
        self._clear_selections([0], True)
        selected_feature = self._current_layer.selectedFeatures()
        if not selected_feature:
            # self._toggle_select_feature(False)
            return
        feature = selected_feature[0]

        layer_name = self._current_layer.name()
        print("here")
        if layer_name.startswith("(080201)") or layer_name.startswith("(080202)") or layer_name.startswith("(080203)"):
            label = feature.attribute("label") if feature.attribute("label") else ""
            self.tabWidget.setCurrentIndex(0)
            if layer_name.startswith("(080201)"):
                if label.startswith("#"):
                    self.tabWidget.setCurrentIndex(1)
                    self._new_nib(label)
                else:
                    self._detect_nib(label)
            elif layer_name.startswith("(080202)"):
                self._detect_su(label)
            elif layer_name.startswith("(080203)"):
                self._detect_hak(label)

            if not label.startswith("#") and self.cmb_nib.currentData() and self.txt_validator.text() == "":
                self.toolbar_import_bidang.setDisabled(False)
            else:
                self.toolbar_import_bidang.setDisabled(True)
            print("here it is")
            self._toggle_select_feature(False)
            self._current_layer = None
            # self._txt = None
        else:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Objek yang dipilih harus pada layer NIB / Hak / SU"
            )
            self._toggle_select_feature(False)

    def _clear_all_selections(self):
        mc = self._iface.mapCanvas()

        for layer in mc.layers():
            if layer.type() == layer.VectorLayer:
                layer.removeSelection()

        mc.refresh()

        # self._iface.mainWindow().findChild(QAction,'mActionDeselectAll').trigger()


    def _clear_selections(self, except_index=[], block_signal=False):
        if block_signal:
            self._current_layer.blockSignals(True)
        selected = self._current_layer.selectedFeatures()
        f_ids = []
        for index, feat in enumerate(selected):
            if index in except_index:
                f_ids.append(feat.id())
        self._current_layer.removeSelection()
        mc = self._iface.mapCanvas()
        for layer in mc.layers():
            if layer.type() == layer.VectorLayer:
                layer.removeSelection()
        mc.refresh()
        if f_ids:
            self._current_layer.selectByIds(f_ids)

        if block_signal:
            self._current_layer.blockSignals(False)

    def _new_nib(self, str_nis):
        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        if not pegawai or "userId" not in pegawai or "userId" not in pegawai:
            return

        self.txt_nis.setText(str_nis)
        pp = {}

        layers = select_layer_by_regex(r"^\(020100\)*")
        if not layers:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Layer batas bidang tanah (020100) tidak bisa ditemukan"
            )
            return

        processing.run("qgis:selectbylocation", {
            "INPUT": layers[0],
            "PREDICATE": 1,
            "INTERSECT": self._txt,
            "METHOD": 0,
            "selectedFeaturesOnly": True,
            "featureLimit": 1
        })

        selected_point = self._txt.selectedFeatures()
        selected_poly = layers[0].selectedFeatures()

        if not selected_poly or not selected_point:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Batas bidang tanah tidak bisa ditentukan"
            )
            return
        else:
            print("new nib")

            poly = selected_poly[0]
            point = selected_point[0]
            point_geom = point.geometry().asPoint()

            identifier = f"{self._current_layer.id()}|{point.id()}".encode("utf-8")
            objectid = hashlib.md5(identifier).hexdigest().upper()

            crs_index = self.cmb_coordinate_system.currentIndex()
            epsg = self._srid_code[crs_index]
            teks_geom = get_sdo_point(point_geom, epsg)
            poli = get_sdo_polygon(poly, epsg)

            label = (
                point.attribute("label")
                if point.attribute("label")
                else poly.attribute("label")
                if poly.attribute("label")
                else ""
            )
            height = (
                float(point.attribute("height"))
                if point.attribute("height")
                else float(poly.attribute("height"))
                if poly.attribute("height")
                else 1
            )
            orientation = (
                float(point.attribute("rotation"))
                if point.attribute("rotation")
                else float(poly.attribute("rotation"))
                if poly.attribute("rotation")
                else 0
            )

            pp["PersilId"] = objectid
            pp["Nama"] = self.cmb_nama_persil.currentData()
            pp["Boundary"] = poli["batas"]
            pp["Text"] = teks_geom
            pp["Height"] = height
            pp["Rotation"] = orientation
            pp["KantorId"] = self._kantor_id
            pp["Label"] = label
            pp["Area"] = poli["luas"]
            pp["UserUpdate"] = pegawai["userId"]

            self._pp = pp
            text_luas = str(round(poli["luas"], 3))
            self.txt_luas_peta.setText(text_luas)
            self.toolbar_new_bidang.setDisabled(False)

    def _do_update(self):
        msg = f"Anda akan melakukan pemetaan batas bidang \nApakah anda akan melanjutkan?"
        result = QtWidgets.QMessageBox.question(self, "Perhatian", msg)
        if result != QtWidgets.QMessageBox.Yes:
            return

        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        if not pegawai or "userId" not in pegawai or "userId" not in pegawai:
            return

        if not self._txt:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Pilih Teks atau titik terlebih dahulu"
            )
            return

        pp = {}
        layers = select_layer_by_regex(r"^\(020100\)*")
        if not layers:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Layer batas bidang tanah (020100) tidak bisa ditemukan"
            )
            return

        print(layers)

        processing.run("qgis:selectbylocation", {
            "INPUT": layers[0],
            "PREDICATE": 1,
            "INTERSECT": self._txt.id(),
            "METHOD": 0,
            "selectedFeaturesOnly": True,
            "featureLimit": 1
        })

        selected_point = self._txt.selectedFeatures()
        selected_poly = layers[0].selectedFeatures()

        if not selected_poly or not selected_point:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Batas bidang tanah tidak bisa ditentukan"
            )
            return
        else:
            poly = selected_poly[0]
            point = selected_point[0]
            point_geom = point.geometry().asPoint()

            persil_id = str(self.cmb_nib.currentData())
            print("persil_ID:",persil_id)

            crs_index = self.cmb_coordinate_system.currentIndex()
            epsg = self._srid_code[crs_index]

            poli = get_sdo_polygon(poly, epsg)

            label = (
                point.attribute("label")
                if point.attribute("label")
                else poly.attribute("label")
                if poly.attribute("label")
                else ""
            )
            height = (
                float(point.attribute("height"))
                if point.attribute("height")
                else float(poly.attribute("height"))
                if poly.attribute("height")
                else 1
            )
            orientation = (
                float(point.attribute("rotation"))
                if point.attribute("rotation")
                else float(poly.attribute("rotation"))
                if poly.attribute("rotation")
                else 0
            )

            if point_geom.x() < 32000 or point_geom.x() > 368000 or point_geom.y() < 282000 or point_geom.y() > 2166000:
                QtWidgets.QMessageBox.warning(
                    None, "Kesalahan", "Koordinat diluar area TM3"
                )
                return
            else:
                if self.cmb_nib.currentData():
                    teks_geom = get_sdo_point(point_geom, epsg)

                    pp["PersilId"] = persil_id
                    pp["Boundary"] = poli["batas"]
                    pp["Text"] = teks_geom
                    pp["Height"] = height
                    pp["Rotation"] = orientation
                    pp["KantorId"] = self._kantor_id
                    pp["Label"] = label
                    pp["Area"] = poli["luas"]
                    pp["UserUpdate"] = pegawai["userId"]

                    try:
                        response = endpoints.update_geometri_persil_sdo(pp)
                        response_str = response.content.decode("utf-8")
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(
                            None, "GeoKKP", response_str
                        )
                        return

                    if response_str == "OK":
                        # field_index = self._txt.fields().indexOf("label")
                        # self._txt.startEditing()
                        # self._txt.changeAttributeValue(
                        #     point.id(), field_index, f"OK: {label}"
                        # )
                        # self._txt.commitChanges()
                        coords = []
                        coord = [
                            point_geom.x(),
                            point_geom.y()
                            ]
                        coords.append(coord)
                        add_bintang(coords)

                    else:
                        QtWidgets.QMessageBox.critical(
                            None, "Kesalahan", response_str
                        )
                        return
        # delete point layer variable, so the layer can be removed safely
        self._txt = None


    def _do_create_persil(self):
        msg = f"Anda akan melakukan pembuatan peta bidang baru \nApakah anda akan melanjutkan?"
        result = QtWidgets.QMessageBox.question(self, "Perhatian", msg)
        if result != QtWidgets.QMessageBox.Yes:
            return

        wilayah_id = ""
        if self.chb_per_kabupaten.isChecked():
            wilayah_id = self.cmb_kabupaten.currentData()
        else:
            wilayah_id = self.cmb_desa.currentData()

        if "Boundary" in self._pp and self._pp["Boundary"]:
            self._pp["Nama"] = self.cmb_nama_persil.currentText()
            try:
                response = endpoints.create_persil_map_sdo(wilayah_id, self._pp)
                response_str = response.content.decode("utf-8")
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    None, "Kesalahan", response_str
                )

            if response_str.startswith("OK"):
                strspl = response_str.split("-")
                nib = strspl[1]

                field_index = self._txt.fields().indexOf("label")
                print("field_index", field_index)
                features = self._txt.getFeatures()

                txt_pos = []

                for feature in features:
                    identifier = f"{self._txt.id()}|{feature.id()}".encode("utf-8")
                    objectid = hashlib.md5(identifier).hexdigest().upper()

                    txt_point = feature.geometry().asPoint()
                    coord = [
                        txt_point.x(),
                        txt_point.y()
                        ]
                    txt_pos.append(coord)


                    if objectid == self._pp["PersilId"]:
                        self._txt.startEditing()
                        self._txt.changeAttributeValue(
                            feature.id(), field_index, nib
                        )
                        self._txt.commitChanges()
                        
                    else:
                        QtWidgets.QMessageBox.critical(
                            None, "Kesalahan", "objectid tidak cocok, gagal mengubah nib"
                        )
                        return
                
                add_bintang(txt_pos)
            else:
                QtWidgets.QMessageBox.critical(
                    None, "Kesalahan", response_str
                )
                return
        else:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Harus ada persil yang diimport"
            )
            return

        self._pp = {}
        # delete point layer variable, so the layer can be removed safely
        self._txt = None

    def _multi_upload(self):
        up = UploadPersilMasif()
        up.show()

    def _cmb_coordinate_system_selected_index_changed(self):
        self._pp = {}
        self.txt_nis.setText("")
        self.txt_luas_peta.setText("")
    