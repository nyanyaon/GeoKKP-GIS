# from asyncio.windows_events import NULL
from math import fabs
import os
import json
import re
from urllib import response

from qgis.PyQt import QtWidgets, uic

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from ...utils import (
    readSetting,
    get_project_crs,
    sdo_to_layer,
    get_layer_config,
    add_layer,
    select_layer_by_regex
)

from ...utils import readSetting
from ...api import endpoints
from ...models.dataset import Dataset
from ...memo import app_state
from ...topology import quick_check_topology
from ...desain_gambar_denah import DesainGambarDenah
from ...FmImportGambarDenah import FmImportGambarDenah
from datetime import datetime
from ...layout_create import CreateLayoutDialog

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../../ui/workpanel/tab_gambar_denah.ui")
)


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class TabGambarDenah(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabGambarDenah, self).__init__(parent)
        self.setupUi(self)

        self._limit = 20
        self._start = 0
        self._count = -1

        self._current_layers = []
        self._importGambarDenah = True
        
        self.cmb_propinsi.currentIndexChanged.connect(
            self._cmb_propinsi_selected_index_changed
        )
        self.cmb_kabupaten.currentIndexChanged.connect(
            self._cmb_kabupaten_selected_index_changed
        )
        self.cmb_kecamatan.currentIndexChanged.connect(
            self._cmb_kecamatan_selected_index_changed
        )

        self.btn_cari.clicked.connect(self.btnCari_Click)
        self.btn_mulai.clicked.connect(self.prepareBerkas)
        self.btn_simpan.clicked.connect(self.Submit)
        self.btn_tutup.clicked.connect(self.StopProcess)
        self.btn_next.clicked.connect(self.btnNext_click)
        self.btn_prev.clicked.connect(self.btnPrev_click)
        self.btn_first.clicked.connect(self.btnFirst_click)
        self.btn_last.clicked.connect(self.btnLast_click)

        self.btn_layout.clicked.connect(self.create_layout)
        self.btn_informasi.setEnabled(False)
        self.btn_layout.setEnabled(False)
        self.btn_tutup.setEnabled(False)

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

        

    def btnCari_Click(self):
        self._start = 0
        self._count = -1
        self._txtNomor = self.txt_nomor.text()
        self._txtTahun = self.txt_tahun.text()

        self.btn_first.setEnabled(True)
        self.btn_last.setEnabled(True)

        self.refresh_grid()

    def refresh_grid(self):
        str_pattern = r"^([0-9]{1,5}|[0-9]{1,5}-[0-9]{1,5})((,([0-9]{1,5}|[0-9]{1,5}-[0-9]{1,5}))?)*$"
        
        txt_nomor = self.txt_nomor.text()
        if txt_nomor:
            if not re.match(str_pattern, txt_nomor):
                QtWidgets.QMessageBox.critical(
                    None, "GeoKKP", "Penulisan Nomor Gambar Denah Salah"
                )
                return

        str_pattern = r"^[0-9]{4}$";
        txt_tahun = self.txt_nomor.text()
        if txt_tahun:
            if not re.match(str_pattern, txt_tahun):
                QtWidgets.QMessageBox.critical(
                    None, "GeoKKP", "Penulisan Tahun Gambar Denah Salah"
                )
                return
        
        wilayah_id = self.cmb_desa.currentData()
        response = endpoints.getGambarDenah(
            wilayah_id,
            self._kantor_id,
            self._txtNomor,
            self._txtTahun,
            str(self._start),
            "20",
            str(self._count))

        self.dSet = json.loads(response.content)

        

        dataset = Dataset()
        table = dataset.add_table("GAMBARDENAH")
        table.add_column("DokumenId")
        table.add_column("WilayahId")
        table.add_column("Desa")
        table.add_column("Tipe")
        table.add_column("Nomor")
        table.add_column("Sejak")
        table.add_column("Sampai")
        table.add_column("Rownums")

        for p in self.dSet["GAMBARDENAH"]:
            d_row = table.new_row()
            d_row["DokumenId"] = p["DOKUMENPENGUKURANID"]
            d_row["WilayahId"] = p["WILAYAHID"]
            d_row["Desa"] = p["DESA"]
            d_row["Tipe"] = p["TIPEDOKUMENID"]
            d_row["Nomor"] = p["NOMOR"]
            if(p["VALIDSEJAK"] == None):
                d_row["Sejak"] = ""
            else:
                d_row["Sejak"] = datetime.fromisoformat(p["VALIDSEJAK"])
            if(p["VALIDSAMPAI"] == None):
                d_row["Sampai"] = ""
            else:
                d_row["Sampai"] = datetime.fromisoformat(p["VALIDSAMPAI"])
            d_row["Rownums"] = p["ROWNUMS"]

        if(self._count == -1):
            self._count = int(self.dSet["jumlahtotal"][0]["COUNT(1)"])

        dataset.render_to_qtable_widget("GAMBARDENAH", self.dgv_GambarDenah,[0,1,2,7])
    
        if (self._count > 0 ):
            print(self._start,self._count,self._limit)
            if(self._start + self._limit >= self._count):
                self.txt_paging.setText(str(self._start)+" - " + str(self._count) + " dari " + str(self._count))
                self.btn_next.setEnabled(False)
            else:
                self.txt_paging.setText(str(self._start)+" - " + str(self._limit + self._start) + " dari " + str(self._count))
                self.btn_next.setEnabled(True)
        else:
            self.txt_paging.setText("0")
            self.btn_next.setEnabled(False)
            self.btn_prev.setEnabled(False)

        if(self._start == 0 or self._count == 0):
            self.btn_prev.setEnabled(False)
        else:
            self.btn_prev.setEnabled(True)

    def prepareBerkas(self):
        self.dgv_GambarDenah.setColumnHidden(0, False)
        item = self.dgv_GambarDenah.selectedItems()
        self.dgv_GambarDenah.setColumnHidden(0, True)
        
        if(item == []):
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih Sebuah Gambar Denah Yang Akan Diproses"
            )
            return

        row = item[0].row()
        dataSelect = []
        self.dgv_GambarDenah.setColumnHidden(0, False)
        for x in range(self.dgv_GambarDenah.columnCount()):
            dataSelect.append(self.dgv_GambarDenah.item(row,x).text())
        self.dgv_GambarDenah.setColumnHidden(0, True)

        username_state = app_state.get("username", "")
        username = username_state.value

        

        dokumenPengukuranId = dataSelect[0]
        response = endpoints.startBerkasSpasialByDokumenPengukuranId(dokumenPengukuranId,self._kantor_id,username)
        self._bs = json.loads(response.content)

        print(self._bs,username)
        
        # if self._bs['valid'] == False:
        #     QtWidgets.QMessageBox.warning(
        #         None, "GeoKKP", self._bs['errorStack'][0]
        #     )
        #     return
        
        

        if(self._bs != None and self._bs["valid"]):
            self._importGambarDenah = False
            self.btn_mulai.setEnabled(False)
            self.btn_informasi.setEnabled(True)
            self.btn_layout.setEnabled(True)
            self.btn_tutup.setEnabled(True)
            self.txt_nomor.setEnabled(False)
            self.txt_tahun.setEnabled(False)
            self.btn_cari.setEnabled(False)
            if(self._bs["newGugusId"]!=""):
                self._load_berkas_spasial(self._bs["newGugusId"],riwayat=False)
            self.txt_nomor.setText(item[4].text())
   
            self.txt_nomor.setEnabled(False)
            self.txt_tahun.setEnabled(False)
            self.btn_cari.setEnabled(False)
            self.btn_mulai.setEnabled(False)

            self.btn_informasi.setEnabled(True)
            self.btn_layout.setEnabled(True)
            self.btn_tutup.setEnabled(True)

            self.cmb_propinsi.setEnabled(False)
            self.cmb_kabupaten.setEnabled(False)
            self.cmb_kecamatan.setEnabled(False)
            self.cmb_desa.setEnabled(False)
        else:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", self._bs['errorStack'][0]
            )
            return 

    def _load_berkas_spasial(self, gugus_ids, riwayat=False):
        response_spatial_sdo = endpoints.get_spatial_document_sdo([gugus_ids],riwayat)
        response_spatial_sdo_json = json.loads(response_spatial_sdo.content)
        print(response_spatial_sdo_json)

        if not response_spatial_sdo_json["status"]:
            QtWidgets.QMessageBox.critical(None, "Error", "Proses Unduh Geometri gagal")
            return

        epsg = get_project_crs()
        layer_config = get_layer_config("020110")

        if response_spatial_sdo_json["geoKkpPolygons"]:
            layer = sdo_to_layer(
                response_spatial_sdo_json["geoKkpPolygons"],
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )
        else:
            layer = add_layer(
                layer_config["Nama Layer"],
                layer_config["Tipe Layer"],
                layer_config["Style Path"],
                layer_config["Attributes"][0],
            )

        iface.actionZoomToLayer().trigger()

    def Submit(self):
        # replacing_current_layers
        self._current_layers = select_layer_by_regex(r"^\(020110\)*")
        if not self._current_layers:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Layer Apartemen (020110) tidak bisa ditemukan"
            )
            return

        topo_error_message = []

        self.desa = {
            "provinsi":[self.cmb_propinsi.currentText(),self.cmb_propinsi.currentData()],
            "kabupaten":[self.cmb_kabupaten.currentText(),self.cmb_kabupaten.currentData()],
            "kecamatan":[self.cmb_kecamatan.currentText(),self.cmb_kecamatan.currentData()],
            "desa":[self.cmb_desa.currentText(),self.cmb_desa.currentData()]      
        }

        for layer in self._current_layers:
            try:
                valid, num = quick_check_topology(layer)
                print(valid, num)
                if not valid:
                    message = f"Ada {num} topology error di layer {layer.name()}"
                    topo_error_message.append(message)
            except RuntimeError:
                continue

        if topo_error_message:
            QtWidgets.QMessageBox.warning(
                None, "Perhatian", "\n".join(topo_error_message)
            )
            return

        if(self._importGambarDenah):
            self.desainDenah =  FmImportGambarDenah()
            self.desainDenah.setupFmMin()
        else:
            self.desainDenah = FmImportGambarDenah()
            self.desainDenah.setupFm(
                self._bs["nomorBerkas"],
                self._bs["tahunBerkas"],
                [self._bs["gambarUkurs"]],
                self._bs["wilayahId"],
                self._bs["newGugusId"],
                self._bs["newParcelNumber"],
                self._bs["newApartmentNumber"],
                [self._bs["newParcels"]],
                [self._bs["oldParcels"]],
                [self._bs["newApartments"]],
                [self._bs["oldApartments"]],
                self._bs["gantiDesa"],
                self.desa
                )

    
    def ImportGambarDenahCall(self):
        pass

    def btnFirst_click(self):
        self._start = 0
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.refresh_grid()

    def btnPrev_click(self):
        self._start -= self._limit 
        if(self._start <= 0):
            self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.refresh_grid()

    def btnNext_click(self):
        self._start += self._limit
        if(self._start + self._limit >= self._count):
            self.btn_next.setEnabled(False)
        self.btn_prev.setEnabled(True)
        self.refresh_grid()

    def btnLast_click(self):
        self._start = self._count // self._limit * self._limit
        if self._start >= self._count:
            self._start -= self._limit
            self.btn_prev.setEnabled(False)
        else:
            self.btn_prev.setEnabled(True)
        self.btn_next.setEnabled(False)
        self.refresh_grid()

    def StopProcess(self):
        response = endpoints.stop_berkas(self._bs['nomorBerkas'],self._bs["tahunBerkas"],self._kantor_id)
        self._bs = None
        self._importGambarDenah = True

        if(json.loads(response.content) is False):
            QtWidgets.QMessageBox.information(
                None,
                "GeoKKP Web",
                "Berkas gagal di stop",
            )
            return

        self.btn_informasi.setEnabled(False)
        self.btn_layout.setEnabled(False)
        self.btn_tutup.setEnabled(False)
        self.txt_nomor.setEnabled(True)
        self.txt_tahun.setEnabled(True)
        self.btn_cari.setEnabled(True)
        self.btn_mulai.setEnabled(True)

        self.cmb_propinsi.setEnabled(True)
        self.cmb_kabupaten.setEnabled(True)
        self.cmb_kecamatan.setEnabled(True)
        self.cmb_desa.setEnabled(True)

        QtWidgets.QMessageBox.information(
                None,
                "GeoKKP Web",
                "Berkas berhasil di stop",
        )

    def create_layout(self):
        # TODO send variable to layout
        create_layout = CreateLayoutDialog()
        create_layout.show()