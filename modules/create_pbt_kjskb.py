from asyncio.windows_events import NULL
import os
import json
import hashlib
from urllib import response

from qgis.PyQt import QtWidgets, uic, QtGui
from qgis.core import QgsProject, QgsWkbTypes, QgsVectorLayer, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/create_pbt_kjskb.ui")
)

from .utils import readSetting, storeSetting
from .utils.geometry import get_sdo_point, get_sdo_polygon
from .api import endpoints
from .memo import app_state
from .models.dataset import Dataset, DataTable

from datetime import date


class CreatePBTKJSKB(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Create Peta Bidang Tanah KJSKB"""

    closingPlugin = pyqtSignal()
    DialogResult = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(CreatePBTKJSKB, self).__init__(parent)
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

        self.btn_tutup.clicked.connect(self.close)
        self.cmb_program.currentIndexChanged.connect(self._cmb_program_index_changed)
        self.cmb_surveyor.currentIndexChanged.connect(self._cmb_surveyor_index_changed)
        self.btn_cari.clicked.connect(self._btn_cari_clicked)

        self.btn_tolak.clicked.connect(self._btn_tolak_clicked)
        self.btn_batal.clicked.connect(self._btn_batal_clicked)
        self.cbx_layer.stateChanged.connect(self._cbx_layer_checkedchange)
        self.cbx_topologi.stateChanged.connect(self._cbx_topologi_checkedchange)
        self.cbx_diluar_wilayah.stateChanged.connect(self._cbx_diluar_wilayah_checkedchange)
        self.cbx_tidak_lengkap.stateChanged.connect(self._cbx_tidak_lengkap_checkedchange)
        self.cbx_overlap.stateChanged.connect(self._cbx_overlap_checkedchange)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setup_workpanel(self):

        self._ds_program = Dataset
        self._desa_id = ""
        self._program_id = ""
        self._surveyor_id = ""
        self._tandaterima_id = ""

        kantor = readSetting("kantorterpilih", {})
        if not kantor:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih lokasi kantor lebih dahulu"
            )
            self.close()
            return

        self._kantor_id = kantor["kantorID"]
        self._tipe_kantor_id = str(kantor["tipeKantorId"])

        response = endpoints.get_wilayah_ptsl_skb(self._kantor_id)
        self._ds_program = Dataset(response.content)
        response_json = json.loads(response.content)

        print(response_json)

        dt_program = DataTable()
        dt_program.add_column("PROGRAMID")
        dt_program.add_column("PROYEK")

        self.cmb_program.clear()
        for dr in self._ds_program["PROGRAM"].rows:
            program_id = dr["PROGRAMID"]
            proyek = dr["PROYEK"]

            drs = self._select_row(dt_program, "PROGRAMID", program_id)

            if not drs:
                drp = dt_program.new_row()
                drp["PROGRAMID"] = program_id
                drp["PROYEK"] = proyek
        
        for row in dt_program.rows:
            self.cmb_program.addItem(row["PROYEK"], row["PROGRAMID"])
        self.cmb_program.setCurrentIndex(-1)

        tahun = str(date.today().year)
        self.txt_tahun.setText(tahun)

        self.dgv_inbox_pbt.clear()
        self.dgv_inbox_pbt.setRowCount(0)
        self.dgv_inbox_pbt.setColumnCount(0)
        

    def _cmb_program_index_changed(self):
        if self.cmb_program.currentIndex() == -1:
            self.cmb_surveyor.setCurrentIndex(-1)
        else:
            self._program_id = self.cmb_program.currentData()

            drs_surveyor = self._select_rows(self._ds_program["PROGRAM"], "PROGRAMID", self._program_id)
            print("drs_surveyor:", drs_surveyor)

            dt_surveyor = DataTable()
            dt_surveyor.add_column("SURVEYORID")
            dt_surveyor.add_column("NAMA")

            for dr in drs_surveyor:
                surveyor_id = dr["SURVEYORID"]
                nama = dr["SURVEYOR"]

                drs = self._select_row(dt_surveyor, "SURVEYORID", surveyor_id)

                if not drs:
                    drp = dt_surveyor.new_row()
                    drp["SURVEYORID"] = surveyor_id
                    drp["NAMA"] = nama
            
            self.cmb_surveyor.clear()
            for row in dt_surveyor.rows:
                print(row)
                self.cmb_surveyor.addItem(row["NAMA"], row["SURVEYORID"])
    
    def _cmb_surveyor_index_changed(self):
        if self.cmb_surveyor.currentIndex() == -1:
            self.cmb_desa.setCurrentIndex(-1)
        else:
            self._surveyor_id = self.cmb_surveyor.currentData()
            filter_drs_wil = self._select_rows(self._ds_program["PROGRAM"], "PROGRAMID", self._program_id)
            filtered = [
                f
                for f in filter_drs_wil
                if f["SURVEYORID"] == self._surveyor_id
            ]
            drs_wil = filtered

            dt_wilayah = DataTable()
            dt_wilayah.add_column("WILAYAHID")
            dt_wilayah.add_column("NAMA")

            drp = dt_wilayah.new_row()
            drp["WILAYAHID"] = "0"
            drp["NAMA"] = "*"
            
            for dr in drs_wil:
                wilayah_id = dr["WILAYAHID"]
                desa = dr["DESA"]
                
                drs = self._select_row(dt_wilayah,"WILAYAHID",wilayah_id)

                if not drs:
                    drp = dt_wilayah.new_row()
                    drp["WILAYAHID"] = wilayah_id
                    drp["NAMA"] = desa
            
            self.cmb_desa.clear()
            for row in dt_wilayah.rows:
                self.cmb_desa.addItem(row["NAMA"],row["WILAYAHID"])



    def _select_row(self, datatable, key, value):
        filtered = [
            f
            for f in datatable.rows
            if f[key] == value
        ]
        if filtered:
            return filtered[0]

    def _select_rows(self, datatable, key, value):
        filtered = [
            f
            for f in datatable.rows
            if f[key] == value
        ]
        if filtered:
            return filtered
    
    def _btn_cari_clicked(self):
        self._program_id = ""
        self._surveyor_id = ""
        self._desa_id = ""

        if self.cmb_program.currentIndex != -1:
            self._program_id = self.cmb_program.currentData()
        
        if self.cmb_surveyor.currentIndex != -1:
            self._surveyor_id = self.cmb_surveyor.currentData()
        
        if self.cmb_desa.currentIndex() < 1:
            self._desa_id = ""
        else:
            self._desa_id = self.cmb_desa.currentData()
        
        response = endpoints.get_tanda_terima_ptsl_skb(
            self._kantor_id,
            self.txt_nomor.text(),
            self.txt_tahun.text(),
            self._program_id,
            self._surveyor_id,
            self._desa_id
        )
        dset = Dataset(response.content)

        if len(dset["TANDATERIMA"].columns) > 0:
            dset.render_to_qtable_widget("TANDATERIMA",self.dgv_inbox_pbt, [0,1,2,3])
        
    def _btn_tolak_clicked(self):
        for i in [0,1,2,3]:
            self.dgv_inbox_pbt.setColumnHidden(i,False)
        selected_item = self.dgv_inbox_pbt.selectedItems()
        for i in [0,1,2,3]:
            self.dgv_inbox_pbt.setColumnHidden(i,True)
        print(selected_item)

        if (len(selected_item) > 0) and (selected_item[8].text() == "None"):
            tandaterima = selected_item[4].text()
            self.cbx_diluar_wilayah.setCheckState(False)
            self.cbx_layer.setCheckState(False)
            self.cbx_overlap.setCheckState(False)
            self.cbx_topologi.setCheckState(False)
            self.cbx_tidak_lengkap.setCheckState(False)

            self.lbl_filename.setText(tandaterima)
            self.panel.setCurrentIndex(1)
        else:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih Tanda Terima Surveyor yang akan diproses!"
            )
        
    def _btn_batal_clicked(self):
        self.panel.setCurrentIndex(0)
    
    def _cbx_layer_checkedchange(self):
        if self.cbx_layer.isChecked():
            teks = self.txt_catatan.toPlainText()
            teks += "Layer tidak standar, "
            self.txt_catatan.setText(teks)
        else:
            text = self.txt_catatan.toPlainText()
            texts = text.replace("Layer tidak standar, ","")
            self.txt_catatan.setText(texts)

    def _cbx_topologi_checkedchange(self):
        if self.cbx_topologi.isChecked():
            teks = self.txt_catatan.toPlainText()
            teks += "Topologi persil error, "
            self.txt_catatan.setText(teks)
        else:
            text = self.txt_catatan.toPlainText()
            texts = text.replace("Topologi persil error, ","")
            self.txt_catatan.setText(texts)

    def _cbx_diluar_wilayah_checkedchange(self):
        if self.cbx_diluar_wilayah.isChecked():
            teks = self.txt_catatan.toPlainText()
            teks += "Diluar batas desa, "
            self.txt_catatan.setText(teks)
        else:
            text = self.txt_catatan.toPlainText()
            texts = text.replace("Diluar batas desa, ","")
            self.txt_catatan.setText(texts)

    def _cbx_tidak_lengkap_checkedchange(self):
        if self.cbx_tidak_lengkap.isChecked():
            teks = self.txt_catatan.toPlainText()
            teks += "Gambar tidak lengkap, "
            self.txt_catatan.setText(teks)
        else:
            text = self.txt_catatan.toPlainText()
            texts = text.replace("Gambar tidak lengkap, ","")
            self.txt_catatan.setText(texts)

    def _cbx_overlap_checkedchange(self):
        if self.cbx_overlap.isChecked():
            teks = self.txt_catatan.toPlainText()
            teks += "Bidang overlap, "
            self.txt_catatan.setText(teks)
        else:
            text = self.txt_catatan.toPlainText()
            texts = text.replace("Bidang overlap, ","")
            self.txt_catatan.setText(texts)
    
    # TODO: btn proses
    # TODO: btn tolak

        
