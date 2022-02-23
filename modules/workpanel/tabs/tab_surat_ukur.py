import os
import json
import re

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from ...api import endpoints
from ...utils import get_layer_config, readSetting, sdo_to_layer
from ...models.dataset import Dataset

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../../ui/workpanel/tab_surat_ukur.ui")
)


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class TabSuratUkut(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabSuratUkut, self).__init__(parent)
        self.setupUi(self)

        self.srid_code = [
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
            23845,
        ]

        self._start = 0
        self._limit = 20
        self._count = -1

        self._kantor_id = ""
        self._tipe_kantor_id = ""

        self._txt_tipe = ""
        self._txt_nomor = ""
        self._txt_tahun = ""

        self._dokumen_pengukuran_id = ""
        self._tipe_dokumen = ""
        self._wilayah_id = ""
        self._new_parcel_number = "1"
        self._new_apartment_number = "1"
        self._old_parcel = ""
        self._old_apartment = ""
        self._old_gugus_id = ""
        self._sumber_geometri = ""

        # self._set_cmb_propinsi()

        self._set_initial_state()

        self.chb_per_kabupaten.stateChanged.connect(
            self._chb_per_kabupaten_state_changed
        )
        self.cmb_propinsi.currentIndexChanged.connect(
            self._cmb_propinsi_selected_index_changed
        )
        self.cmb_kabupaten.currentIndexChanged.connect(
            self._cmb_kabupaten_selected_index_changed
        )
        self.cmb_kecamatan.currentIndexChanged.connect(
            self._cmb_kecamatan_selected_index_changed
        )
        self.cmb_tipe_dokumen.currentIndexChanged.connect(self._cmb_tipe_dokumen_selected_index_changed)
        
        self.btn_cari.clicked.connect(self._btn_cari_click)
        self.btn_first.clicked.connect(self._btn_first_click)
        self.btn_prev.clicked.connect(self._btn_prev_click)
        self.btn_next.clicked.connect(self._btn_next_click)
        self.btn_last.clicked.connect(self._btn_last_click)

        self.btn_start_process.clicked.connect(self._prepare_dokumen)
        # self.btn_save_data.clicked.connect()
        # self.btn_info_process.clicked.connect()
        # self.btn_create_layout.clicked.connect()
        self.btn_finish_process.clicked.connect(self._stop_import)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
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

        self._set_cmb_propinsi()
        # TODO : "ketika buka tab surat ukur tidak refresh propinsi, kabupaten, dll."
    
    def _set_initial_state(self):
        self.btn_start_process.setEnabled(True)
        self.btn_save_data.setEnabled(False)
        self.btn_info_process.setEnabled(False)
        self.btn_create_layout.setEnabled(False)
        self.btn_finish_process.setEnabled(False)

        self.cmb_tipe_dokumen.clear()
        self.cmb_tipe_dokumen.addItem("SU/GS/SUS/PLL/GT")
        self.cmb_tipe_dokumen.addItem("GD")
        self.cmb_tipe_dokumen.setCurrentIndex(0)

        self.toolbar_inbox.setEnabled(True)

    def _chb_per_kabupaten_state_changed(self):
        if self.chb_per_kabupaten.isChecked():
            self.cmb_desa.setVisible(False)
            self.cmb_kecamatan.setVisible(False)
            self.lbl_wilayah.setVisible(False)
            self.lbl_wilayah_induk.setVisible(False)
        else:
            self.cmb_desa.setVisible(True)
            self.cmb_kecamatan.setVisible(True)
            self.lbl_wilayah.setVisible(True)
            self.lbl_wilayah_induk.setVisible(True)

    def _cmb_propinsi_selected_index_changed(self, index):
        self._set_cmb_kabupaten()

    def _cmb_kabupaten_selected_index_changed(self, index):
        self._set_cmb_kecamatan()

    def _cmb_kecamatan_selected_index_changed(self, index):
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

    def _btn_cari_click(self):
        self._start = 0
        self._count = -1
        self._txt_nomor = self.txt_nomor.text()
        self._txt_tahun = self.txt_tahun.text()

        self._refresh_grid()

    def _refresh_grid(self):
        str_pattern = r"^([0-9]{1,5}|[0-9]{1,5}-[0-9]{1,5})((,([0-9]{1,5}|[0-9]{1,5}-[0-9]{1,5}))?)*$"

        txt_nomor = self.txt_nomor.text()
        if txt_nomor:
            if not re.match(str_pattern, txt_nomor):
                QtWidgets.QMessageBox.critical(
                    None, "GeoKKP", "Penulisan Nomor Surat Ukur Salah"
                )
                return
        
        str_pattern = r"^[0-9]{4}$"
        txt_tahun = self.txt_tahun.text()
        if txt_tahun:
            if not re.match(str_pattern, txt_tahun):
                QtWidgets.QMessageBox.critical(
                    None, "GeoKKP", "Penulisan Tahun Surat Ukur Salah"
                )
                return                
            
        wilayah_id = ""
        if self.chb_per_kabupaten.isChecked():
            wilayah_id = self.cmb_kabupaten.currentData()
        else:
            wilayah_id = self.cmb_desa.currentData()
        
        if (self.cmb_tipe_dokumen.currentText() == "SU/GS/SUS/PLL/GT"):
            print("SU/GS/SUS/PLL/GT triggered")
            response = endpoints.get_surat_ukur(
                wilayah_id,
                "*",
                self._txt_nomor,
                self._txt_tahun,
                str(self._start),
                str(self._limit),
                str(self._count),
            )
            d_set = Dataset(response.content)

            print(d_set)
            if self._count == -1:
                self._count = int(d_set["jumlahtotal"].rows[0]["COUNT(1)"])
            
            d_set.render_to_qtable_widget("suratukur", self.dgv_surat_ukur, [0,1,2,7,8])
            print(self.dgv_surat_ukur.horizontalHeaderItem(0).text)
            self.dgv_surat_ukur.setHorizontalHeaderLabels(["DOKUMENPENGUKURANID","WILAYAHID","DESA","Tipe","Nomor","Sejak","Sampai","VALID","ROWNUMS"])

            # TODO : check source code if necessary


        else:
            print("GD Triggered")

            # TODO : implement getGambarDenah

            pass
        
        if self._count > 0:
            if self._start + self._limit >= self._count:
                page = f"{self._start + 1} - {self._count} dari {self._count}"
                self.btn_next.setEnabled(False)
            else:
                page = f"{self._start + 1} - {self._start + self._limit} dari {self._count}"
                self.btn_next.setEnabled(True)
        else:
            page = "0"
            self.btn_next.setEnabled(False)
            self.btn_prev.setEnabled(False)

        if self._start == 0 or self._count == 0:
            self.btn_prev.setEnabled(False)
        else:
            self.btn_prev.setEnabled(True)
        self.txt_paging.setText(page)
    
    def _btn_first_click(self):
        self._start = 0
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)
        self._refresh_grid()

    def _btn_prev_click(self):
        self._start -= self._limit
        if self._start <= 0:
            self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)
        self._refresh_grid()

    def _btn_next_click(self):
        self._start += self._limit
        if self._start + self._limit >= self._count:
            self.btn_next.setEnabled(False)
        self.btn_prev.setEnabled(True)
        self._refresh_grid()

    def _btn_last_click(self):
        self._start = self._count // self._limit * self._limit
        print(self._start)
        if self._start >= self._count:
            self._start -= self._limit
            self.btn_prev.setEnabled(False)
        else:
            self.btn_prev.setEnabled(True)
        self.btn_next.setEnabled(False)
        self._refresh_grid()

    def _prepare_dokumen(self):
        if len(self.dgv_surat_ukur.selectedItems()) > 0 :
            self.dgv_surat_ukur.setColumnHidden(0,False)
            selected_item = self.dgv_surat_ukur.selectedItems()
            self.dgv_surat_ukur.setColumnHidden(0,True)
            self._dokumen_pengukuran_id = selected_item[0].text()
            print(self._dokumen_pengukuran_id)
            self._start_import()
        else:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih Sebuah Dokumen Yang Akan Diproses"
            )
            return

    def _start_import(self):
        response_start_import = endpoints.start_import_dokumen_pengukuran(self._dokumen_pengukuran_id)
        sdp = json.loads(response_start_import.content)
        print(sdp)
        if sdp["Status"]:
            self._dokumen_pengukuran_id = sdp["DokumenPengukuranId"]
            self._tipe_dokumen = sdp["TipeDokumen"]
            self._wilayah_id = sdp["WilayahId"]
            if "NewParcelNumber" in sdp.keys():
                self._new_parcel_number = sdp["NewParcelNumber"]
            if "NewApartmentNumber" in sdp.keys():
                self._new_apartment_number = sdp["NewApartmentNumber"]
            if "OldParcel" in sdp.keys():
                self._old_parcel = sdp["OldParcel"]
            if "OldApartment" in sdp.keys():
                self._old_apartment = sdp["OldApartment"]
            self._old_gugus_id = sdp["OldGugusIds"]
            self._sumber_geometri = sdp["SumberGeometri"]

            if self._old_gugus_id:
                print("triggered old gugus id")
                gugus_id_str = [self._old_gugus_id]
                print(gugus_id_str)
                print(self._old_gugus_id)
                response_draw_entity = endpoints.get_spatial_document_sdo(
                    gugus_id_str,False
                )
                de = json.loads(response_draw_entity.content)
                print(de)
                self._draw(de)

            else:

                pass
                # TODO: draw and the else
            
            self._set_button(True)
            if self._sumber_geometri != "AC":
                self.btn_save_data.setEnabled(True)
            else:
                self.btn_save_data.setEnabled(False)
            self.txt_nomor.setText(self._txt_nomor)
            self.txt_tahun.setText(self._txt_tahun)
            self.txt_nomor.setEnabled(False)
            self.txt_tahun.setEnabled(False)
            self.btn_cari.setEnabled(False)
            self.cmb_propinsi.setEnabled(False)
            self.cmb_kabupaten.setEnabled(False)
            self.cmb_kecamatan.setEnabled(False)
            self.cmb_desa.setEnabled(False)
            self.cmb_tipe_dokumen.setEnabled(False)
            self.btn_start_process.setEnabled(False)
            self.chb_per_kabupaten.setEnabled(False)

            # self.dgv_surat_ukur.setEnabled(False)
        
        else:
            msg = ""
            for o in sdp["errorStack"]:
                msg += f"{o} \n"
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", msg
            )
            return            

    def _set_button(self, enabled):
        self.btn_save_data.setEnabled(enabled)
        self.btn_info_process.setEnabled(enabled)
        self.btn_finish_process.setEnabled(enabled)
    
    def _draw(self, de):

        if de["status"]:
            if de["geoKkpPolygons"]:
                crs = None
                layer_config = get_layer_config("020100")
                layer = sdo_to_layer(
                    de["geoKkpPolygons"],
                    name=layer_config["Nama Layer"],
                    symbol=layer_config["Style Path"],
                    crs=crs,
                    coords_field="boundary",
                )
            if de["geoKkpGariss"]:
                layer_config = get_layer_config("020200")
                layer = sdo_to_layer(
                    de["geoKkpGariss"],
                    name=layer_config["Nama Layer"],
                    symbol=layer_config["Style Path"],
                    crs=crs,
                    coords_field="line",
                )                
                # NOTE: will deprecate it in the future
                # TODO: refactoring layer type

    def _stop_import(self):
        self._set_button(False)
        self.txt_nomor.setEnabled(True)
        self.txt_tahun.setEnabled(True)
        self.btn_cari.setEnabled(True)
        self.cmb_propinsi.setEnabled(True)
        self.cmb_kabupaten.setEnabled(True)
        self.cmb_kecamatan.setEnabled(True)
        self.cmb_desa.setEnabled(True)
        self.cmb_tipe_dokumen.setEnabled(True)

        self.btn_start_process.setEnabled(True)
        self.chb_per_kabupaten.setEnabled(True)
        self.btn_create_layout.setEnabled(False)
        # self.btn_parcel_mapping.setEnabled(False)

        # reset variable        
        self._txt_tipe = ""
        self._txt_nomor = ""
        self._txt_tahun = ""

        self._dokumen_pengukuran_id = ""
        self._tipe_dokumen = ""
        self._wilayah_id = ""
        self._new_parcel_number = "0"
        self._new_apartment_number = "0"
        self._old_parcel = ""
        self._old_apartment = ""
        self._old_gugus_id = ""
        self._sumber_geometri = ""

        # self.dgv_surat_ukur.setEnabled(True)

        QtWidgets.QMessageBox.information(
            None, "GeoKKP - Informasi", "Proses telah dihentikan"
        )
    
    def _cmb_tipe_dokumen_selected_index_changed(self):
        if self.cmb_tipe_dokumen.selectedItems() == "GD":
            self.chb_per_kabupaten.setChecked(False)
            self.chb_per_kabupaten.setEnabled(False)
        else:
            self.chb_per_kabupaten.setChecked(True)
            self.chb_per_kabupaten.setEnabled(True)            
    
    def _create_layout(self):
        pass
        # TODO: implement create layout

    def _parcel_mapping(self):
        pass
        # TODO: implement parcel mapping

    def _submit(self):
        pass
        # TODO: implement submit dan kawan2nya