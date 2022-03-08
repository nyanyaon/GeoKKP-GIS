from asyncio.windows_events import NULL
import os
import json
import hashlib
from re import template
from urllib import response
from xml.dom.expatbuilder import parseString
# from modules.import_surat_ukur import DS_PERSIL_EDIT_COLUMNS, DS_PERSIL_POLIGON_COLUMNS

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject, QgsWkbTypes, QgsVectorLayer
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from .utils import (
    readSetting,
    storeSetting,
    get_nlp,
    get_nlp_index,
    get_epsg_from_tm3_zone,
)
from .utils.geometry import get_sdo_point, get_sdo_polygon
from .api import endpoints
from .memo import app_state
from .models.dataset import Dataset

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/import_surat_ukur.ui")
)

DS_PERSIL_EDIT = "PersilEdit"
DS_POLIGON = "Polygon"
DS_GARIS = "Garis"
DS_TEKS = "Teks"
DS_TITIK = "Titik"
DS_DIMENSI = "Dimensi"

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
]

DS_POLIGON_COLUMNS = [
    "Key"
    "Type"
    "Label"
    "Height"
    "Orientation"
    "Boundary"
    "Text"
]

DS_GARIS_COLUMN = [
    "KEY"
    "TYPE"
    "LINE"
]

DS_TEKS_COLUMN = [
    "Key"
    "Type"
    "Height"
    "Orientation"
    "Label"
    "Position"
]

DS_TITIK_COLUMN = [
    "Key"
    "Type"
    "PointOrientation"
    "TextOrientation"
    "Scale"
    "Height"
    "Label"
    "PointPosition"
    "TextPosition"
]

DS_DIMENSI_COLUMN = [
    "Key"
    "Type"
    "Line"
    "Initialpoint"
    "Labelpoint"
    "Endpoint"
    "Initialorientation"
    "Labelorientation"
    "Endorientation"
    "Height"
    "Label"
]

DS_COLUMN_MAP = {
    DS_PERSIL_EDIT : DS_PERSIL_EDIT_COLUMNS,
    DS_POLIGON : DS_POLIGON_COLUMNS,
    DS_GARIS : DS_GARIS_COLUMN,
    DS_TEKS : DS_TEKS_COLUMN,
    DS_TITIK : DS_TITIK_COLUMN,
    DS_DIMENSI : DS_DIMENSI_COLUMN,
}

class ImportSuratUkur(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()
    writeLeftStatus = pyqtSignal(str)
    writeRightStatus = pyqtSignal(str)
    writeErrorLog = pyqtSignal(str)
    changeTabIndex = pyqtSignal(int)
    processed = pyqtSignal(object)

    def __init__(
        self,
        parent,
        old_parcel,
        old_apartment,
        wilayah_id,
        per_desa,
        old_gugus_id,
    ):
        super(ImportSuratUkur, self).__init__(parent)

        self._parent = parent

        # self._ent_dataset = {}
        self._wilayah_id = ""
        self._per_desa = False
        self._old_gugus_id = ""
        self._new_parcels = []
        self._new_apartments = []
        # self._bpn_layer 
        self._current_parcel_table = ""
        self._first_load_prop = True
        self._first_load_kabu = True
        self._first_load_keca = True
        self._first_load_desa = True

        self._ds_persil = {
            DS_PERSIL_EDIT : [],
            DS_POLIGON : [],
            DS_GARIS : [],
            DS_TEKS : [],
            DS_TITIK : [],
            DS_DIMENSI : [],
        }

        # self._bpn_layer = bpn_layer
        # self._create_dataset_integration()
        self._kantor_id = ""
        self._tipe_kantor_id = ""

        if not old_apartment:
            if type(old_parcel) == str:
                self._new_parcels = [old_parcel]
            else:
                self._new_parcels = old_parcel
        else:
            if type(old_apartment) == str:
                self._new_apartments = [old_apartment]
            else:
                self._new_apartments = old_apartment
        self._old_gugus_id = old_gugus_id
        self._wilayah_id = wilayah_id
        self._per_desa = per_desa
        self._dt_wilayah = self._get_wilayah_prior(self._wilayah_id)

        self.setupUi(self)

        self.cmb_data_view.currentIndexChanged.connect(self._data_view_changed)
        self.cmb_propinsi.currentIndexChanged.connect(self._propinsi_changed)
        self.cmb_kabupaten.currentIndexChanged.connect(self._kabupaten_changed)
        self.cmb_kecamatan.currentIndexChanged.connect(self._kecamatan_changed)
        self.btn_validasi.clicked.connect(self._btn_validasi_clicked)
        self.btn_proses.clicked.connect(self._btn_proses_clicked)
        self.chb_tm3.stateChanged.connect(self._chb_tm3_state_changed)
        self.chb_tm3.setChecked(True)

        self.dgv_parcel.__class__.dropEvent = self._drop_event

        self._get_current_settings()
        self.setup_workpanel()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()

    def setup_workpanel(self):
        if len(self._new_parcels) > 0:
            self.cmb_data_view.addItem("Persil Edit")
            self._fill_new_parcels()
            self._fill_persil_data_table_automatically()
            self.cmb_data_view.setCurrentIndex(0)
            self._refresh_status()
            self._set_context_menu_visiblity()
        
        print(self._dt_wilayah)
        print(self._kantor_id)
        print(self._tipe_kantor_id)

        self._set_cmb_propinsi(
            self._kantor_id,
            self._tipe_kantor_id
        )

        if self._first_load_prop:
            current_propinsi_id = self.cmb_propinsi.currentData()
            self._set_cmb_kabupaten(
                self._kantor_id,
                self._tipe_kantor_id,
                current_propinsi_id
            )
            self._first_load_prop = False
        
        if len(self._dt_wilayah) <= 2:
            self.cmb_kecamatan.hide()
            self.cmb_desa.hide()
            self.lbl_wilayah_induk.hide()
            self.lbl_wilayah.hide()
        
        # TODO: sistem koordinat
    
    def _get_current_settings(self):
        self._current_kantor = readSetting("kantorterpilih")
        self._propinsi_by_kantor = readSetting("provinsibykantor", {})
        self._kabupaten_by_propinsi = readSetting("kabupatenbyprovinsi", {})
        self._kecamatan_by_kabupaten = readSetting("kecamatanbykabupaten", {})
        self._kelurahan_by_kecamatan = readSetting("kelurahanbykecamatan", {})
        
        if not self._current_kantor or "kantorID" not in self._current_kantor:
            return

        self._kantor_id = self._current_kantor["kantorID"]
        self._tipe_kantor_id = str(self._current_kantor["tipeKantorId"])        

    # def _create_dataset_integration(self):
    #     self._ent_dataset = {
    #         DS_PERSIL_EDIT: [],
    #         DS_POLIGON: [],
    #         DS_TEKS: [],
    #         DS_TITIK: [],
    #         DS_DIMENSI: [],
    #     }

    def _get_wilayah_prior(self, wilayah_id=None):
        if not wilayah_id:
            return []

        response = endpoints.get_wilayah_prior(wilayah_id)
        self._wilayah_prior = json.loads(response.content)
        return self._wilayah_prior

    def _set_cmb_propinsi(self, kantor_id, tipe_kantor_id):
        self._clear_combobox(4)
        if (
            kantor_id in self._propinsi_by_kantor.keys()
            and self._propinsi_by_kantor[kantor_id]
        ):
            data_propinsi = self._propinsi_by_kantor[kantor_id]
        else:
            response = endpoints.get_provinsi_by_kantor(kantor_id, str(tipe_kantor_id))
            response_json = json.loads(response.content)
            if response_json and len(response_json["PROPINSI"]):
                data_propinsi = response_json["PROPINSI"]
                self._propinsi_by_kantor[kantor_id] = data_propinsi
                storeSetting("provinsibykantor", self._propinsi_by_kantor)
            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Data Provinsi",
                    "Tidak bisa membaca data provinsi dari server",
                )
                return
        
        prior = [f for f in self._dt_wilayah if f["TIPEWILAYAHID"] == 1]
        current_index = 0
        for index, propinsi in enumerate(data_propinsi):
            if propinsi["PROPINSIID"] == prior[0]["WILAYAHID"]:
                current_index = index
            self.cmb_propinsi.addItem(propinsi["PROPNAMA"], propinsi["PROPINSIID"])
        if self._first_load_prop:
            self.cmb_propinsi.setCurrentIndex(current_index)
            self._first_load_prop = False
    
    def _set_cmb_kabupaten(self, kantor_id, tipe_kantor_id, propinsi_id):
        self._clear_combobox(3)
        if (
            propinsi_id in self._kabupaten_by_propinsi.keys()
            and self._kabupaten_by_propinsi[propinsi_id]
        ):
            data_kabupaten = self._kabupaten_by_propinsi[propinsi_id]
        else:
            response = endpoints.get_kabupaten_by_kantor(
                kantor_id, str(tipe_kantor_id), propinsi_id
            )
            response_json = json.loads(response.content)
            if response_json and len(response_json["KABUPATEN"]):
                data_kabupaten = response_json["KABUPATEN"]
                self._kabupaten_by_propinsi[propinsi_id] = data_kabupaten
                storeSetting("kabupatenbyprovinsi", self._kabupaten_by_propinsi)
            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Data Kabupaten",
                    "Tidak bisa membaca data kabupaten dari server",
                )
                return

        prior = [f for f in self._dt_wilayah if f["TIPEWILAYAHID"] in (2, 3, 4)]
        current_index = 0
        for index, kabupaten in enumerate(data_kabupaten):
            if kabupaten["KABUPATENID"] == prior[0]["WILAYAHID"]:
                current_index = index
            self.cmb_kabupaten.addItem(
                kabupaten["KABUNAMA"], kabupaten["KABUPATENID"]
            )
        if self._first_load_kabu:
            self.cmb_kabupaten.setCurrentIndex(current_index)
            self._first_load_kabu = False
    
    def _set_cmb_kecamatan(self, kantor_id, tipe_kantor_id, kabupaten_id):

        self._clear_combobox(2)
        if (
            kabupaten_id in self._kecamatan_by_kabupaten.keys()
            and self._kecamatan_by_kabupaten[kabupaten_id]
        ):
            data_kecamatan = self._kecamatan_by_kabupaten[kabupaten_id]
        else:
            response = endpoints.get_kecamatan_by_kantor(
                kantor_id, str(tipe_kantor_id), kabupaten_id
            )
            response_json = json.loads(response.content)
            if response_json and len(response_json["KECAMATAN"]):
                data_kecamatan = response_json["KECAMATAN"]
                self._kecamatan_by_kabupaten[kabupaten_id] = data_kecamatan
                storeSetting("kecamatanbykabupaten", self._kecamatan_by_kabupaten)

            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Data Kabupaten",
                    "Tidak bisa membaca data kabupaten dari server",
                )
                return

        prior = [f for f in self._dt_wilayah if f["TIPEWILAYAHID"] == 5]
        current_index = 0
        for index, kecamatan in enumerate(data_kecamatan):
            if kecamatan["KECAMATANID"] == prior[0]["WILAYAHID"]:
                current_index = index
            self.cmb_kecamatan.addItem(
                kecamatan["KECANAMA"], kecamatan["KECAMATANID"]
            )

        if self._first_load_keca:
            self.cmb_kecamatan.setCurrentIndex(current_index)
            self._first_load_keca = False

    def _set_cmb_desa(self, kantor_id, tipe_kantor_id, kecamatan_id):
        self._clear_combobox(1)
        if (
            kecamatan_id in self._kelurahan_by_kecamatan.keys()
            and self._kelurahan_by_kecamatan[kecamatan_id]
        ):
            data_kelurahan = self._kelurahan_by_kecamatan[kecamatan_id]
        else:
            response = endpoints.get_desa_by_kantor(
                kantor_id, str(tipe_kantor_id), kecamatan_id
            )
            response_json = json.loads(response.content)
            if response_json and len(response_json["DESA"]):
                data_kelurahan = response_json["DESA"]
                self._kelurahan_by_kecamatan[kecamatan_id] = data_kelurahan
                storeSetting("kelurahanbykecamatan", self._kelurahan_by_kecamatan)
            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Data Kabupaten",
                    "Tidak bisa membaca data kabupaten dari server",
                )
                return

        prior = [f for f in self._dt_wilayah if f["TIPEWILAYAHID"] in [6, 7]]
        current_index = 0
        for index, kelurahan in enumerate(data_kelurahan):
            if kelurahan["DESAID"] == prior[0]["WILAYAHID"]:
                current_index = index
            self.cmb_desa.addItem(kelurahan["DESANAMA"], kelurahan["DESAID"])

        if self._first_load_desa:
            self.cmb_desa.setCurrentIndex(current_index)
            self._first_load_desa = False

    def _propinsi_changed(self):
        if self._kantor_id not in self._propinsi_by_kantor.keys():
            return
        current_propinsi_id = self.cmb_propinsi.currentData()
        self._set_cmb_kabupaten(
            self._kantor_id, self._tipe_kantor_id, current_propinsi_id
        )

    def _kabupaten_changed(self):
        current_propinsi_id = self.cmb_propinsi.currentData()
        if current_propinsi_id not in self._kabupaten_by_propinsi.keys():
            return

        current_kabupaten_id = self.cmb_kabupaten.currentData()
        if not self._per_desa:
            self._set_cmb_kecamatan(
                self._kantor_id, self._tipe_kantor_id, current_kabupaten_id
            )

    def _kecamatan_changed(self):
        current_kabupaten_id = self.cmb_kabupaten.currentData()
        if current_kabupaten_id not in self._kecamatan_by_kabupaten.keys():
            return

        current_kecamatan_id = self.cmb_kecamatan.currentData()
        if not self._per_desa:
            self._set_cmb_desa(
                self._kantor_id, self._tipe_kantor_id, current_kecamatan_id
            )
    
    def _clear_combobox(self, level):
        combo = [
            self.cmb_desa,
            self.cmb_kecamatan,
            self.cmb_kabupaten,
            self.cmb_propinsi,
        ]
        for i in range(0, level):
            combo[i].blockSignals(True)
        for i in range(0, level):
            combo[i].clear()
        for i in range(0, level):
            combo[i].blockSignals(False)
    
    def _data_view_changed(self):
        self._refresh_status()
        self._set_context_menu_visiblity()

    def _fill_new_parcels(self):
        if (self._new_parcels and len(self._new_parcels) > 0):
            parcel_ids = [str(p) for p in self._new_parcels]

            response = endpoints.get_parcels(parcel_ids)
            response_json = json.loads(response.content)
            print("new_persil", response_json)
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
                self._ds_persil[DS_PERSIL_EDIT].append(a_row)

        else:
            print("there is no new parcels")

    def _fill_persil_data_table_automatically(self):
        print(f"current layer : {self._parent._current_layers}")
        print(f"submit layer : {self._parent._submit_layers}")
        for layer in self._parent._submit_layers:
            try:
                layer.id()
            except RuntimeError:
                continue

            if not layer.name().startswith("(020100)"):
                continue

            features = layer.getFeatures()
            for feature in features:
                identifier = f"{layer.id()}|{feature.id()}".encode("utf-8")
                objectid = hashlib.md5(identifier).hexdigest().upper()

                point = feature.geometry().pointOnSurface().asPoint()
                teks = get_sdo_point(point)
                poli = get_sdo_polygon(feature)

                nib = feature.attribute("label") if feature.attribute("label") else ""
                height = (
                    float(feature.attribute("height"))
                    if feature.attribute("height")
                    else 0
                )
                orientation = (
                    float(feature.attribute("rotation"))
                    if feature.attribute("rotation")
                    else 0
                )

                if poli["batas"]:
                    row = {}
                    if len(self._ds_persil["PersilEdit"]):
                        filtered = [
                            f
                            for f in self._ds_persil["PersilEdit"]
                            if f["NIB"] == nib
                        ]
                        if filtered:
                            row = filtered[0]
                    luas_round = str(round(poli["luas"], 3))

                    if row:
                        row[DS_PERSIL_EDIT_COLUMNS[0]] = objectid
                        row[DS_PERSIL_EDIT_COLUMNS[4]] = nib
                        row[DS_PERSIL_EDIT_COLUMNS[5]] = luas_round
                        row[DS_PERSIL_EDIT_COLUMNS[6]] = poli["batas"]
                        row[DS_PERSIL_EDIT_COLUMNS[7]] = teks
                        row[DS_PERSIL_EDIT_COLUMNS[8]] = "Tunggal"
                        row[DS_PERSIL_EDIT_COLUMNS[9]] = height
                        row[DS_PERSIL_EDIT_COLUMNS[10]] = orientation
                        # self._ds_persil["PersilEdit"].append(row)
                    else:
                        a_row = {}
                        for index, col in enumerate(DS_COLUMN_MAP[DS_PERSIL_EDIT]):
                            a_row[col] = None
                        a_row[DS_COLUMN_MAP[DS_PERSIL_EDIT][0]] = objectid
                        a_row[DS_COLUMN_MAP[DS_PERSIL_EDIT][4]] = nib
                        a_row[DS_COLUMN_MAP[DS_PERSIL_EDIT][5]] = luas_round
                        a_row[DS_COLUMN_MAP[DS_PERSIL_EDIT][6]] = poli["batas"]
                        a_row[DS_COLUMN_MAP[DS_PERSIL_EDIT][7]] = teks
                        a_row[DS_COLUMN_MAP[DS_PERSIL_EDIT][8]] = "Tunggal"
                        a_row[DS_COLUMN_MAP[DS_PERSIL_EDIT][9]] = height
                        a_row[DS_COLUMN_MAP[DS_PERSIL_EDIT][10]] = orientation
                        self._ds_persil["PersilEdit"].append(a_row)
                else:
                    continue

    def _refresh_status(self):
        msg_status = ""
        label = self.cmb_data_view.currentText()
        if label == "Persil Baru":
            self._current_parcel_table = "PersilBaru"
            msg_status = "Jumlah Persil Baru"
        elif label == "Persil Edit":
            self._current_parcel_table = "PersilEdit"
            msg_status = "Jumlah Persil Edit"
        elif label == "Apartemen Baru":
            self._current_parcel_table = "ApartemenBaru"
            msg_status = "Jumlah Apartemen"
        elif label == "Apartemen Edit":
            self._current_parcel_table = "ApartemenEdit"
            msg_status = "Jumlah Apartemen"

        self._populate_dgv_parcel()
        
        jml_all = str(self.dgv_parcel.rowCount())
        right_status = f"{msg_status} : {jml_all}"
        self.writeRightStatus.emit(right_status)

    def _populate_dgv_parcel(self):
        self.dgv_parcel.setRowCount(0)
        data = self._ds_persil[self._current_parcel_table]
        if not data:
            return
        columns = [
            col
            for col in data[0].keys()
            if col not in ["BOUNDARY", "LUAST", "TEXT"]
        ]
        self.dgv_parcel.setColumnCount(len(columns))
        self.dgv_parcel.setHorizontalHeaderLabels(columns)

        for item in data:
            pos = self.dgv_parcel.rowCount()
            self.dgv_parcel.insertRow(pos)

            for index, col in enumerate(columns):
                self.dgv_parcel.setItem(
                    pos, index, QtWidgets.QTableWidgetItem(str(item[col]))
                )
    
    def _set_context_menu_visiblity(self):
        if self._current_parcel_table == "PersilBaru":
            pass
            # TODO: miEditedParcel
            # TODO: miNewParcel
            # TODO: btnDelete
        else:
            # TODO: miEditedParcel
            # TODO: miNewParcel
            # TODO: btnDelete
            pass
        # TODO: implement context_menu_visiblity
        pass

    def _drop_event(self, event):
        row_index_from = self.dgv_parcel.currentRow()
        row_index_to = self.dgv_parcel.rowAt(event.pos().y())
        print("Drop from " + str(row_index_from) + " into row " + str(row_index_to))
        # event.accept()
        if not row_index_to == -1 and not row_index_from == row_index_to:
            oid = self.dgv_parcel.item(row_index_from,0).text()
            if (oid == None or oid == "None" or oid == ""):
                QtWidgets.QMessageBox.warning(
                    None, "GeoKKP", "Persil asal harus punya batas geometri"
                    )
                return
            source_parcel = self._select_row(self._ds_persil[self._current_parcel_table], "OID", oid)
            print(f"source_parcel = {source_parcel}")

            luas = source_parcel["AREA"]
            target_parcel = {}
            geom_t = source_parcel["TEXT"]

            reg = str(self.dgv_parcel.item(row_index_from,1).text())
            print(reg)
            if not (reg == None or reg == "None" or reg == ""):
                QtWidgets.QMessageBox.warning(
                    None, "GeoKKP","Persil tekstual tidak bisa digabung!"
                    )
                return

            regid = self.dgv_parcel.item(row_index_to,1).text()
            oid_to = self.dgv_parcel.item(row_index_to,0.).text()
            if regid:
                target_parcel = self._select_row(self._ds_persil[self._current_parcel_table],"REGID",regid)
            else:
                target_parcel = self._select_row(self._ds_persil[self._current_parcel_table],"OID",oid_to)
            
            if target_parcel["BOUNDARY"]:
                merge_geom = {}
                
                merge_geom["SdoElemInfo"] = [None]*((len(target_parcel["BOUNDARY"]["SdoElemInfo"]))+(len(source_parcel["BOUNDARY"]["SdoElemInfo"])))
                for i,item in enumerate(target_parcel["BOUNDARY"]["SdoElemInfo"]):        
                    merge_geom["SdoElemInfo"][i] = (item)

                # CHECK!
                merge_geom["SdoElemInfo"][0 + len(target_parcel["BOUNDARY"]["SdoElemInfo"])] = source_parcel["BOUNDARY"]["SdoElemInfo"][0] + len(source_parcel["BOUNDARY"]["SdoOrdinates"])
                merge_geom["SdoElemInfo"][1 + len(target_parcel["BOUNDARY"]["SdoElemInfo"])] = source_parcel["BOUNDARY"]["SdoElemInfo"][1]
                merge_geom["SdoElemInfo"][2 + len(target_parcel["BOUNDARY"]["SdoElemInfo"])] = source_parcel["BOUNDARY"]["SdoElemInfo"][2]
                
                print(merge_geom["SdoElemInfo"])
                merge_geom["SdoGtype"] = 2003
                merge_geom["SdoSRID"] = source_parcel["BOUNDARY"]["SdoSRID"]
                merge_geom["SdoSRIDAsInt"] = source_parcel["BOUNDARY"]["SdoSRIDAsInt"]
                
                
                coordinates = [] 
                for i,item in enumerate(target_parcel["BOUNDARY"]["SdoOrdinates"]):
                    coordinates.append(item)
                for i,item in enumerate(source_parcel["BOUNDARY"]["SdoOrdinates"]):
                    coordinates.append(item)
                merge_geom["SdoOrdinates"] = coordinates

                print(merge_geom["SdoOrdinates"])

                geom_t = target_parcel["TEXT"]
                luas += target_parcel["AREA"]

            else:
                merge_geom = source_parcel["BOUNDARY"]
                target_parcel["LABEL"] = source_parcel["LABEL"]
            
            target_parcel["OID"] = oid
            target_parcel["AREA"] = str(luas)
            target_parcel["BOUNDARY"] = merge_geom
            target_parcel["TEXT"] = geom_t
            target_parcel["KETERANGAN"] = "Gabungan"
            target_parcel["HEIGHT"] = source_parcel["HEIGHT"]
            target_parcel["ORIENTATION"] = source_parcel["ORIENTATION"]

            if "baru" in self._current_parcel_table.lower():
                print(self._ds_persil[self._current_parcel_table])
                if self.dgv_parcel.item(row_index_to,1).text():
                    target_parcel["REGID"] = self.dgv_parcel.item(row_index_to,1).text()
                elif self.dgv_parcel.item(row_index_from,1).text():
                    target_parcel["REGID"] = self.dgv_parcel.item(row_index_from,1).text()

            print(target_parcel)

            del source_parcel
            self._ds_persil[self._current_parcel_table].pop(row_index_from)
            self._refresh_status()


    
    def _select_row(self, dataset, key, value):
        a = []
        for i,list in enumerate(dataset):
            if dataset[i][key] == value:
                 a.append(dataset[i])
            if a:
                return a[0]
            

    def _btn_validasi_clicked(self):
        valid = True
        msg = ""
        if not self._validate_extent():
            if self._tipe_sistem_koordinat == "TM3":
                msg = "\nKoordinat diluar TM3! Koordinat Harus diantara [32000, 282000] dan [368000, 2166000]"
            else:
                msg = "\nKoordinat diluar boundary! Koordinat Harus diantara [-2200000, -2200000] dan [2200000, 2200000]"
            valid = False
        
        if len(self._new_parcels) > 1:
            for row in self._ds_persil[DS_PERSIL_EDIT]:
                if not row["BOUNDARY"]:
                    valid = False
                    msg = "\nAda Persil Edit yang tidak memiliki geometri!"
                    break
                if not row["REGID"]:
                    valid = False
                    msg = "\nAda Persil Edit yang tidak memiliki regid!"
                    break
        
        if valid:
            self.btn_proses.setEnabled(True)
            self.writeLeftStatus.emit("Lakukan integrasi")
            # set status color black
        else:
            self.writeLeftStatus.emit("Ada kesalahan, cek error log")
            self.writeErrorLog.emit(msg)
            self.changeTabIndex.emit(1)
            # set status color red

    
    def _validate_extent(self):
        min_x = 0
        min_y = 0
        max_x = 0
        max_y = 0
        for layer in self._parent._submit_layers:
            if not layer.name().startswith("(020100)"):
                continue
            extent = layer.extent()
            min_x = min(min_x, extent.xMinimum())
            min_y = min(min_y, extent.yMinimum())
            max_x = max(max_x, extent.xMaximum())
            max_y = max(max_y, extent.xMaximum())

        if self._tipe_sistem_koordinat == "TM3":
            return not (
                min_x < 32000 - 10000
                and max_x > 368000 + 10000
                and min_y < 282000 - 10000
                and max_y > 2166000 + 10000
            )
        else:
            return not (
                min_x < -2200000
                and max_x > 2200000
                and min_y < -2200000
                and max_y > 2200000
            )
    
    def _chb_tm3_state_changed(self):
        if self.chb_tm3.isChecked():
            self._tipe_sistem_koordinat = "TM3"
        else:
            self._tipe_sistem_koordinat = "NonTM3"

    def _btn_proses_clicked(self):
        self.btn_proses.setEnabled(False)
        self.btn_validasi.setEnabled(False)

        sdo_to_submit = {}

        lines = self._fill_entity_data_table()
        texts = self._fill_text_entity()
        # TODO: self._fill_point_entity()
        # TODO: self._fill_dimensi_entity()

        lspe = [] # list sdo persil edit
        
        # TODO: check the data type
        for row in self._ds_persil[DS_PERSIL_EDIT]:
            spe = {}
            spe["OID"] = row["OID"]
            spe["REGID"] = row["REGID"]
            spe["NIB"] = row["NIB"]
            spe["Luast"] = float(row["LUAST"]) if row["LUAST"] else 0
            spe["Label"] = row["LABEL"]
            spe["Area"] = float(row["AREA"].replace(",", ".")) if row["AREA"] else 0
            spe["Boundary"] = row["BOUNDARY"]
            spe["Text"] = row["TEXT"]
            spe["Keterangan"] = row["KETERANGAN"]
            spe["Height"] = row["HEIGHT"]
            spe["Orientation"] = row["ORIENTATION"]

            lspe.append(spe)
        
        sdo_to_submit["PersilEdit"] = lspe
        sdo_to_submit["Garis"] = lines
        sdo_to_submit["Teks"] = texts

        print(f"sdo_to_submit={sdo_to_submit}")
        
        self._run_integration(sdo_to_submit)
    
    def _fill_entity_data_table(self):
        layers = self._parent._submit_layers

        lines = []
        for layer in layers:
            if (
                isinstance(layer, QgsVectorLayer)
                and "line" not in QgsWkbTypes.displayString(layer.wkbType()).lower()
            ):
                continue

            code, object_type = self.identify_layer_object(layer.name())
            if not code and not object_type:
                continue
            object_type = object_type if object_type else "GarisLain"

            features = layer.getFeatures()
            for feature in features:
                identifier = f"{layer.id()}|{feature.id()}".encode("utf-8")
                objectid = hashlib.md5(identifier).hexdigest().upper()

                line = self._get_sdo_linestring(feature)

                if line and (code.startsWith("08") or object_type == "GarisLain"):
                    row = {"Key": objectid, "Type": object_type, "Line": line}
                    lines.append(row)
        return lines        
    
    def identify_layer_object(self, layer_name):
        layer_raw = layer_name.split(") ")
        if len(layer_raw) != 2:
            return None, None

        code_raw, object_raw = layer_raw

        try:
            code = code_raw.replace("(", "")[-1]
        except:
            code = None

        try:
            object_type = object_raw.split("/")[0].replace(" ", "")
        except:
            object_type = None

        return code, object_type

    def _fill_text_entity(self):
        layers = self._parent._submit_layers

        points = []
        for layer in layers:
            if (
                isinstance(layer, QgsVectorLayer)
                and "point" not in QgsWkbTypes.displayString(layer.wkbType()).lower()
            ):
                continue

            code, object_type = self.identify_layer_object(layer.name())
            if not code and not object_type:
                continue

            object_type = object_type if object_type else "TeksLain"

            features = layer.getFeatures()
            for feature in features:
                identifier = f"{layer.id()}|{feature.id()}".encode("utf-8")
                objectid = hashlib.md5(identifier).hexdigest().upper()

                point = get_sdo_point(feature)

                label = feature.attribute("label") if feature.attribute("label") else ""
                height = (
                    float(feature.attribute("height"))
                    if feature.attribute("height")
                    else 0
                )
                orientation = (
                    float(feature.attribute("rotation"))
                    if feature.attribute("rotation")
                    else 0
                )

                if point and (code.startsWith("08") or object_type == "TeksLain"):
                    row = {
                        "Key": objectid,
                        "Type": object_type,
                        "Height": height,
                        "Orientation": orientation,
                        "Label": label,
                        "Position": point,
                    }
                    points.append(row)
        return points

    def _run_integration(self,sdo_to_submit):
        sd = {}

        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        user_id = pegawai["userId"] if "userId" in pegawai else ""

        sts = sdo_to_submit
        response = endpoints.update_geometri_persil_legal_sdo(
            kantor_id = self._kantor_id,
            nama_petugas = user_id,
            sts = sts,
            gugus_id = self._old_gugus_id,
            user_id = user_id,
        )
        ds = json.loads(response.content)

        print(ds)

        if len(ds) == 0:
            sd["status"] = False
            sd["autoClosed"] = True
            sd["errorMessage"] = "Penyimpanan gagal Surat Ukur / Gambar Situasi!\nCek service berkas spatial di server sudah dijalankan!"
            self.processed.emit(sd)
            return
        
        if len(ds["Error"]) > 0:
            sd["status"] = False
            sd["autoClosed"] = True
            sd["errorMessage"] = str(ds["Error"][0]["message"])
            self.processed.emit(sd)
            return
        
        self._new_parcels = []
        
        result_oid_map = {}
        for row in ds["PersilBaru"]:
            result_oid_map[row["oid"]] = row["nib"]

        for layer in self._parent._current_layers:
            try:
                layer.id()
            except RuntimeError:
                continue
            field_index = layer.fields().indexOf("label")
            print("field_index", field_index)
            features = layer.getFeatures()
            for feature in features:
                identifier = f"{layer.id()}|{feature.id()}".encode("utf-8")
                objectid = hashlib.md5(identifier).hexdigest().upper()
                print("objectid", objectid)
                if objectid not in result_oid_map:
                    continue

                layer.startEditing()
                layer.changeAttributeValue(
                    feature.id(), field_index, result_oid_map[objectid]
                )
                layer.commitChanges()
        
        sd["status"] = True
        self.processed.emit(sd)





