from asyncio.windows_events import NULL
from contextlib import nullcontext
import imp
import os
import json
import re

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface
from qgis.core import QgsRectangle
from ...api import endpoints
from ...utils import readSetting, get_epsg_from_tm3_zone, get_layer_config, sdo_to_layer
from ...models.dataset import Dataset
from ...download_persil_sekitarnya import DownloadPersilSekitar

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../../ui/workpanel/tab_unduh_persil.ui")
)


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class TabUnduhPersil(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabUnduhPersil, self).__init__(parent)
        self.setupUi(self)

        self.srid_code = [
            23830, 23831, 23832, 23833, 23834, 23835, 23836, 23837, 23838, 23839, 23840, 23841, 23842, 23843, 23844, 23845
        ]
        self._upr = {}

        self._start = 0
        self._limit = 20
        self._count = -1

        self._txt_nomor = ""
        self._wilayah_id = ""
        self._srid_code = ""
        self._ext = QgsRectangle(0, 0, 50, 50)
        self._init_ext = True

        self._kantor_id = ""
        self._tipe_kantor_id = ""

        self.toolbar_inbox.setEnabled(True)
        self.cmb_propinsi.currentIndexChanged.connect(self._cmb_propinsi_selected_index_changed)
        self.cmb_kabupaten.currentIndexChanged.connect(self._cmb_kabupaten_selected_index_changed)
        self.cmb_kecamatan.currentIndexChanged.connect(self._cmb_kecamatan_selected_index_changed)
        self.btn_cari.clicked.connect(self._btn_cari_click)
        self.btn_start_process.clicked.connect(self._handle_download_hasil_query)
        self.btn_first.clicked.connect(self._btn_first_click)
        self.btn_prev.clicked.connect(self._btn_prev_click)
        self.btn_next.clicked.connect(self._btn_next_click)
        self.btn_last.clicked.connect(self._btn_last_click)
        self.btn_next_record.clicked.connect(self._btn_next_record_click)
        self.btn_download_all.clicked.connect(self.DownloadAll)
        self.chb_per_kabupaten.stateChanged.connect(self._chb_per_kabupaten_state_changed)
        self.btn_download_rectangle.clicked.connect(self.DownloadRadius)

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

        self.cmb_coordinate_system.setCurrentIndex(7)

        # TODO: refactor configFile

    def _cmb_propinsi_selected_index_changed(self, index):
        self._set_cmb_kabupaten()

    def _cmb_kabupaten_selected_index_changed(self, index):
        self._set_cmb_kecamatan()

    def _cmb_kecamatan_selected_index_changed(self, index):
        self._set_cmb_desa()

    def _set_cmb_propinsi(self):
        response = endpoints.get_provinsi_by_kantor(self._kantor_id, self._tipe_kantor_id)
        prop_dataset = json.loads(response.content)

        self.cmb_propinsi.clear()
        for prop in prop_dataset["PROPINSI"]:
            self.cmb_propinsi.addItem(prop["PROPNAMA"], prop["PROPINSIID"])

    def _set_cmb_kabupaten(self):
        selected_prov = self.cmb_propinsi.currentData()
        response = endpoints.get_kabupaten_by_kantor(self._kantor_id, self._tipe_kantor_id, selected_prov)
        kabu_dataset = json.loads(response.content)
      
        self.cmb_kabupaten.clear()
        for kab in kabu_dataset["KABUPATEN"]:
            self.cmb_kabupaten.addItem(kab["KABUNAMA"], kab["KABUPATENID"])

    def _set_cmb_kecamatan(self):
        selected_kab = self.cmb_kabupaten.currentData()
        response = endpoints.get_kecamatan_by_kantor(self._kantor_id, self._tipe_kantor_id, selected_kab)
        keca_dataset = json.loads(response.content)

        self.cmb_kecamatan.clear()
        for kec in keca_dataset["KECAMATAN"]:
            self.cmb_kecamatan.addItem(kec["KECANAMA"], kec["KECAMATANID"])

    def _set_cmb_desa(self):
        selected_kec = self.cmb_kecamatan.currentData()
        response = endpoints.get_desa_by_kantor(self._kantor_id, self._tipe_kantor_id, selected_kec)
        desa_dataset = json.loads(response.content)

        self.cmb_desa.clear()
        for des in desa_dataset["DESA"]:
            self.cmb_desa.addItem(des["DESANAMA"], des["DESAID"])

    def _btn_cari_click(self):
        print("triggered")
        self.toolbar_inbox.setDisabled(True)
        self.btn_cari.setDisabled(True)
        self.chb_per_kabupaten.setDisabled(True)
        self.cmb_coordinate_system.setDisabled(True)
        self.cmb_kecamatan.setDisabled(True)
        self.cmb_desa.setDisabled(True)

        self._start = 0
        self._count = -1
        self._txt_nomor = self.txt_nomor.text()

        self.btn_first.setDisabled(False)
        self.btn_last.setDisabled(False)

        self._refresh_grid()

        self.toolbar_inbox.setDisabled(False)
        self.btn_cari.setDisabled(False)
        self.chb_per_kabupaten.setDisabled(False)
        self.cmb_coordinate_system.setDisabled(False)
        self.cmb_kecamatan.setDisabled(False)
        self.cmb_desa.setDisabled(False)

    def _refresh_grid(self):
        str_pattern = r"^([0-9]{1,5}|[0-9]{1,5}-[0-9]{1,5})((,([0-9]{1,5}|[0-9]{1,5}-[0-9]{1,5}))?)*$"
        print("triggered2")

        txt_nomor = self.txt_nomor.text()
        if txt_nomor:
            if not re.match(str_pattern, txt_nomor):
                QtWidgets.QMessageBox.critical(
                    None, "GeoKKP", "Penulisan Nomor Bidang Salah"
                )
                return

        wilayah_id = ""
        if self.chb_per_kabupaten.isChecked():
            wilayah_id = self.cmb_kabupaten.currentData()
        else:
            wilayah_id = self.cmb_desa.currentData()

        try:
            crs = self.cmb_coordinate_system.currentText()
            zone = crs.replace("TM3-", "")
            srs_name = get_epsg_from_tm3_zone(zone, include_epsg_key=False)
            response = endpoints.unduh_persil_sdo(wilayah_id, self._txt_nomor, srs_name, str(
                self._start), str(self._limit), str(self._count))
            self._upr = json.loads(response.content)
            
   
            if not self._upr["status"]:
                QtWidgets.QMessageBox.warning(
                    None, "GeoKKP", self._upr["message"]
                )
                return

            if self._count == -1:
                self._count = int(self._upr["total"])

            if self._count > 0:
                if self._start + self._limit >= self._count:
                    page = f"{self._start + 1} - {self._count} dari {self._count}"
                    self.txt_paging.setText(page)
                    self.btn_next.setDisabled(True)
                    self.btn_next_record.setDisabled(True)
                else:
                    page = f"{self._start + 1} - {self._start + self._limit} dari {self._count}"
                    self.txt_paging.setText(page)
                    self.btn_next.setDisabled(False)
                    self.btn_next_record.setDisabled(False)
            else:
                self.txt_paging.setText("0")
                self.btn_next.setDisabled(True)
                self.btn_prev.setDisabled(True)
                self.btn_next_record.setDisabled(True)

            if self._start == 0 or self._count == 0:
                self.btn_prev.setDisabled(True)
            else:
                self.btn_prev.setDisabled(False)

            dataset = Dataset()
            table = dataset.add_table("PERSIL")
            table.add_column("Key")
            table.add_column("Type")
            table.add_column("NIB")
            table.add_column("NamaDesa")
            table.add_column("LuasTertulis")
            table.add_column("Height")
            table.add_column("Rotation")
            table.add_column("Label")
            table.add_column("RowNums")

            for p in self._upr["persils"]:
                d_row = table.new_row()
                d_row["Key"] = p["key"]
                d_row["Type"] = p["type"]
                d_row["NIB"] = p["nomor"]
                d_row["Label"] = p["label"]
                d_row["NamaDesa"] = p["namaDesa"]
                d_row["LuasTertulis"] = p["luasTertulis"]
                d_row["Height"] = p["height"]
                d_row["Rotation"] = p["rotation"]
                d_row["RowNums"] = p["rowNums"]

            dataset.render_to_qtable_widget(
                "PERSIL",
                self.dgv_persil,
                [0, 1, 5, 6, 8]
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "GeoKKP", str(e)
            )
            return

    def _handle_download_hasil_query(self):
        if not self._upr or not self._upr["status"]:
            QtWidgets.QMessageBox.critical(
                self, "GeoKKP", "Silakan melakukan query terlebih dahulu"
            )
        else :
            self.toolbar_inbox.setDisabled(True)
            self.btn_cari.setDisabled(True)
            self.chb_per_kabupaten.setDisabled(True)
            self.cmb_coordinate_system.setDisabled(True)
            self.cmb_kecamatan.setDisabled(True)
            self.cmb_desa.setDisabled(True)

            self._draw(self._upr)

            self.toolbar_inbox.setDisabled(False)
            self.btn_cari.setDisabled(False)
            self.chb_per_kabupaten.setDisabled(False)
            self.cmb_coordinate_system.setDisabled(False)
            self.cmb_kecamatan.setDisabled(False)
            self.cmb_desa.setDisabled(False)

    def _draw(self, upr):
        # print(upr)
        crs = self.cmb_coordinate_system.currentText()
        zone = crs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)

        if upr["persils"]:
            print(upr["persils"][0])

            if upr["persils"]:
                layer_config = get_layer_config("020100")
                print(layer_config)
                layer = sdo_to_layer(
                    upr["persils"],
                    name=layer_config["Nama Layer"],
                    symbol=layer_config["Style Path"],
                    crs=epsg,
                    coords_field="boundary",
                )
                # NOTE: will deprecate it in the future
                # self.current_layers.append(layer)

    def _btn_first_click(self):
        self._start = 0
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.btn_next_record.setEnabled(True)
        self._refresh_grid()

    def _btn_prev_click(self):
        self._start -= self._limit
        if (self._start <= 0):
            self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.btn_next_record.setEnabled(True)
        self._refresh_grid()

    def _btn_next_click(self):
        self._start += self._limit
        if (self._start + self._limit >= self._count):
            self.btn_next.setEnabled(False)
            self.btn_next_record.setEnabled(False)
        self.btn_prev.setEnabled(True)
        self._refresh_grid()

    def _btn_last_click(self):
        self._start = self._count // self._limit * self._limit
        print(self._start)
        if (self._start >= self._count):
            self._start -= self._limit
            self.btn_prev.setEnabled(False)
        else :
            self.btn_prev.setEnabled(True)
        self.btn_next.setEnabled(False)
        self.btn_next_record.setEnabled(False)
        self._refresh_grid()

    def _btn_next_record_click(self):
        self.toolbar_inbox.setEnabled(False)
        self._start += self._limit
        if (self._start + self._limit >= self._count):
            self.btn_next.setEnabled(False)
            self.btn_next_record.setEnabled(False)
        self.btn_prev.setEnabled(True)
        self._refresh_grid()
        self.toolbar_inbox.setEnabled(True)

    def _chb_per_kabupaten_state_changed(self):
        if (self.chb_per_kabupaten.isChecked()):
            self.cmb_desa.setVisible(False)
            self.cmb_kecamatan.setVisible(False)
            self.lbl_wilayah.setVisible(False)
            self.lbl_wilayah_induk.setVisible(False)
        else :
            self.cmb_desa.setVisible(True)
            self.cmb_kecamatan.setVisible(True)
            self.lbl_wilayah.setVisible(True)
            self.lbl_wilayah_induk.setVisible(True)

    def DownloadAll(self):

        try:

            self.toolbar_inbox.setEnabled(False)
            self.btn_cari.setEnabled(False)
            self.chb_per_kabupaten.setEnabled(False)
            self.cmb_coordinate_system.setEnabled(False)
            self.cmb_kecamatan.setEnabled(False)
            self.cmb_desa.setEnabled(False)

            if self.chb_per_kabupaten.isChecked():
                self._wilayah_id = self.cmb_kabupaten.currentData()
            else:
                self._wilayah_id = self.cmb_desa.currentData()

            crs = self.cmb_coordinate_system.currentText()
            zone = crs.replace("TM3-", "")
            self._srid_code = get_epsg_from_tm3_zone(zone, include_epsg_key=False)

            self._count = -1
            self._start = 0

            response = endpoints.unduh_persil_sdo(self._wilayah_id,"",self._srid_code,str(self._start),"20",str(self._count))
            upr = json.loads(response.content)

            self._count = int(upr["total"])

            response = endpoints.unduh_persil_sdo(self._wilayah_id,"",self._srid_code,str(self._start),str(self._count),str(self._count))
            upr = json.loads(response.content)
            self.UpdateStatus(upr, "Mengunduh " + str(self._start + 1) + " - " + str(self._count+self._start) +" dari " + str(self._count) + " persil")

            upr = None

            self.UpdateStatus(upr,"Mengunduh Selesai")

        except Exception as e:
            print(e)


    def UpdateStatus(self,_upr,value):
        print(_upr)
        if(value.startswith("Mengunduh")):
            if(_upr != None):
                self._draw(_upr)
            if(value != "Mengunduh Selesai"):
                print(value)
                self.toolbar_inbox.setEnabled(False)
                self.btn_cari.setEnabled(False)
                self.chb_per_kabupaten.setEnabled(False)
                self.cmb_coordinate_system.setEnabled(False)
                self.cmb_kecamatan.setEnabled(False)
                self.cmb_desa.setEnabled(False)
            else:
                self.toolbar_inbox.setEnabled(True)
                self.btn_cari.setEnabled(True)
                self.chb_per_kabupaten.setEnabled(True)
                self.cmb_coordinate_system.setEnabled(True)
                self.cmb_kecamatan.setEnabled(True)
                self.cmb_desa.setEnabled(True)
        else:
            self.toolbar_inbox.setEnabled(True)
            self.btn_cari.setEnabled(True)
            self.chb_per_kabupaten.setEnabled(True)
            self.cmb_coordinate_system.setEnabled(True)
            self.cmb_kecamatan.setEnabled(True)
            self.cmb_desa.setEnabled(True)

    def DownloadRadius(self):
        downloadPersil = DownloadPersilSekitar()
        downloadPersil.show()
