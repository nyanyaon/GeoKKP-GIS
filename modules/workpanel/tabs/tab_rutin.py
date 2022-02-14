import os
import json
import hashlib

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from ...utils import (
    readSetting,
    get_project_crs,
    sdo_to_layer,
    get_layer_config,
    add_layer
)
from ...models.dataset import Dataset

from ...api import endpoints
from ...memo import app_state
from ...topology import quick_check_topology
from ...desain_persil import DesainPersil
from ...informasi_persil import InformasiPersil
from ...link_di302 import LinkDI302
from ...link_di302a import LinkDI302A
from ...input_denah import InputDenah

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../../ui/workpanel/tab_rutin.ui")
)


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class TabRutin(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabRutin, self).__init__(parent)
        self.setupUi(self)

        self._start = 0
        self._limit = 20
        self._count = -1
        self._berkas_id = ""

        self._txt_nomor = ""
        self._txt_tahun = ""
        self._kantor_id = ""
        self._tipe_kantor_id = ""
        self._nomor_berkas = ""
        self._tahun_berkas = ""
        self._tipe_berkas = ""
        self._ganti_desa = "0"
        self._kode_sppop = ""
        self._wilayah_id = ""
        self._gambar_ukur_id = ""
        self._new_gugus_id = ""
        self._new_parcel_number = ""
        self._new_apartment_number = ""

        self._new_parcels = []
        self._old_parcels = []
        self._del_parcels = []
        self._new_apartments = []
        self._old_apartments = []
        self._del_apartments = []
        self._gambar_ukurs = []
        self._error_stack = []
        self._old_gugus_ids = []

        self._parcel_ready_to_map = []
        self._process_available = False

        self._sts = None
        self._ent_dataset = None

        self.project = QgsProject
        self._set_initial_state()

        self.current_berkas = None
        self.current_layers = []
        self._sistem_koordinat = ""

        self.btn_rutin_cari.clicked.connect(self._handle_cari)
        self.btn_rutin_mulai.clicked.connect(self.mulai_berkas_rutin)
        self.btn_rutin_informasi.clicked.connect(self._handle_informasi_berkas_rutin)
        self.btn_rutin_simpan.clicked.connect(self.simpan_berkas_rutin)
        self.btn_rutin_tutup.clicked.connect(self.tutup_berkas_rutin)
        self.btn_rutin_selesai.clicked.connect(self.selesai_berkas_rutin)
        self.btn_first.clicked.connect(self._handle_first_page)
        self.btn_last.clicked.connect(self._handle_last_page)
        self.btn_next.clicked.connect(self._handle_next_page)
        self.btn_prev.clicked.connect(self._handle_prev_page)
        self.btn_rutin_di302.clicked.connect(self._handle_update_di302)

    def _reset_variable(self):
        self._txt_nomor = ""
        self._txt_tahun = ""
        self._kantor_id = ""
        self._tipe_kantor_id = ""
        self._nomor_berkas = ""
        self._tahun_berkas = ""
        self._tipe_berkas = ""
        self._ganti_desa = "0"
        self._kode_sppop = ""
        self._wilayah_id = ""
        self._gambar_ukur_id = ""
        self._new_gugus_id = ""
        self._new_parcel_number = ""
        self._new_apartment_number = ""

        self._new_parcels = []
        self._old_parcels = []
        self._del_parcels = []
        self._new_apartments = []
        self._old_apartments = []
        self._del_apartments = []
        self._gambar_ukurs = []
        self._error_stack = []
        self._old_gugus_ids = []

        self._parcel_ready_to_map = []
        self.setup_workpanel()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()

    def setup_workpanel(self):
        kantor = readSetting("kantorterpilih")

        if not kantor:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih lokasi kantor lebih dahulu"
            )
            return

        self._kantor_id = kantor["kantorID"]
        self._tipe_kantor_id = str(kantor["tipeKantorId"])

    def _set_initial_state(self):
        self.btn_rutin_cari.setDisabled(False)
        self.btn_rutin_mulai.setDisabled(False)
        self.btn_rutin_simpan.setDisabled(True)
        self.btn_rutin_informasi.setDisabled(True)
        self.btn_rutin_di302.setDisabled(True)
        self.btn_rutin_layout.setDisabled(True)
        self.btn_rutin_tutup.setDisabled(True)
        self.btn_rutin_selesai.setDisabled(True)
        self.input_rutin_no_berkas.setDisabled(False)
        self.input_rutin_th_berkas.setDisabled(False)

    def _cari_berkas_rutin(self):
        response = endpoints.get_berkas(
            nomor_berkas=self._txt_nomor,
            tahun_berkas=self._txt_tahun,
            kantor_id=self._kantor_id,
            tipe_kantor_id=self._tipe_kantor_id,
            start=self._start,
            limit=self._limit,
            count=self._count,
        )
        response_json = Dataset(response.content)

        print("cari", response_json)
        self._setup_pagination(response_json)
        response_json.render_to_qtable_widget("BERKASSPATIAL", self.table_rutin, [0, 4])

    def _setup_pagination(self, data):
        if self._count == -1:
            self._count = data["JUMLAHTOTAL"].rows[0]["COUNT(1)"]

        if self._count > 0:
            if self._start + self._limit >= self._count:
                page = (
                    f"{self._start + 1} - {self._count} dari {self._count}"
                )
                self.btn_next.setDisabled(True)
                self.btn_last.setDisabled(True)
            else:
                page = f"{self._start + 1} - {self._start + self._limit} dari {self._count}"
                self.btn_next.setDisabled(False)
                self.btn_last.setDisabled(False)
        else:
            page = "0"
            self.btn_next.setDisabled(True)
            self.btn_prev.setDisabled(True)
            self.btn_first.setDisabled(True)
            self.btn_last.setDisabled(True)

        prev_btn_disabled = self._start == 0 or self._count == 0
        self.btn_prev.setDisabled(prev_btn_disabled)
        self.btn_first.setDisabled(self._start == 0)
        self.input_page.setText(page)

    def _handle_first_page(self):
        self._start = 0
        self._cari_berkas_rutin()

    def _handle_next_page(self):
        self._start += self._limit
        self._cari_berkas_rutin()

    def _handle_prev_page(self):
        self._start -= self._limit
        self._cari_berkas_rutin()

    def _handle_last_page(self):
        self._start = (self._count // self._limit) * self._limit
        if self._start >= self._count:
            self._start -= self._limit
        self._cari_berkas_rutin()

    def _handle_cari(self):
        self._start = 0
        self._count = -1
        self._txt_nomor = self.input_rutin_no_berkas.text()
        self._txt_tahun = self.input_rutin_th_berkas.text()

        self.btn_first.setDisabled(False)
        self.btn_last.setDisabled(False)

        self._cari_berkas_rutin()

    def mulai_berkas_rutin(self):
        self.table_rutin.setColumnHidden(0, False)
        selected_row = self.table_rutin.selectedItems()
        self.table_rutin.setColumnHidden(0, True)
        self._nomor_berkas = selected_row[1].text()
        self._tahun_berkas = selected_row[2].text()
        self._tipe_berkas = selected_row[3].text()
        self._berkas_id = selected_row[0].text()
        username = app_state.get("username").value

        response_start_berkas = endpoints.start_berkas_spasial(
            nomor_berkas=self._nomor_berkas,
            tahun_berkas=self._tahun_berkas,
            kantor_id=self._kantor_id,
            tipe_kantor_id=self._tipe_kantor_id,
            username=username,
        )
        bs = json.loads(response_start_berkas.content)
        print(bs)
        if bs["valid"]:
            lanjut_blanko = True
            is_e_sertifikat = readSetting("isESertifikat")
            response = endpoints.get_is_e_sertifikat(self._kantor_id)
            print('e_cert', is_e_sertifikat)
            print('e_cert2', response.content)
            print('tipe_kantor', self._tipe_kantor_id)

            if not is_e_sertifikat and self._tipe_kantor_id not in ["1", "2"]:
                response_blanko = endpoints.get_blanko_by_berkas_id(
                    berkas_id=bs["berkasId"]
                )
                response_blanko_json = json.loads(response_blanko.content)
                print('blanko', response_blanko_json)
                if len(response_blanko_json["BLANKO"]) > 0:
                    lanjut_blanko = True
                else:
                    lanjut_blanko = False

            if (
                bs["kodeSpopp"]
                in [
                    "SPOPP-3.46.3",
                    "SPOPP-3.09.9",
                    "SPOPP-3.09.1",
                    "SPOPP-3.09.2",
                    "SPOPP-3.18.1",
                    "SPOPP-3.12.1",
                ]
                or lanjut_blanko
            ):
                self._wilayah_id = bs["wilayahId"]
                self._new_parcel_number = bs["newParcelNumber"]
                self._new_apartment_number = bs["newApartmentNumber"]
                self._new_gugus_id = bs["newGugusId"]
                self._ganti_desa = bs["gantiDesa"]
                self._kode_sppop = bs["kodeSpopp"]

                if bs["gambarUkurs"]:
                    self._gambar_ukurs = bs["gambarUkurs"]
                if bs["oldParcels"]:
                    self._old_parcels = bs["oldParcels"]
                if bs["delParcels"]:
                    self._del_parcels = bs["delParcels"]
                if bs["newParcels"]:
                    self._new_parcels = bs["newParcels"]
                if bs["oldApartments"]:
                    self._old_apartments = bs["oldApartments"]
                if bs["delApartments"]:
                    self._del_apartments = bs["delApartments"]
                if bs["newApartments"]:
                    self._new_apartments = bs["newApartments"]
                if bs["oldGugusIds"]:
                    self._old_gugus_ids = bs["oldGugusIds"]

                if self._new_gugus_id:
                    if self._tipe_berkas != "DAG":
                        gugus_id = str(self._new_gugus_id)
                        # TODO: refactor to draw entity
                        self._load_berkas_spasial([gugus_id], False)
                else:
                    if self._old_gugus_ids:
                        gugus_ids = [
                            str(id) for id in self._old_gugus_ids
                        ]
                        self._load_berkas_spasial(gugus_ids, True)
                    else:
                        layer_config = get_layer_config("020100")
                        add_layer(
                            layer_config["Nama Layer"],
                            layer_config["Tipe Layer"],
                            layer_config["Style Path"],
                            layer_config["Attributes"][0]
                        )

                self._set_button(True)
                self._process_available = True
                self.input_rutin_no_berkas.setText(self._nomor_berkas)
                self.input_rutin_th_berkas.setText(self._tahun_berkas)
                self.input_rutin_no_berkas.setDisabled(True)
                self.input_rutin_th_berkas.setDisabled(True)
                self.btn_rutin_mulai.setDisabled(True)

                self.btn_rutin_cari.setDisabled(True)

                if self._tipe_berkas != "DAG":
                    # TODO: refactor to static storage
                    self._sistem_koordinat = "TM3"
                else:
                    self.input_gambar_denah()
            else:
                QtWidgets.QMessageBox.warning(
                    None, "Perhatian", "Lakukan registrasi blanko terlebih dahulu"
                )
        else:
            message = "\n".join(bs["errorStack"])
            QtWidgets.QMessageBox.critical(None, "Error", message)

    def _set_button(self, enabled):
        disabled = not enabled
        self.btn_rutin_simpan.setDisabled(disabled)
        self.btn_rutin_informasi.setDisabled(disabled)
        self.btn_rutin_tutup.setDisabled(disabled)

    def _load_berkas_spasial(self, gugus_ids, riwayat=False):
        response_spatial_sdo = endpoints.get_spatial_document_sdo(
            gugus_ids=gugus_ids, include_riwayat=riwayat
        )
        response_spatial_sdo_json = json.loads(response_spatial_sdo.content)
        print(response_spatial_sdo_json)

        if not response_spatial_sdo_json["status"]:
            QtWidgets.QMessageBox.critical(None, "Error", "Proses Unduh Geometri gagal")
            return

        epsg = get_project_crs()
        if response_spatial_sdo_json["geoKkpPolygons"]:
            print(response_spatial_sdo_json["geoKkpPolygons"][0])

            if response_spatial_sdo_json["geoKkpPolygons"]:
                layer_config = get_layer_config("020100")
                print(layer_config)
                layer = sdo_to_layer(
                    response_spatial_sdo_json["geoKkpPolygons"],
                    name=layer_config["Nama Layer"],
                    symbol=layer_config["Style Path"],
                    crs=epsg,
                    coords_field="boundary",
                )
                self.current_layers.append(layer)

    def simpan_berkas_rutin(self):
        if self._tipe_berkas == "DAG":
            self.input_gambar_denah()
            return

        # TODO: handle topology logic as layer
        topo_error_message = []
        for layer in self.current_layers:
            valid, num = quick_check_topology(layer)
            print(valid, num)
            if not valid:
                message = f"Ada {num} topology error di layer {layer.name()}"
                topo_error_message.append(message)

        if topo_error_message:
            QtWidgets.QMessageBox.warning(
                None, "Perhatian", "\n".join(topo_error_message)
            )
            return

        self._create_dataset_integration()

        g_ukur_id = (
            str(self._gambar_ukurs[0])
            if self._gambar_ukurs
            else ""
        )
        pd = DesainPersil(
            parent=self,
            nomor_berkas=self._nomor_berkas,
            tahun_berkas=self._tahun_berkas,
            kantor_id=self._kantor_id,
            tipe_kantor_id=self._tipe_kantor_id,
            tipe_berkas=self._tipe_berkas,
            gambar_ukur_id=g_ukur_id,
            wilayah_id=self._wilayah_id,
            tipe_sistem_koordinat="TM3",
            new_parcel_number=self._new_parcel_number,
            new_apartment_number=self._new_apartment_number,
            new_parcels=self._new_parcels,
            old_parcels=self._old_parcels,
            new_apartments=self._new_apartments,
            old_apartments=self._old_apartments,
        )
        pd.show()
        pd.integrasi.connect(self._process_integration)

    def _process_integration(self, payload):
        if not payload["ds_parcel"]:
            return

        self._wilayah_id = payload["wilayah_id"]
        self._sts = {}

        list_data = []
        print("integrasi", payload)
        for data in payload["ds_parcel"]["PersilBaru"]:
            temp = {
                "OID": data["OID"],
                "Label": data["LABEL"],
                "Area": float(str(data["AREA"]).replace(",", ".")),
                "Boundary": data["BOUNDARY"],
                "Text": data["TEXT"],
                "Keterangan": data["KETERANGAN"],
                "Height": data["HEIGHT"],
                "Orientation": data["ORIENTATION"],
            }
            list_data.append(temp)
        self._sts["PersilBaru"] = list_data

        list_data = []
        for data in payload["ds_parcel"]["PersilEdit"]:
            temp = {
                "OID": data["OID"],
                "REGID": data["REGID"],
                "NIB": data["NIB"],
                "Luast": float(str(data["LUAST"]).replace(",", ".")),
                "Label": data["LABEL"],
                "Area": float(str(data["AREA"]).replace(",", ".")),
                "Boundary": data["BOUNDARY"],
                "Text": data["TEXT"],
                "Keterangan": data["KETERANGAN"],
                "Height": data["HEIGHT"],
                "Orientation": data["ORIENTATION"],
            }
            list_data.append(temp)
        self._sts["PersilEdit"] = list_data

        list_data = []
        for data in payload["ds_parcel"]["PersilInduk"]:
            if data["OID"] is None:
                continue

            temp = {
                "OID": data["OID"],
                "REGID": data["REGID"],
                "NIB": data["NIB"],
                "Luast": float(str(data["LUAST"]).replace(",", ".")),
                "Label": data["LABEL"],
                "Area": float(str(data["AREA"]).replace(",", ".")),
                "Boundary": data["BOUNDARY"],
                "Text": data["TEXT"],
                "Keterangan": data["KETERANGAN"],
                "Height": data["HEIGHT"],
                "Orientation": data["ORIENTATION"],
            }
            list_data.append(temp)
        self._sts["PersilInduk"] = list_data

        if self._tipe_berkas in ["SUB", "UNI"]:
            for p in self._del_parcels:
                row = self._ent_dataset["PersilMati"].new_row()
                row[0] = str(p)

        self._fill_entity_datatable()
        self._fill_text_entity()
        self._fill_point_entity()
        self._fill_dimensi_entity()

        self._run_integration(payload["reset_302"])

    def _run_integration(self, reset302):
        gu_reg_id = ""
        if self._gambar_ukurs:
            gu_reg_id = str(self._gambar_ukurs[0])

        # TODO: implement staticstorage
        skb = "NonTM3" if self._sistem_koordinat not in ["TM3", "NonTM3"] else "TM3"
        user = app_state.get("pegawai", {})
        print("user", user)
        user_id = (
            user.value["userId"]
            if user.value and "userId" in user.value.keys() and user.value["userId"]
            else ""
        )
        try:
            response = endpoints.submit_sdo(
                nomor_berkas=self._nomor_berkas,
                tahun_berkas=self._tahun_berkas,
                kantor_id=self._kantor_id,
                tipe_kantor_id=self._tipe_kantor_id,
                wilayah_id=self._wilayah_id,
                sistem_koordinat=skb,
                keterangan="",
                petugas_id=user_id,
                sdo_to_submit=self._sts,
                gugus_ids=self._new_gugus_id,
                gu_id=gu_reg_id,
                reset302=reset302,
                user_id=user_id,
            )
            response_json = json.loads(response.content)
            print(response_json)
            if not response_json:
                QtWidgets.QMessageBox.critical(
                    None,
                    "Integrasi",
                    "Integrasi gagal!\nCek service berkas spatial di server sudah dijalankan!",
                )

            if response_json["Error"]:
                if response_json["Error"][0]["message"].startswith(
                    "Geometri persil dengan ID"
                ) or response_json["Error"][0]["message"].startswith(
                    "Geometri apartemen dengan ID"
                ):
                    # TODO: zoom to object
                    msg = str(response_json["Error"][0]["message"]).split("|")[0]
                    QtWidgets.QMessageBox.critical(None, "GeoKKP Web", msg)
                else:
                    msg = str(response_json["Error"][0]["message"])
                    QtWidgets.QMessageBox.critical(None, "GeoKKP Web", msg)
                return

            self._parcel_ready_to_map = []
            self._new_parcels = []

            result_oid_map = {}
            for persil in response_json["PersilBaru"]:
                regid = persil["regid"]
                self._parcel_ready_to_map.append(regid)

                if (
                    regid not in self._old_parcels
                    and regid not in self._del_parcels
                    and regid not in self._old_apartments
                    and regid not in self._del_apartments
                ):
                    self._new_parcels.append(regid)

                result_oid_map[persil["oid"]] = persil["nib"]

            # update nib to layer
            for layer in self.current_layers:
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

            self.btn_rutin_selesai.setDisabled(False)
            self.btn_rutin_layout.setDisabled(False)
            self.btn_rutin_di302.setDisabled(False)

            QtWidgets.QMessageBox.information(
                None,
                "GeoKKP Web",
                "Data telah disimpan ke dalam database. \nLanjutkan ke pencetakan dan plotting peta",
            )
        except Exception as e:
            self._process_available = False
            self._set_button(False)
            self.input_rutin_no_berkas.setDisabled(False)
            self.input_rutin_th_berkas.setDisabled(False)
            self.btn_rutin_cari.setDisabled(False)

            self.btn_rutin_mulai.setDisabled(False)
            self.btn_rutin_selesai.setDisabled(True)
            self.btn_rutin_layout.setDisabled(True)
            self.btn_rutin_di302.setDisabled(True)

            self._reset_variable()
            QtWidgets.QMessageBox.information(
                None,
                "Informasi",
                "Proses telah dihentikan",
            )

    def _fill_entity_datatable(self):
        # TODO: add layer query by code
        pass

    def _fill_text_entity(self):
        # TODO: add layer query by code
        pass

    def _fill_point_entity(self):
        # TODO: add layer query by code
        pass

    def _fill_dimensi_entity(self):
        # TODO: add layer query by code
        pass

    def _process_ganti_desa(self, payload):
        pass

    def _create_dataset_integration(self):
        self._ent_dataset = Dataset()
        persil_mati = self._ent_dataset.add_table("PersilMati")
        persil_mati.add_column("REGID")

        polygon = self._ent_dataset.add_table("Polygon")
        polygon.add_column("Key")
        polygon.add_column("Type")
        polygon.add_column("Label")
        polygon.add_column("Height")
        polygon.add_column("Orientation")
        polygon.add_column("Boundary")
        polygon.add_column("Text")

        garis = self._ent_dataset.add_table("Garis")
        garis.add_column("KEY")
        garis.add_column("TYPE")
        garis.add_column("LINE")

        teks = self._ent_dataset.add_table("Teks")
        teks.add_column("Key")
        teks.add_column("Type")
        teks.add_column("Height")
        teks.add_column("Orientation")
        teks.add_column("Label")
        teks.add_column("Position")

        titik = self._ent_dataset.add_table("Titik")
        titik.add_column("Key")
        titik.add_column("Type")
        titik.add_column("PointOrientation")
        titik.add_column("TextOrientation")
        titik.add_column("Scale")
        titik.add_column("Height")
        titik.add_column("Label")
        titik.add_column("PointPosition")
        titik.add_column("TextPosition")

        dimensi = self._ent_dataset.add_table("Dimensi")
        dimensi.add_column("Key")
        dimensi.add_column("Type")
        dimensi.add_column("Line")
        dimensi.add_column("Initialpoint")
        dimensi.add_column("Labelpoint")
        dimensi.add_column("Endpoint")
        dimensi.add_column("Initialorientation")
        dimensi.add_column("Labelorientation")
        dimensi.add_column("Endorientation")
        dimensi.add_column("Height")
        dimensi.add_column("Label")

    def _handle_informasi_berkas_rutin(self):
        gambar_ukur_id = (
            self._gambar_ukurs[0]
            if self._gambar_ukurs
            else ""
        )

        informasi_persil = InformasiPersil(
            self._nomor_berkas,
            self._tahun_berkas,
            self._kantor_id,
            self._tipe_berkas,
            self._sistem_koordinat,
            self._new_parcel_number,
            self._wilayah_id,
            gambar_ukur_id,
            self._new_parcels,
            self._old_parcels,
        )
        informasi_persil.show()

    def _handle_update_di302(self):
        ucl = LinkDI302(self._berkas_id, self._kode_sppop)
        if self._kode_sppop in ["SPOPP-3.13", "SPOPP-3.12.1", "SPOPP-2.03", "SPOPP-3.17.3"]:
            ucl = LinkDI302A(self._berkas_id)
        ucl.show()

    def input_gambar_denah(self):
        fgd = InputDenah(
            self._nomor_berkas,
            self._tahun_berkas,
            self._berkas_id,
            self._kantor_id,
            self._tipe_berkas,
            self._wilayah_id,
            self._new_parcel_number,
            self._new_apartment_number,
            self._new_parcels,
            self._old_parcels,
            self._new_apartments,
            self._old_apartments,
            self._ganti_desa
        )
        fgd.done.connect(self._handle_input_gambar_denah)
        fgd.show()

    def _handle_input_gambar_denah(self, success):
        if success:
            self.btn_rutin_simpan.setDisabled(False)

    def tutup_berkas_rutin(self):
        response_tutup_berkas = endpoints.stop_berkas(
            nomor_berkas=self._nomor_berkas,
            tahun_berkas=self._tahun_berkas,
            kantor_id=self._kantor_id,
        )
        response_tutup_berkas_json = json.loads(response_tutup_berkas.content)
        if response_tutup_berkas_json:
            self._process_available = False
            self._set_button(False)
            self.input_rutin_no_berkas.setDisabled(False)
            self.input_rutin_th_berkas.setDisabled(False)
            self.btn_rutin_cari.setDisabled(False)

            self._reset_variable()

            layer_ids = [layer.id() for layer in self.current_layers]
            self.project.instance().removeMapLayers(layer_ids)
            iface.mapCanvas().refresh()
            self.current_layers = []

            self._set_initial_state()

            QtWidgets.QMessageBox.information(
                None,
                "Informasi",
                "Proses telah dihentikan",
            )
        else:
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                "Proses tidak berhasil dihentikan",
            )

    def selesai_berkas_rutin(self):
        if self._tipe_berkas != "DAG" and self._parcel_ready_to_map:
            if self._old_apartments and self._del_apartments:
                parcels = [str(p) for p in self._parcel_ready_to_map]
                force_mapping = True
                response = endpoints.cek_mapping(parcels)
                already_mapped = bool(response.content)
                if not already_mapped:
                    if force_mapping:
                        result = QtWidgets.QMessageBox.question(
                            None,
                            "Selesai Berkas",
                            "Persil belum dipetakan\nApakah akan menyelesaikan berkas?",
                        )
                        if result != QtWidgets.QMessageBox.Yes:
                            return
                    else:
                        QtWidgets.QMessageBox.critical(
                            None,
                            "Selesai Berkas",
                            "Persil belum dipetakan\nUntuk menyelesaikan berkas lakukan proses Map Placing terlebih dahulu",
                        )
