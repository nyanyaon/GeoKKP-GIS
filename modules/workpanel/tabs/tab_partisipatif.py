import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsMapLayer
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from ...api import endpoints
from ...memo import app_state
from ...utils import get_layer_config, get_project_crs, readSetting, sdo_to_layer,storeSetting, get_epsg_from_tm3_zone, select_layer_by_regex
from ...topology import quick_check_topology
from ...models.dataset import Dataset
from ...create_pbt_partisipatif import CreatePBTPartisipatif

from datetime import date

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../../ui/workpanel/tab_partisipatif.ui")
)


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class TabPartisipatif(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabPartisipatif, self).__init__(parent)
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

        # NOTE: check source (C# script)
        self._kode_hak = ["", "BT1", "BT2", "BT3", "BT4", "BT5", "BT8"]
        self._txt_nomor = ""
        self._txt_tahun = ""
        self._persil_par_id = ""
        self._nomor_sertipikat = ""
        self._srid_code = ""
        self._upr = {}
        self._ds_program = {}

        self._init_ext = True

        self.cmb_propinsi.currentIndexChanged.connect(
            self._cmb_propinsi_selected_index_changed
        )
        self.cmb_kabupaten.currentIndexChanged.connect(
            self._cmb_kabupaten_selected_index_changed
        )
        self.cmb_kecamatan.currentIndexChanged.connect(
            self._cmb_kecamatan_selected_index_changed
        )

        self.btn_cari.clicked.connect(self._btn_cari_click)

        self.btn_first.clicked.connect(self._btn_first_click)
        self.btn_prev.clicked.connect(self._btn_prev_click)
        self.btn_next.clicked.connect(self._btn_next_click)
        self.btn_last.clicked.connect(self._btn_last_click)

        self.btn_unduh.clicked.connect(self._btn_unduh_clicked)
        self.btn_validasi.clicked.connect(self._btn_validasi_click)
        
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

        self._validate_layers = []

        self._set_cmb_propinsi()

        self.cmb_coordinate_system.clear()
        self.cmb_coordinate_system.addItem("TM3-46.2")
        self.cmb_coordinate_system.addItem("TM3-47.1")
        self.cmb_coordinate_system.addItem("TM3-47.2")
        self.cmb_coordinate_system.addItem("TM3-48.1")
        self.cmb_coordinate_system.addItem("TM3-48.2")
        self.cmb_coordinate_system.addItem("TM3-49.1")
        self.cmb_coordinate_system.addItem("TM3-49.2")
        self.cmb_coordinate_system.addItem("TM3-50.1")
        self.cmb_coordinate_system.addItem("TM3-50.2")
        self.cmb_coordinate_system.addItem("TM3-51.1")
        self.cmb_coordinate_system.addItem("TM3-51.2")
        self.cmb_coordinate_system.addItem("TM3-52.1")
        self.cmb_coordinate_system.addItem("TM3-52.2")
        self.cmb_coordinate_system.addItem("TM3-53.1")
        self.cmb_coordinate_system.addItem("TM3-53.2")
        self.cmb_coordinate_system.addItem("TM3-54.1")

        # TODO: set cmb coord system same with config file
        self.cmb_coordinate_system.setCurrentIndex(7)

        tahun = str(date.today().year)
        self.txt_tahun_gugus.setText(tahun)

        self._tipe_partisipatif = "perorangan"
        self.tab_widget.setCurrentIndex(0)
        self.tab_widget.currentChanged.connect(self._tab_widget_current_changed_handler)
        self._set_cmb_program()
    
    def _tab_widget_current_changed_handler(self):
        if self.tab_widget.currentIndex() == 0:
            self._tipe_partisipatif = "perorangan"
        elif self.tab_widget.currentIndex() == 1:
            self._tipe_partisipatif = "ptsl"
        print(self._tipe_partisipatif)


    def _set_cmb_program(self):
        self._ds_program = {}
        try:
            response_participatory = endpoints.get_program_participatory_mapping_by_kantor(self._kantor_id)
            self._ds_program = json.loads(response_participatory.content)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Gagal mendapatkan data program dari server"
            )
            return

        d_row = {"PROGRAMID": "","NAMA": "*"}
        self._ds_program["PROGRAM"].insert(0,d_row)
        print("ds_program:", self._ds_program)

        self.cmb_program.clear()
        for row in self._ds_program["PROGRAM"]:
            self.cmb_program.addItem(row["NAMA"],row["PROGRAMID"])

        self.cmb_program.setCurrentIndex(0)

    def _cmb_propinsi_selected_index_changed(self, index):
        self._set_cmb_kabupaten()

    def _cmb_kabupaten_selected_index_changed(self, index):
        self._set_cmb_kecamatan()

    def _cmb_kecamatan_selected_index_changed(self, index):
        self._set_cmb_desa()

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
    
    def _btn_cari_click(self):
        self._start = 0
        self._count = -1
        self._txt_nomor = self.txt_nomor.text()

        self.btn_first.setEnabled(True)
        self.btn_last.setEnabled(True)        

        crs = self.cmb_coordinate_system.currentText()
        zone = crs.replace("TM3-", "")
        self._srid_code = get_epsg_from_tm3_zone(zone, include_epsg_key=False)
        
        self._refresh_grid()

    
    def _refresh_grid(self):
        if self._tipe_partisipatif == "ptsl":
            self._refresh_grid_proyek()
            return

        wilayah_id = ""
        jenis_hak = ""
        username = app_state.get("username").value
        if self.cmb_jenis_hak.currentIndex() != -1:
            index_hak = self.cmb_jenis_hak.currentIndex()
            jenis_hak = self._kode_hak[index_hak]
        else:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih alas hak lebih dahulu"
            )
            return

        if self.cmb_desa.currentIndex() != -1:
            wilayah_id = self.cmb_desa.currentData()
            print("wilayah_id:",wilayah_id)
        
        try:
            response_unduh_persil_par_sdo = endpoints.unduh_persil_par_sdo(
                jenis_hak= jenis_hak,
                no_sertipikat= self._txt_nomor,
                wilayah_id= wilayah_id,
                kantor_id= self._kantor_id,
                username= username,
                srs_name= self._srid_code,
                start= self._start,
                limit= self._limit,
                count= self._count
                )

            self._upr = json.loads(response_unduh_persil_par_sdo.content)
            print(self._upr)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "GeoKKP", f"Error access webservice: {str(e)}")
            return

        if not self._upr["status"]:
            msg = self._upr["message"]
            QtWidgets.QMessageBox.critical(self, "GeoKKP", f"Error: {msg}")
            return

        if self._count == -1:
            self._count = self._upr["total"]
        
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

        self.dgv_inbox.clear()
        self.dgv_inbox.setRowCount(0)
        self.dgv_inbox.setColumnCount(0)

        if self._upr["persils"]:
            _upr_persil = {k:v for (k,v) in self._upr.items() if k == "persils"}
            _upr_dset = Dataset(json.dumps(_upr_persil))
            _upr_dset.render_to_qtable_widget("persils", self.dgv_inbox, [0,1,5,6,7,8,9,10,13,14])
            # TODO: set header labels for column 2 3 4
        else:
            print("No Persil")

    def _refresh_grid_proyek(self):
        program_id = self.cmb_program.currentData()
        print("program_id :",program_id)
        nomor_tanda_terima = self.txt_no_gugus.text()
        tahun_tanda_terima = str(self.txt_tahun_gugus.text())

        dset = {}
        try:
            response = endpoints.get_tanda_terima_ptsl_pm(
                kantor_id= self._kantor_id,
                nomor= nomor_tanda_terima,
                tahun= tahun_tanda_terima,
                program_id= program_id,
                wilayah_id= "",
            )
            dset = Dataset(response.content)
            dset_json2 = json.loads(response.content)
            print(dset)
            print(dset_json2)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "GeoKKP", f"Error access webservice: {str(e)}")
            return
        self._upr = {}

        dset_json = dset.to_json()
        if dset_json["Error"]:
            print("error:",dset_json["Error"])
            msg = str(dset_json["Error"][0])
            QtWidgets.QMessageBox.critical(self, "GeoKKP", f"Error: {msg}")
            return

        self.dgv_inbox.clear()
        self.dgv_inbox.setRowCount(0)
        self.dgv_inbox.setColumnCount(0)
        
        dset.render_to_qtable_widget(
            "TANDATERIMA",
            self.dgv_inbox,
            [0,1,2,6,8]
            )
        # TODO: set header labels for column 3 4 5 7
        
        self.btn_next.setEnabled(False)
        self.btn_prev.setEnabled(False)

    def _btn_unduh_clicked(self):   
        if self._tipe_partisipatif == "ptsl":
            self._unduh_persil_par_ptsl()

        if self._upr and self._upr["status"]:
            self._draw(self._upr)


    def _unduh_persil_par_ptsl(self):
        if not len(self.dgv_inbox.selectedItems()) > 0 :
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Silakan melakukan query terlebih dahulu"
            )
            return

        for i in [0,1,2,6,8]:
            self.dgv_inbox.setColumnHidden(i,False)
        selected_item = self.dgv_inbox.selectedItems()
        for i in [0,1,2,6,8]:
            self.dgv_inbox.setColumnHidden(i,True)
        print(selected_item)

        gugus_partisipatif_id = selected_item[2].text()
        nomor_tanda_terima = selected_item[3].text()
        notts = nomor_tanda_terima.split("/")
        self.txt_no_gugus.setText(notts[0])
        self.txt_tahun_gugus.setText(notts[1])
        username = app_state.get("username").value
        
        print("gugus id:",gugus_partisipatif_id)

        try:
            response_unduh_ptsl = endpoints.unduh_persil_par_ptsl_sdo(
                gugus_id= gugus_partisipatif_id,
                kantor_id= self._kantor_id,
                username= username,
                srs_name= self._srid_code,
            )
            self._upr = json.loads(response_unduh_ptsl.content)
            print(self._upr)


        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "GeoKKP", f"Error access webservice: {str(e)}")
            return
    
    def _draw(self, upr):
        if upr["status"]:
            for p in upr["persils"]:
                key = p["key"]
                tipe = p["type"]
                label = p["nomor"]
                obj_bidang = []

            epsg = get_project_crs
            if upr["persils"] and upr["persils"][0]["boundary"]:
                layer_config = get_layer_config("020100")
                layer = sdo_to_layer(
                    upr["persils"],
                    name=layer_config["Nama Layer"],
                    symbol=layer_config["Style Path"],
                    crs=epsg,
                    coords_field="boundary",
                )

                # set label to fieldName "nomor"
                settings = QgsPalLayerSettings()
                settings.fieldName = "nomor"
                labeling = QgsVectorLayerSimpleLabeling(settings)
                layer.setLabeling(labeling)
                layer.triggerRepaint()


            if upr["garis"]:
                layer_config = get_layer_config("020200")
                layer = sdo_to_layer(
                    upr["garis"],
                    name=layer_config["Nama Layer"],
                    symbol=layer_config["Style Path"],
                    crs=epsg,
                    coords_field="line",
                )
            
                # NOTE: will deprecate it in the future
                # TODO: refactoring layer type
            

            iface.actionZoomToLayer().trigger()
        else:
            if upr["message"]:
                msg = upr["message"]
                QtWidgets.QMessageBox.critical(
                    None, "GeoKKP", "Gagal menggambar layer : "+msg
                )
                return
        
    def _btn_validasi_click(self):
        if not len(self.dgv_inbox.selectedItems()) > 0 :
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Silakan melakukan query terlebih dahulu"
            )
            return
        
        self._validate_layers = select_layer_by_regex(r"^\(020100\)*")
        if not self._validate_layers:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Layer batas bidang tanah (020100) tidak bisa ditemukan"
            )
            return

        self._start_berkas()
    
    def _start_berkas(self):
        selected_item = []
        print(self.dgv_inbox.horizontalHeaderItem(2).text())
        if self.dgv_inbox.horizontalHeaderItem(2).text() == "nomor":
        # if self.dgv_inbox.horizontalHeaderItem(0) == "NoHak":
            # perorangan
            for i in [0,1,5,6,7,8,9,10,13,14]:
                self.dgv_inbox.setColumnHidden(i,False)
            selected_item = self.dgv_inbox.selectedItems()
            for i in [0,1,5,6,7,8,9,10,13,14]:
                self.dgv_inbox.setColumnHidden(i,True) 
            print("perorangan :",selected_item)

            self._persil_par_id = selected_item[0].text()
            no_hak = selected_item[2].text()
            folder_id = selected_item[10].text()
            desa = selected_item[3].text()
            luas_entri = selected_item[4].text()

            QtWidgets.QMessageBox.information(
                None, "GeoKKP", "belum diimplementasikan"
            )
            return
            # TODO: impelement form valid partisipatory
        
        else:
            # ptsl
            for i in [0,1,2,6,8]:
                self.dgv_inbox.setColumnHidden(i,False)
            selected_item = self.dgv_inbox.selectedItems()
            for i in [0,1,2,6,8]:
                self.dgv_inbox.setColumnHidden(i,True)
            print("PTSL :",selected_item)
            
            tanda_terima_ptsl_id = selected_item[0].text()
            wilayah_id = selected_item[1].text()
            gugus_id = selected_item[2].text()
            no_tanda_terima = selected_item[3].text()
            jml_bidang = selected_item[4].text()
            desa = selected_item[5].text()
            tipe = selected_item[7].text()
            kecamatan = selected_item[8].text()

            cek_no_tanda_terima = f"{self.txt_no_gugus.text()}/{self.txt_tahun_gugus.text()}"
            if no_tanda_terima != cek_no_tanda_terima:
                QtWidgets.QMessageBox.warning(
                    None, "GeoKKP", "Masukkan Nomor dan Tahun Tanda Terima yang akan divalidasi, kemudian klik Cari!"
                )
                return

            if not self._upr:
                QtWidgets.QMessageBox.warning(
                    None, "GeoKKP", "Unduh dulu Tanda Terima yang akan divalidasi!"
                )
                return
            
            if tipe != "GUK":
                QtWidgets.QMessageBox.warning(
                    None, "GeoKKP", "Hanya Gambar Ukur yang dapat dilanjutkan menjadi PBT!"
                )
                return
            
            create_pbt_partisipatif = CreatePBTPartisipatif(
                self._upr,
                tanda_terima_ptsl_id,
                wilayah_id,
                gugus_id,
                no_tanda_terima,
                desa,
                kecamatan,
                jml_bidang,
                self
            )
            create_pbt_partisipatif.show()
            create_pbt_partisipatif.DialogResult.connect(self._refresh_grid_proyek)