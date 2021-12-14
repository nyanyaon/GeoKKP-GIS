import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from ...utils import (
    readSetting,
    storeSetting,
    get_project_crs,
    sdo_to_layer
)
from ...api import endpoints
from ...memo import app_state
from ...topology import quick_check_topology
from ...desain_persil import DesainPersil

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../../../ui/workpanel/tab_rutin.ui'))


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class TabRutin(QtWidgets.QWidget, FORM_CLASS):
    """ Dialog for Peta Bidang """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabRutin, self).__init__(parent)
        self.setupUi(self)
        self.project = QgsProject

        self.current_berkas = None
        self.current_layers = []
        
        self.current_settings = self._get_current_settings()

        self.btn_rutin_cari.clicked.connect(self.cari_berkas_rutin)
        self.btn_rutin_mulai.clicked.connect(self.mulai_berkas_rutin)
        self.btn_rutin_simpan.clicked.connect(self.simpan_berkas_rutin)
        self.btn_rutin_tutup.clicked.connect(self.tutup_berkas_rutin)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()
    
    def setup_workpanel(self):
        pass

    def _get_current_settings(self):
        kantor = readSetting('kantorterpilih')
        provinsi = readSetting('provinsiterpilih')
        kabupaten = readSetting('kabupatenterpilih')
        kecamatan = readSetting('kecamatanterpilih')
        kelurahan = readSetting('kelurahanterpilih')

        self.current_settings = {
            "kantor": kantor,
            "provinsi": provinsi,
            "kabupaten": kabupaten,
            "kecamatan": kecamatan,
            "kelurahan": kelurahan
        }
        return self.current_settings 

    def cari_berkas_rutin(self):
        # TODO implement pagiation
        self._get_current_settings()
        if not self.current_settings["kantor"]:
            return

        no_berkas = self.input_rutin_no_berkas.text()
        th_berkas = self.input_rutin_th_berkas.text()

        response = endpoints.get_berkas(
            nomor_berkas=no_berkas,
            tahun_berkas=th_berkas,
            kantor_id=self.current_settings["kantor"]["kantorID"],
            tipe_kantor_id=str(self.current_settings["kantor"]["tipeKantorId"]))
        response_json = json.loads(response.content)
        self.populate_berkas_rutin(response_json["BERKASSPATIAL"])

    def populate_berkas_rutin(self, data):
        self.table_rutin.setRowCount(0)
        for item in data:
            pos = self.table_rutin.rowCount()
            self.table_rutin.insertRow(pos)

            self.table_rutin.setItem(pos, 0, QtWidgets.QTableWidgetItem(str(item["NOMOR"])))
            self.table_rutin.setItem(pos, 1, QtWidgets.QTableWidgetItem(str(item["TAHUN"])))
            self.table_rutin.setItem(pos, 2, QtWidgets.QTableWidgetItem(item["OPERASISPASIAL"]))

    def mulai_berkas_rutin(self):
        if self.current_berkas is not None:
            QtWidgets.QMessageBox.critical(None, 'Tutup berkas', 'Tutup berkas yang sedang dikerjakan terlebih dahulu')
            return

        selected_row = self.table_rutin.selectedItems()
        no_berkas = selected_row[0].text()
        th_berkas = selected_row[1].text()
        username = app_state.get("username").value

        response_start_berkas = endpoints.start_berkas_spasial(
            nomor_berkas=no_berkas,
            tahun_berkas=th_berkas,
            kantor_id=self.current_settings["kantor"]["kantorID"],
            tipe_kantor_id=str(self.current_settings["kantor"]["tipeKantorId"]),
            username=username)
        response_start_berkas_json = json.loads(response_start_berkas.content)
        self.current_berkas = response_start_berkas_json
        print(self.current_berkas)

        if self.current_berkas["valid"]:
            lanjut_blanko = True
            is_e_sertifikat = readSetting("isESertifikat")
            if is_e_sertifikat and self.tipe_kantor_id not in ["1", "2"]:
                response_blanko = endpoints.get_blanko_by_berkas_id(berkas_id=self.current_berkas["BERKASID"])
                response_blanko_json = json.loads(response_blanko.content)
                if len(response_blanko_json["BLANKO"]) > 0:
                    lanjut_blanko = True
                else:
                    lanjut_blanko = False
            
            if self.current_berkas["kodeSpopp"] in [
                "SPOPP-3.46.3",
                "SPOPP-3.09.9",
                "SPOPP-3.09.1",
                "SPOPP-3.09.2",
                "SPOPP-3.18.1",
                "SPOPP-3.12.1"
            ] or lanjut_blanko :
                if self.current_berkas["newGugusId"] != "":
                    if self.current_berkas["tipeBerkas"] != "DAG":
                        gugus_id = self.current_berkas["newGugusId"]
                        response_spatial_sdo = endpoints.get_spatial_document_sdo(gugus_ids=[gugus_id])
                        response_spatial_sdo_json = json.loads(response_spatial_sdo.content)
                        print(response_spatial_sdo_json.keys())

                        epsg = get_project_crs()
                        layer = sdo_to_layer(
                            response_spatial_sdo_json["geoKkpPolygons"],
                            name="Batas Persil",
                            symbol='simplepersil.qml',
                            crs=epsg
                        )
                        self.current_layers.append(layer)
                else:
                    if self.current_berkas["oldGugusIds"]:
                        gugus_ids = [str(id) for id in self.current_berkas["oldGugusIds"]]
                        response_spatial_sdo = endpoints.get_spatial_document_sdo(
                            gugus_ids=[gugus_id], 
                            include_riwayat=True
                        )
                        response_spatial_sdo_json = json.loads(response_spatial_sdo.content)
                        print(response_spatial_sdo_json)
                        epsg = get_project_crs()
                        layer = sdo_to_layer(
                            response_spatial_sdo_json["geoKkpPolygons"],
                            name="Batas Persil",
                            symbol='simplepersil.qml',
                            crs=epsg
                        )
                        self.current_layers.append(layer)
                    else:
                        # TODO: Add new blank layer
                        pass

                self.btn_rutin_cari.setDisabled(True)
                self.btn_rutin_mulai.setDisabled(True)
                self.input_rutin_no_berkas.setDisabled(True)
                self.input_rutin_th_berkas.setDisabled(True)

                if self.current_berkas["tipeBerkas"] == "DAG":
                    # TODO: Add input gambar denah
                    pass
            else:
                QtWidgets.QMessageBox.warning(None, "Perhatian", "Lakukan registrasi blanko terlebih dahulu")
        else:
            message = "\n".join(self.current_berkas["errorStack"])
            QtWidgets.QMessageBox.critical(None, "Error", message)

    def simpan_berkas_rutin(self):
        if self.current_berkas and self.current_berkas["tipeBerkas"] == "DAG":
            # TODO: Add input gambar denah
            return

        topo_error_message = []
        for layer in self.current_layers:
            valid, num = quick_check_topology(layer)
            if not valid:
                message = f"Ada {num} topology error di layer {layer.name()}"
                topo_error_message.append(message)

        if topo_error_message:
            QtWidgets.QMessageBox.warning(None, "Perhatian", topo_error_message.join("\n"))
            return

        # _create_dataset_integration save to self
        gambar_ukur_id = self.current_berkas["gambarUkurs"] if self.current_berkas["gambarUkurs"] else ""
        desain_persil = DesainPersil(
            nomor_berkas=self.current_berkas["nomorBerkas"],
            tahun_berkas=self.current_berkas["tahunBerkas"],
            kantor_id=self.current_settings["kantor"]["kantorID"],
            tipe_kantor_id=str(self.current_settings["kantor"]["tipeKantorId"]),
            tipe_berkas=self.current_berkas["tipeBerkas"],
            gambar_ukur_id=gambar_ukur_id,
            kelurahan_id=self.current_settings["kelurahan"]["DESAID"],
            tipe_sistem_koordinat="3",
            new_parcel_number=self.current_berkas["newParcelNumber"],
            new_apartment_number=self.current_berkas["newApartmentNumber"],
            new_parcels=self.current_berkas["newParcels"],
            old_parcels=self.current_berkas["oldParcels"],
            new_apartments=self.current_berkas["newApartments"],
            old_apartments=self.current_berkas["oldApartments"]
        )
        desain_persil.show()

    def _create_dataset_integration(self):
        dataset_integration = {
            "PersilMati": [], # REGID
            "Poligon": [], # Key, Type, Label, Height, Orientation, Boundary, Text
            "Garis": [], # KEY, TYPE, LINE
            "Teks": [], # Key, Type, Height, Orientation, Label, Position
            "Titik": [], # Key, Type, PointOrientation, TextOrientation, Scale, height, Label, PointPosition, TextPosition
            "Dimensi": [], # Key, Type, Line, InitialPoint, Label, Endpoint, Initialorientation, Labelorientation, Endorientation, Height, Label 
        }

    def tutup_berkas_rutin(self):
        current_settings = self._get_current_settings()
        if not current_settings["kantor"]:
            return

        response_tutup_berkas = endpoints.stop_berkas(
            nomor_berkas=self.current_berkas["nomorBerkas"],
            tahun_berkas=self.current_berkas["tahunBerkas"],
            kantor_id=current_settings["kantor"]["kantorID"]
        )
        response_tutup_berkas_json = json.loads(response_tutup_berkas.content)
        if response_tutup_berkas_json:
            self.current_berkas = None
            layer_ids = [layer.id() for layer in self.current_layers]
            self.project.instance().removeMapLayers(layer_ids)
            iface.mapCanvas().refresh()
            self.current_layers = []
            self.btn_rutin_mulai.setDisabled(False)