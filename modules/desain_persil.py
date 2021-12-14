import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from .utils import (
    readSetting,
    storeSetting
)
from .api import endpoints
from .memo import app_state

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), "../ui/desain_persil.ui"))


LIHAT_DATA_PERSIL_BARU = "Persil Baru"
LIHAT_DATA_PERSIL_EDIT = "Persil Edit"
LIHAT_DATA_PERSIL_INDUK = "Persil Induk"
LIHAT_DATA_APARTEMENT_BARU = "Apartemen Baru"
LIHAT_DATA_APARTEMENT_EDIT = "Apartemen Edit"

DS_PERSIL_BARU = "PersilBaru"
DS_PERSIL_EDIT = "PersilEdit"
DS_PERSIL_INDUK = "PersilInduk"
DS_APARTEMEN_BARU = "ApartemenBaru"
DS_APARTEMEN_EDIT = "ApartemenEdit"

DS_PERSIL_BARU_COLUMNS = [
    "OID", 
    "LABEL", 
    "AREA", 
    "BOUNDARY", 
    "TEXT", 
    "KETERANGAN", 
    "HEIGHT", 
    "ORIENTATION", 
    "URUT", 
    "NOLEMBAR", 
    "KOTAK"
]
DS_PERSIL_EDIT_COLUMNS = [
    "OID", 
    "REGID", 
    "NIB", 
    "LUAST", 
    "LABEL", 
    "AREA", 
    "BOUNDARY", 
    "TEXT", 
    "KETERANGAN", 
    "HEIGHT", 
    "ORIENTATION", 
    "NOLEMBAR", 
    "KOTAK"
]
DS_PERSIL_INDUK_COLUMNS = [
    "OID", 
    "REGID",
    "NIB",
    "LUAST",
    "LABEL", 
    "AREA", 
    "BOUNDARY", 
    "TEXT", 
    "KETERANGAN", 
    "HEIGHT", 
    "ORIENTATION"
]
DS_APARTEMEN_BARU_COLUMN = [
    "OID", 
    "LABEL", 
    "AREA", 
    "BOUNDARY", 
    "TEXT", 
    "KETERANGAN", 
    "HEIGHT", 
    "ORIENTATION"
]
DS_APARTEMEN_EDIT_COLUMN = [
    "OID", 
    "REGID", 
    "NOGD", 
    "LUAST", 
    "AREA", 
    "BOUNDARY", 
    "TEXT", 
    "KETERANGAN", 
    "HEIGHT", 
    "ORIENTATION"
]

DS_COLUMN_MAP = {
    DS_PERSIL_BARU: DS_PERSIL_BARU_COLUMNS,
    DS_PERSIL_EDIT: DS_PERSIL_EDIT_COLUMNS,
    DS_PERSIL_INDUK: DS_PERSIL_INDUK_COLUMNS,
    DS_APARTEMEN_BARU: DS_APARTEMEN_BARU_COLUMN,
    DS_APARTEMEN_EDIT: DS_APARTEMEN_EDIT_COLUMN
}

class DesainPersil(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Desain Persil """

    closingPlugin = pyqtSignal()
    parcel_design_event = pyqtSignal(object)

    def __init__(self, 
                parent=iface.mainWindow(),
                nomor_berkas=None,
                tahun_berkas=None,
                kantor_id=None,
                tipe_kantor_id=None,
                tipe_berkas=None,
                gambar_ukur_id=None,
                kelurahan_id=None,
                tipe_sistem_koordinat=None,
                new_parcel_number=None,
                new_apartment_number=None,
                new_parcels=[],
                old_parcels=[],
                new_apartments=[],
                old_apartments=[],
                ganti_desa=None):
        super(DesainPersil, self).__init__(parent)
        self.setupUi(self)
        self.btn_proses.setDisabled(True)

        self._current_kantor = {}
        self._current_provinsi = {}
        self._current_kabupaten = {}
        self._current_kecamatan = {}
        self._current_kelurahan = {}
        self._provinsi_by_kantor = {}
        self._kabupaten_by_kantor = {}
        self._kecamatan_by_kantor = {}
        self._kelurahan_by_kecamatan = {}
        
        self._wilayah_prior = {}
        self._ds_parcel = {
            DS_PERSIL_BARU: [], # OID, LABEL, AREA, BOUNDARY, TEXT, KETERANGAN, HEIGHT, ORIENTATION, URUT, NOLEMBAR, KOTAK
            DS_PERSIL_EDIT: [], # OID, REGID, NIB, LUAST, LABEL, AREA, BOUNDARY, TEXT, KETERANGAN, HEIGHT, ORIENTATION, NOLEMBAR, KOTAK
            DS_PERSIL_INDUK: [], # OID, LABEL, AREA, BOUNDARY, TEXT, KETERANGAN, HEIGHT, ORIENTATION
            DS_APARTEMEN_BARU: [], # OID, LABEL, AREA, BOUNDARY, TEXT, KETERANGAN, HEIGHT, ORIENTATION
            DS_APARTEMEN_EDIT: [], # OID, REGID, NOGD, LUAST, AREA, BOUNDARY, TEXT, KETERANGAN, HEIGHT, ORIENTATION
        } # TODO: Create dedicated data structure

        self._process_parcels = False

        self._nomor_berkas = nomor_berkas
        self._tahun_berkas = tahun_berkas
        self._kantor_id = kantor_id
        self._tipe_kantor_id = tipe_kantor_id
        self._tipe_berkas = tipe_berkas
        self._gambar_ukur_id = gambar_ukur_id
        self._kelurahan_id = kelurahan_id
        self._tipe_sistem_koordinat = tipe_sistem_koordinat
        self._new_parcel_number = int(new_parcel_number)
        self._new_apartment_number = int(new_apartment_number)
        self._new_parcels = new_parcels
        self._old_parcels = old_parcels
        self._new_apartments = new_apartments
        self._old_apartments = old_apartments
        self._ganti_desa = ganti_desa

        self._get_current_settings()
        self._setup_workpanel()

        self.combo_lihat_data.currentTextChanged.connect(self._handle_lihat_data_changed)
        self.combo_provinsi.currentIndexChanged.connect(self.provinsi_changed)
        self.combo_kabupaten.currentIndexChanged.connect(self.kabupaten_changed)
        self.combo_kecamatan.currentIndexChanged.connect(self.kecamatan_changed)
        self.combo_kelurahan.currentIndexChanged.connect(self.kelurahan_changed)
        self.btn_proses.clicked.connect(self._handle_process)
        self.btn_validasi.clicked.connect(self._handle_validate)
        self.btn_batal.clicked.connect(self._handle_batal)
        self.btn_ganti_desa.clicked.connect(self._handle_ganti_desa)
        self.check_nib.stateChanged.connect(self._handle_check_nib)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
    
    def _get_current_settings(self):
        self._current_kantor = readSetting("kantorterpilih")
        self._current_provinsi = readSetting("provinsiterpilih")
        self._current_kabupaten = readSetting("kabupatenterpilih")
        self._current_kecamatan = readSetting("kecamatanterpilih")
        self._current_kelurahan = readSetting("kelurahanterpilih")
        self._provinsi_by_kantor = readSetting("provinsibykantor")
        self._kabupaten_by_provinsi = readSetting("kabupatenbyprovinsi")
        self._kecamatan_by_kabupaten = readSetting("kecamatanbykabupaten")
        self._kelurahan_by_kecamatan = readSetting("kelurahanbykecamatan")

    def _setup_workpanel(self):
        self._process_parcels = True

        self.combo_lihat_data.clear()
        if self._tipe_berkas in ["NPG", "VPG", "SPL", "UNI", "SUB", "DIV"]:
            self.combo_lihat_data.addItems([LIHAT_DATA_PERSIL_BARU, LIHAT_DATA_PERSIL_EDIT])
            self._fill_new_persil()
            if self._tipe_berkas in ["DIV", "SPL"]:
                self.combo_lihat_data.addItem(LIHAT_DATA_PERSIL_INDUK)
                self._fill_old_persil(DS_PERSIL_INDUK)
        elif self._tipe_berkas in ["DEG", "NPR"]:
            if len(self._old_parcels) > 0:
                self.combo_lihat_data.addItem(LIHAT_DATA_PERSIL_EDIT)
                self._fill_old_persil(DS_PERSIL_EDIT)
            else:
                self._process_parcels = False
                self.combo_lihat_data.addItem(LIHAT_DATA_APARTEMENT_EDIT)
                self._fill_old_apartment(DS_APARTEMEN_EDIT)
        elif self._tipe_berkas == "NME":
            self.combo_lihat_data.addItem(LIHAT_DATA_PERSIL_INDUK)
            self._fill_old_persil(DS_PERSIL_INDUK)
        elif self._tipe_berkas == "DAG":
            self._process_parcels = False
            self.combo_lihat_data.addItems([LIHAT_DATA_APARTEMENT_BARU, LIHAT_DATA_APARTEMENT_EDIT])
            self._fill_new_apartment()

        if self._kantor_id is None and self._tipe_kantor_id is not None:
            return

        self.get_wilayah_prior(self._kelurahan_id)

        current_provinsi_id = self._current_provinsi["PROPINSIID"]
        current_provinsi_index = 0
        for index, provinsi in enumerate(self._provinsi_by_kantor[self._kantor_id]):
            if provinsi["PROPINSIID"] == current_provinsi_id:
                current_provinsi_index = index

        self.populate_provinsi(self._kantor_id, str(self._tipe_kantor_id))
        self.populate_kabupaten(self._kantor_id, str(self._tipe_kantor_id), self._current_provinsi["PROPINSIID"])
        self.populate_kecamatan(self._kantor_id, str(self._tipe_kantor_id), self._current_kabupaten["KABUPATENID"])
        self.populate_kelurahan(self._kantor_id, str(self._tipe_kantor_id), self._current_kecamatan["KECAMATANID"])

        # TODO: ask is it okay to use currently selected propinsi instead of using wilayah prior?

        if self._process_parcels:
            self._autofill_persil_data()
        else:
            self._autofill_apartemen_data()

        if not self._validate_extent():
            # TODO: Show error message tergantung proyeksi, tm3 atau bukan
            pass
        
        if len(self._ds_parcel[DS_PERSIL_EDIT]) > 0 or len(self._ds_parcel[DS_APARTEMEN_EDIT]) > 0:
            self.combo_provinsi.setDisabled(True)
            self.combo_kabupaten.setDisabled(True)
            self.combo_kecamatan.setDisabled(True)
            self.combo_kelurahan.setDisabled(True)
        else:
            self.combo_provinsi.setDisabled(False)
            self.combo_kabupaten.setDisabled(False)
            self.combo_kecamatan.setDisabled(False)
            self.combo_kelurahan.setDisabled(False)

        if len(self._wilayah_prior) <= 2:
            self.label_kecamatan.hide()
            self.combo_kecamatan.hide()
            self.label_kelurahan.hide()
            self.combo_kelurahan.hide()
            self.check_simpan_bidang.setCheckState(2)

        if (len(self._ds_parcel[DS_PERSIL_EDIT]) == 0 \
                and len(self._ds_parcel[DS_PERSIL_INDUK]) == 0 \
                and len(self._ds_parcel[DS_APARTEMEN_EDIT]) == 0 ) \
                or self._tipe_berkas == "DAG":
            self.check_reset_di302.hide()
        
        edit_null_count = len([p for p in self._ds_parcel[DS_PERSIL_EDIT] if "NIB" not in p.keys() or not p["NIB"]])
        induk_null_count = len([p for p in self._ds_parcel[DS_PERSIL_INDUK] if "NIB" not in p.keys() or not p["NIB"]])
        
        print(edit_null_count, induk_null_count)
        print(self._ds_parcel[DS_PERSIL_EDIT])
        print(self._ds_parcel[DS_PERSIL_INDUK])

        if edit_null_count > 0 or induk_null_count > 0:
            self.label_status_l.setText('Ada kesalahan, cek error log')
            self.error_log.setHtml("Persil Edit atau Persil Induk dalam proses ini tidak memiliki NIB.<br/>" + \
                "Silahkan periksa data buku tanah yang dimasukkan dalam proses ini terlebih dahulu.<br/>" + \
                "Apabila memiliki NIB, perbaiki data buku tanah sesuai fisiknya. Jika tidak, " + \
                "silahkan memilih Lengkapi NIB untuk melanjutkan proses ini." + \
                "<br/>Jika memilih Lengkapi NIB maka GeoKKPWeb akan memberikan NIB yang baru")
            self.tabWidget.setCurrentIndex(1)
            self.btn_validasi.setDisabled(True)
        else:
            self.btn_validasi.setDisabled(False)
            self.check_nib.show()

    def _validate_extent(self):
        # TODO: validate extent is it correct
        return True

    def _handle_lihat_data_changed(self, label):
        if label == LIHAT_DATA_PERSIL_BARU:
            pass
        elif label == LIHAT_DATA_PERSIL_EDIT:
            pass
        elif label == LIHAT_DATA_PERSIL_INDUK:
            pass
        elif label == LIHAT_DATA_APARTEMENT_BARU:
            pass
        elif label == LIHAT_DATA_APARTEMENT_EDIT:
            pass

    def get_wilayah_prior(self, kelurahan_id=None):
        if not kelurahan_id:
            return
        
        response = endpoints.get_wilayah_prior(kelurahan_id)
        self._wilayah_prior = json.loads(response.content)
        return self._wilayah_prior

    def _autofill_persil_data(self):
        pass

    def _autofill_apartemen_data(self):
        pass

    def _fill_new_persil(self):
        if not self._new_parcels:
            return
        persil_ids = [str(p) for p in self._new_parcels]

        response = endpoints.get_parcels(persil_ids)
        response_json = json.loads(response.content)
        print('new_persil', response_json)
        column_defs = DS_COLUMN_MAP[DS_PERSIL_EDIT]
        column_defs_res = list(response_json["PERSILBARU"][0].keys())

        template = {}
        for col in column_defs:
            template[col] = None
        
        for row in response_json["PERSILBARU"]:
            a_row = template.copy()
            a_row[column_defs[1]] = row[column_defs_res[0]] 
            a_row[column_defs[2]] = row[column_defs_res[1]][9:] 
            a_row[column_defs[3]] = row[column_defs_res[2]] 
            self._ds_parcel[DS_PERSIL_EDIT].append(a_row)
    
    def _fill_old_persil(self, name):
        if not self._old_parcels:
            return
        persil_ids = [str(p) for p in self._old_parcels]
        response = endpoints.get_parcels(persil_ids)
        response_json = json.loads(response.content)
        print('old_persil', response_json)
        column_defs = DS_COLUMN_MAP[name]
        column_defs_res = list(response_json["PERSILBARU"][0].keys())

        template = {}
        for col in column_defs:
            template[col] = None

        for row in response_json["PERSILBARU"]:
            a_row = template.copy()
            a_row[column_defs[1]] = row[column_defs_res[0]] 
            a_row[column_defs[2]] = row[column_defs_res[1]][9:] 
            a_row[column_defs[3]] = row[column_defs_res[2]]
            self._ds_parcel[name].append(a_row)
    
    def _fill_new_apartment(self):
        if not self._new_apartments:
            return
        apartment_ids = [str(a) for a in self._new_apartments]

        response = endpoints.get_apartments(apartment_ids)
        response_json = json.loads(response.content)
        print('new_apartments', response_json)
        column_defs = DS_COLUMN_MAP[DS_APARTEMEN_EDIT]
        column_defs_res = list(response_json["APARTEMENBARU"][0].keys())

        template = {}
        for col in column_defs:
            template[col] = None

        for row in response_json["APARTEMENBARU"]:
            a_row = template.copy()
            a_row[column_defs[1]] = row[column_defs_res[0]] 
            a_row[column_defs[2]] = row[column_defs_res[1]] 
            a_row[column_defs[3]] = row[column_defs_res[2]] 
            self._ds_parcel[DS_APARTEMEN_EDIT].append(a_row)

    def _fill_old_apartment(self, name):
        if not self._new_apartments:
            return
        apartment_ids = [str(a) for a in self._new_apartments]

        response = endpoints.get_apartments(apartment_ids)
        response_json = json.loads(response.content)
        print('new_apartments', response_json)
        column_defs = DS_COLUMN_MAP[DS_APARTEMEN_EDIT]
        column_defs_res = list(response_json["APARTEMENBARU"][0].keys())

        template = {}
        for col in column_defs:
            template[col] = None

        for row in response_json["APARTEMENBARU"]:
            a_row = template.copy()
            a_row[column_defs[1]] = row[column_defs_res[0]] 
            a_row[column_defs[2]] = row[column_defs_res[1]] 
            a_row[column_defs[3]] = row[column_defs_res[2]]
            self._ds_parcel[name].append(a_row)

    def clear_combobox(self, level):
        combo = [
            self.combo_kelurahan,
            self.combo_kecamatan,
            self.combo_kabupaten,
            self.combo_provinsi,
        ]
        for i in range(0, level):
            combo[i].blockSignals(True)
        for i in range(0, level):
            combo[i].clear()
        for i in range(0, level):
            combo[i].blockSignals(False)

    def populate_provinsi(self, kantor_id, tipe_kantor_id):
        prev = readSetting("provinsiterpilih", {})
        prev_id = prev["PROPINSIID"] if prev else None
        
        self.clear_combobox(4)
        if kantor_id in self._provinsi_by_kantor.keys() \
                and self._provinsi_by_kantor[kantor_id]:
            data_provinsi = self._provinsi_by_kantor[kantor_id]
        else:
            response = endpoints.get_provinsi_by_kantor(kantor_id, str(tipe_kantor_id))
            response_json = json.loads(response.content)
            if response_json and len(response_json["PROPINSI"]):
                data_provinsi = response_json["PROPINSI"]
                self._provinsi_by_kantor[kantor_id] = data_provinsi
                storeSetting("provinsibykantor", self._provinsi_by_kantor)
            else:
                QtWidgets.QMessageBox.warning(
                    None, 
                    "Data Provinsi", 
                    "Tidak bisa membaca data provinsi dari server"
                )
                return

        current_index = 0
        for index, provinsi in enumerate(data_provinsi):
            if provinsi["PROPINSIID"] == prev_id:
                current_index = index
            self.combo_provinsi.addItem(provinsi["PROPNAMA"])
        self.combo_provinsi.setCurrentIndex(current_index)

    def populate_kabupaten(self, kantor_id, tipe_kantor_id, provinsi_id):
        prev = readSetting("kabupatenterpilih", {})
        prev_id = prev["KABUPATENID"] if prev else None

        self.clear_combobox(3)
        if provinsi_id in self._kabupaten_by_provinsi.keys() \
                and self._kabupaten_by_provinsi[provinsi_id]:
            data_kabupaten = self._kabupaten_by_provinsi[provinsi_id]
        else:
            response = endpoints.get_kabupaten_by_kantor(kantor_id, str(tipe_kantor_id), provinsi_id)
            response_json = json.loads(response.content)
            if response_json and len(response_json["KABUPATEN"]):
                data_kabupaten = response_json["KABUPATEN"]
                self._kabupaten_by_provinsi[provinsi_id] = data_kabupaten
                storeSetting("kabupatenbyprovinsi", self._kabupaten_by_provinsi)
            else:
                QtWidgets.QMessageBox.warning(
                    None, 
                    "Data Kabupaten", 
                    "Tidak bisa membaca data kabupaten dari server"
                )
                return

        current_index = 0
        for index, kabupaten in enumerate(data_kabupaten):
            if kabupaten["KABUPATENID"] == prev_id:
                current_index = index
            self.combo_kabupaten.addItem(kabupaten["KABUNAMA"])
        self.combo_kabupaten.setCurrentIndex(current_index)

    def populate_kecamatan(self, kantor_id, tipe_kantor_id, kabupaten_id):
        prev = readSetting("kecamatanterpilih", {})
        prev_id = prev["KECAMATANID"] if prev else None
        
        self.clear_combobox(2)
        if kabupaten_id in self._kecamatan_by_kabupaten.keys() \
                and self._kecamatan_by_kabupaten[kabupaten_id]:
            data_kecamatan = self._kecamatan_by_kabupaten[kabupaten_id]
        else:
            response = endpoints.get_kecamatan_by_kantor(kantor_id, str(tipe_kantor_id), kabupaten_id)
            response_json = json.loads(response.content)
            if response_json and len(response_json["KECAMATAN"]):
                data_kecamatan = response_json["KECAMATAN"]
                self._kecamatan_by_kabupaten[kabupaten_id] = data_kecamatan
                storeSetting("kecamatanbykabupaten", self._kecamatan_by_kabupaten)

            else:
                QtWidgets.QMessageBox.warning(
                    None, 
                    "Data Kabupaten", 
                    "Tidak bisa membaca data kabupaten dari server"
                )
                return

        current_index = 0
        for index, kecamatan in enumerate(data_kecamatan):
            if kecamatan["KECAMATANID"] == prev_id:
                current_index = index
            self.combo_kecamatan.addItem(kecamatan["KECANAMA"])
        self.combo_kecamatan.setCurrentIndex(current_index)

    def populate_kelurahan(self, kantor_id, tipe_kantor_id, kecamatan_id):
        prev = readSetting("kelurahanterpilih", {})
        prev_id = prev["DESAID"] if prev else None
        
        self.clear_combobox(1)
        if kecamatan_id in self._kelurahan_by_kecamatan.keys() \
                and self._kelurahan_by_kecamatan[kecamatan_id]:
            data_kelurahan = self._kelurahan_by_kecamatan[kecamatan_id]
        else:
            response = endpoints.get_desa_by_kantor(kantor_id, str(tipe_kantor_id), kecamatan_id)
            response_json = json.loads(response.content)
            if response_json and len(response_json["DESA"]):
                data_kelurahan = response_json["DESA"]
                self._kelurahan_by_kecamatan[kecamatan_id] = data_kelurahan
                storeSetting("kelurahanbykecamatan", self._kelurahan_by_kecamatan)
            else:
                QtWidgets.QMessageBox.warning(
                    None, 
                    "Data Kabupaten", 
                    "Tidak bisa membaca data kabupaten dari server"
                )
                return

        current_index = 0
        for index, kelurahan in enumerate(data_kelurahan):
            if kelurahan["DESAID"] == prev_id:
                current_index = index
            self.combo_kelurahan.addItem(kelurahan["DESANAMA"])
        self.combo_kelurahan.setCurrentIndex(current_index)

    def provinsi_changed(self, index):
        if self._kantor_id not in self._provinsi_by_kantor.keys():
            return
        data_provinsi = self._provinsi_by_kantor[self._kantor_id]
        self._current_provinsi = data_provinsi[index]

        current_provinsi_id = self._current_provinsi["PROPINSIID"]
        self.populate_kabupaten(self._kantor_id, self._tipe_kantor_id, current_provinsi_id)

    def kabupaten_changed(self, index):
        current_provinsi_id = self._current_provinsi["PROPINSIID"]
        if current_provinsi_id not in self._kabupaten_by_provinsi.keys():
            return
        data_kabupaten = self._kabupaten_by_provinsi[current_provinsi_id]
        self._current_kabupaten = data_kabupaten[index]

        current_kabupaten_id = self._current_kabupaten["KABUPATENID"]
        self.populate_kecamatan(self._kantor_id, self._tipe_kantor_id, current_kabupaten_id)

    def kecamatan_changed(self, index):
        current_kabupaten_id = self._current_kabupaten["KABUPATENID"]
        if current_kabupaten_id not in self._kecamatan_by_kabupaten.keys():
            return
        data_kecamatan = self._kecamatan_by_kabupaten[current_kabupaten_id]
        self._current_kecamatan = data_kecamatan[index]
        
        current_kecamatan_id = self._current_kecamatan["KECAMATANID"]
        self.populate_kelurahan(self._kantor_id, self._tipe_kantor_id, current_kecamatan_id)

    def kelurahan_changed(self, index):
        current_kecamatan_id = self._current_kecamatan["KECAMATANID"]
        if current_kecamatan_id not in self._kelurahan_by_kecamatan.keys():
            return
        data_kelurahan = self._kelurahan_by_kecamatan[current_kecamatan_id]

        self._current_kelurahan = data_kelurahan[index]
    
    def _handle_process(self):
        if len(self._ds_parcel[DS_PERSIL_BARU]) > 0 or len(self._ds_parcel[DS_APARTEMEN_BARU]) > 0:
            msg = ""
            if len(self._wilayah_prior) == 2:
                msg = f"Anda akan melakukan integrasi di Kabupaten / Kota {self.combo_kabupaten.currentText()}, " + \
                    f"Provinsi {self.combo_provinsi.currentText()}.\nApakah anda akan melanjutkan?"
            else:
                msg = f"Anda akan melakukan integrasi di Desa {self.combo_kelurahan.currentText()}, " + \
                    f"Kecamatan {self.combo_kecamatan.currentText()}.\nApakah anda akan melanjutkan?"
            
            result = QtWidgets.QMessageBox.question(self, 'Perhatian', msg)
            if result == QtWidgets.QMessageBox.Yes:
                parcel_design = {
                    "wilayah_id": '',
                    "ds_parcel": {},
                    "old_parcel": [],
                    "ganti_desa": '',
                    "reset_302": False
                }
                if len(self._wilayah_prior) > 2:
                    parcel_design["wilayah_id"] = self.current_kelurahan["DESAID"]
                else:
                    parcel_design["wilayah_id"] = self.current_kabupaten["KABUPATENID"]
                
                parcel_design["ds_parcel"] = self._ds_parcel
                parcel_design["old_parcel"] = self._old_parcels
                parcel_design["ganti_desa"] = self._ganti_desa
                parcel_design["reset_302"] = self.check_reset_di302.isChecked()
                self.parcel_design_event.emit(parcel_design)
        else:
            parcel_design = {
                "wilayah_id": '',
                "ds_parcel": {},
                "old_parcel": [],
                "ganti_desa": '',
                "reset_302": False
            }
            if len(self._wilayah_prior) > 2:
                parcel_design["wilayah_id"] = self._current_kelurahan["DESAID"]
            else:
                parcel_design["wilayah_id"] = self._current_kabupaten["KABUPATENID"]
            
            parcel_design["ds_parcel"] = self._ds_parcel
            parcel_design["old_parcel"] = self._old_parcels
            parcel_design["ganti_desa"] = self._ganti_desa
            parcel_design["reset_302"] = self.check_reset_di302.isChecked()
            self.parcel_design_event.emit(parcel_design)
        self.close()

    def _handle_validate(self):
        valid = True
        msg = ""
        if self._new_parcel_number > 0:
            if len(self._ds_parcel[DS_PERSIL_BARU]) + len(self._ds_parcel[DS_PERSIL_EDIT]) != self._new_parcel_number:
                valid = False
                msg = "Jumlah persil baru tidak sesuai!"
        else:
            if len(self._ds_parcel[DS_PERSIL_BARU]) > 0:
                valid = False
                msg = "Maaf, proses ini tidak membuat persil baru"

        if self._new_parcels or self._old_parcels:
            for row in self._ds_parcel[DS_PERSIL_EDIT]:
                if not row["BOUNDARY"]:
                    valid = False
                    msg = "Ada Persil Edit yang tidak memiliki geometri!"
                    break
                if not row["REGID"]:
                    valid = False
                    msg = "Ada Persil Edit yang tidak memiliki REGID!"
                    break

        if self._new_apartments or self._old_apartments:
            for row in self._ds_parcel[DS_PERSIL_EDIT]:
                if not row["BOUNDARY"]:
                    valid = False
                    msg = "Ada Apartemen Edit yang tidak memiliki geometri!"
                    break
                if not row["REGID"]:
                    valid = False
                    msg = "Ada Apartemen Edit yang tidak memiliki REGID!"
                    break

        if self._tipe_berkas in ["DIV", "NME", "SPL"]:
            persil_induk_count = len(self._ds_parcel[DS_PERSIL_INDUK])
            if self._tipe_berkas in ["DIV", "SPL"] and persil_induk_count != 1:
                valid = False
                msg = "Prosedur DIV/SPL jumlah persil induk harus ada 1!"
            elif self._tipe_berkas == "NME" and persil_induk_count < 1:
                valid = False
                msg = "Prosedur NME jumlah persil induk harus ada minimal 1!"
            else:
                for row in self._ds_parcel[DS_PERSIL_INDUK]:
                    if not row["REGID"]:
                        valid = False
                        msg = "Persil Induk tidak memiliki REGID!"
                        break
            
        if self._tipe_berkas == "DAG":
            if self._new_apartment_number > 0:
                if len(self._ds_parcel[DS_APARTEMEN_BARU]) + len(self._ds_parcel[DS_APARTEMEN_EDIT]) != self._new_apartment_number:
                    valid = False
                    msg = "Jumlah apartemen tidak sesuai!"
                for row in self._ds_parcel[DS_APARTEMEN_EDIT]:
                    if not row["BOUNDARY"]:
                        valid = False
                        msg = "Ada Apartemen Edit yang tidak memiliki geometri!"
                        break
                    if not row["REGID"]:
                        valid = False
                        msg = "Ada Apartemen Edit yang tidak memiliki REGID!"
                        break
        
        if valid:
            self.btn_proses.setDisabled(False)
            self.label_status_l.setText("Lakukan Integrasi")
        else:
            self.label_status_l.setText("Ada kesalahan, cek error log")
            self.error_log.setText(msg)
            self.tabWidget.setCurrentIndex(1)

    def _handle_ganti_desa(self):
        if not self.combo_kelurahan.isEnabled() and not self.combo_kecamatan.isEnabled():
            QtWidgets.QMessageBox.warning(
                None, 
                "Perhatian", 
                "Pilih Desa Tujuan, Kemudian Klik Ganti Desa Lagi"
            )

            self.combo_kecamatan.setDisabled(False)
            self.combo_kelurahan.setDisabled(False)
            self.combo_lihat_data.setDisabled(True)
            self.btn_validasi.setDisabled(True)
            self.btn_proses.setDisabled(True)
        else:
            msg = f"Anda akan melakukan perubahan data persil, su, dan hak ke desa {self.combo_kelurahan.currentText()} " + \
                f", Kecamatan {self.combo_kecamatan.currentText()}. \nApakah anda akan melanjutkan?"
            result = QtWidgets.QMessageBox.question(self, 'Perhatian', msg)

            if result == QtWidgets.QMessageBox.Yes:
                selected_parcels = [str(p) for p in self._old_parcels]
                user = app_state.set('user', {})
                user_id = user.value["userId"] if user.value and "userId" in user.value.keys() else None
                current_kelurahan_id = self._current_kelurahan["DESAID"]
                response = endpoints.ganti_desa(
                    self._nomor_berkas, 
                    self._tahun_berkas,
                    self._kantor_id,
                    self._tipe_kantor_id,
                    current_kelurahan_id,
                    "Persil",
                    selected_parcels,
                    user_id
                )
                response_json = json.loads(response.content)
                print('ganti desa', response_json)
                
                if len(response_json["Error"]) > 0:
                    msg = response_json["Error"][0]["message"]
                    QtWidgets.QMessageBox.critical(self, 'Error', msg)
                else:
                    parcels = [str(p) for p in self._old_parcels]
                    kelurahan_id = self._current_kelurahan["DESAID"]
                    table_name = self.combo_lihat_data.currentText().replace(" ", "")

                    msg = "Ganti desa berhasil dilakukan"

                    # TODO: change this to column based, the source only use key index instead of key
                    columns = response_json["DataBaru"].keys()
                    col0 = column[0]
                    col1 = column[1]
                    col2 = column[2]
                    col6 = column[6]
                    col7 = column[7]

                    for row in response_json["DataBaru"]:
                        if row[col6] in self._old_parcels:
                            self._old_parcels.remove(row[col6])
                            self._old_parcels.append(row[col7])

                            my_rows = [x for x in self._ds_parcel[table_name] if x["REGID"] == col6]
                            my_rows[0]["REGID"] = row[col7]
                            my_rows[0]["NIB"] = row[col1].split('.')[1]
                            msg += f"\nNIB {row[col0]} ==> {row[col1]}"
                            msg += f"\nSU {row[col2]} ==> {row[col3]}"
                            msg += f"\nHAK {row[col4]} ==> {row[col5]}"
                    
                    # TODO: refresh table desain persil

                    parcel_design = {
                        "wilayah_id": current_kelurahan_id,
                        "ds_parcel": {},
                        "old_parcel": self._old_parcels,
                        "ganti_desa": "1",
                        "reset_302": False
                    }
                    self.parcel_design_event.emit(parcel_design)

                    QtWidgets.QMessageBox.information(
                        None, 
                        "Perhatian", 
                        msg
                    )

                    self.check_nib.show()
                    self.btn_validasi.setDisabled(False)
                    self.btn_proses.setDisabled(True)
                    self.btn_ganti_desa.setDisabled(True)
            
                self.combo_kecamatan.setDisabled(True)
                self.combo_kelurahan.setDisabled(True)
                self.combo_lihat_data.setDisabled(False)
            else:
               self.combo_kecamatan.setDisabled(True) 
               self.combo_kelurahan.setDisabled(True)
               self.combo_lihat_data.setDisabled(False)

               self.btn_validasi.setDisabled(False)
               self.btn_proses.setDisabled(True)
               self.btn_ganti_desa.setDisabled(False)

    def get_sdo_point(self):
        pass

    def get_sdo_polygon(self):
        pass

    def create_sdo_polygon_from_ring(self):
        pass

    def calculate_area(self):
        pass

    def get_linear_ring(self):
        pass
    
    def set_context_menu_visibility(self):
        pass
    
    def move_apartment(self):
        pass

    def refresh_status(self):
        pass
    
    def _handle_check_nib(self, checked):
        edit_null_count = len([p for p in self._ds_parcel[DS_PERSIL_EDIT] if "NIB" not in p.keys() or not p["NIB"]])
        induk_null_count = len([p for p in self._ds_parcel[DS_PERSIL_INDUK] if "NIB" not in p.keys() or not p["NIB"]])
        print(checked, edit_null_count, induk_null_count)
        print(self._ds_parcel[DS_PERSIL_EDIT])
        print(self._ds_parcel[DS_PERSIL_INDUK])

        if edit_null_count > 0 or induk_null_count > 0:
            if checked:
                self.btn_validasi.setDisabled(False)
                self.tabWidget.setCurrentIndex(0)
                self.label_status_l.setText("")
            else:
                self.btn_validasi.setDisabled(True)
                self.label_status_l.setText("Ada Kesalahan, cek error log")

    def _handle_batal(self):
        self.close()