from datetime import datetime
import os
import json
import hashlib
from urllib import response

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from ...utils import (
    get_layers_config_by_topology,
    readSetting,
    get_project_crs,
    sdo_to_layer,
    get_layer_config,
    add_layer,
    select_layer_by_topology,
)
from ...utils.draw_entity import DrawEntity
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
        self._ganti_desa = "0"
        self._kode_spopp = ""
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

        self._ent_dataset = None
        self._sts = None

        self._parcels_ready_2_map = []
        self._process_available = False
        self._d_set = None
        self._system_coordinate = "TM3"

        self._layers = []

        self.btn_cari.clicked.connect(self._btn_cari_click)
        self.btn_first.clicked.connect(self._btn_first_click)
        self.btn_prev.clicked.connect(self._btn_prev_click)
        self.btn_next.clicked.connect(self._btn_next_click)
        self.btn_last.clicked.connect(self._btn_last_click)
        self.btn_start_process.clicked.connect(self._prepare_berkas)
        self.btn_save_data.clicked.connect(self._submit)
        self.btn_info_process.clicked.connect(self._get_process_info)
        self.btn_parcel_mapping.clicked.connect(self._update_di_302)
        self.btn_pause_process.clicked.connect(self._stop_process)
        self.btn_finish_process.clicked.connect(self._finish_process)

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

        self.txt_tahun.setText(datetime.now().strftime("%Y"))

    def _btn_cari_click(self):
        self._start = 0
        self._count = -1
        self._txt_nomor = self.txt_nomor.text()
        self._txt_tahun = self.txt_tahun.text()

        self.btn_first.setDisabled(False)
        self.btn_first.setDisabled(False)

        self._refresh_grid()

    def _refresh_grid(self):
        response = endpoints.get_berkas(
            self._txt_nomor,
            self._txt_tahun,
            self._kantor_id,
            self._tipe_kantor_id,
            self._start,
            self._limit,
            self._count
        )
        self._d_set = Dataset(response.content)

        if self._count == -1:
            self._count = int(self._d_set["JUMLAHTOTAL"].rows[0][0])

        if self._count > 0:
            if self._start + self._limit >= self._count:
                page = f"{self._start + 1} - {self._count} dari {self._count}"
                self.txt_paging.setText(page)
                self.btn_next.setDisabled(True)
            else:
                page = f"{self._start + 1} - {self._start + self._limit} dari {self._count}"
                self.txt_paging.setText(page)
                self.btn_next.setDisabled(True)
            if self._d_set["BERKASSPATIAL"]:
                self._d_set["BERKASSPATIAL"].render_to_qtable_widget(
                    self.dgv_inbox,
                    [0, 4]
                )
        else:
            self.txt_paging.setText("0")
            self.btn_next.setDisabled(True)
            self.btn_prev.setDisabled(True)
            self.dgv_inbox.setRowCount(0)

        if self._start == 0 or self._count == 0:
            self.btn_prev.setDisabled(True)
        else:
            self.btn_prev.setDisabled(False)

    def _btn_first_click(self):
        self._start = 0
        self.btn_prev.setDisabled(True)
        self.btn_next.setDisabled(False)
        self._refresh_grid()

    def _btn_prev_click(self):
        self._start -= self._limit
        if self._start <= 0:
            self.btn_prev.setDisabled(True)
        self.btn_next.setDisabled(False)
        self._refresh_grid()

    def _btn_next_click(self):
        self._start += self._limit
        if self._start + self._limit >= self._count:
            self.btn_next.setDisabled(True)
        self.btn_prev.setDisabled(False)
        self._refresh_grid()

    def _btn_last_click(self):
        self._start = (self._count // self._limit) * self._limit
        if self._start >= self._count:
            self._start -= self._limit
            self.btn_prev.setDisabled(True)
        else:
            self.btn_prev.setDisabled(False)

        self.btn_next.setDisabled(True)
        self.btn_first.setDisabled(False)
        self._refresh_grid()

    def _prepare_berkas(self):
        if self._d_set['BERKASSPATIAL'] and self._d_set['BERKASSPATIAL'].get_selected_qtable_widget():
            selected = self._d_set['BERKASSPATIAL'].get_selected_qtable_widget()
            self._nomor_berkas = selected[1].text()
            self._tahun_berkas = selected[2].text()
            self._tipe_berkas = selected[3].text()
            self._berkas_id = selected[0].text()
            self._start_berkas()
        else:
            QtWidgets.QMessageBox.warning(
                None, "Perhatian", "Pilih Sebuah Berkas Yang Akan Diproses"
            )

    def _start_berkas(self):
        username_state = app_state.get("username", "")
        username = username_state.value
        response = endpoints.start_berkas_spasial(
            self._nomor_berkas,
            self._tahun_berkas,
            self._kantor_id,
            self._tipe_kantor_id,
            username
        )
        bs = json.loads(response.content)
        print(bs)
        if bs["valid"]:
            lanjut_blanko = True
            response = endpoints.get_is_e_sertifikat(self._kantor_id)
            is_e_sertifikat = readSetting("isESertifikat")
            if is_e_sertifikat and self._tipe_kantor_id != "1" and self._tipe_kantor_id != "2":
                response = endpoints.get_blanko_by_berkas_id(self._berkas_id, "P")
                blanko_dataset = json.loads(response.content)
                if blanko_dataset["BLANKO"]:
                    lanjut_blanko = True
                else:
                    lanjut_blanko = False
            if bs["kodeSpopp"] == "SPOPP-3.46.3" \
                    or bs["kodeSpopp"] == "SPOPP-3.09.9" \
                    or bs["kodeSpopp"] == "SPOPP-3.09.1" \
                    or bs["kodeSpopp"] == "SPOPP-3.09.2" \
                    or bs["kodeSpopp"] == "SPOPP-3.18.1" \
                    or bs["kodeSpopp"] == "SPOPP-3.12.1" \
                    or lanjut_blanko:
                self._wilayah_id = bs["wilayahId"]
                self._new_parcel_number = bs["newParcelNumber"]
                self._new_apartment_number = bs["newApartmentNumber"]
                self._new_gugus_id = bs["newGugusId"]
                self._ganti_desa = bs["gantiDesa"]
                self._kode_spopp = bs["kodeSpopp"]

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
                        de = DrawEntity([self._new_gugus_id], True)
                        de.draw()
                else:
                    if self._old_gugus_ids:
                        str = [str(s) for s in self._old_gugus_ids]
                        de = DrawEntity(str, True)
                        de.draw()
                    else:
                        QtWidgets.QMessageBox.information(
                            None, "GeoKKP", "Data kosong, silahkan buat layer baru melalui menu \"Layer Baru\""
                        )

                self._set_button(True)
                self._process_available = True
                self.txt_nomor.setText(self._nomor_berkas)
                self.txt_tahun.setText(self._tahun_berkas)
                self.txt_nomor.setDisabled(True)
                self.txt_tahun.setDisabled(True)
                self.btn_cari.setDisabled(True)

                self.btn_start_process.setDisabled(True)

                if self._tipe_berkas != "DAG":
                    self._system_coordinate = "TM3"
                else:
                    self._input_gambar_denah()
            else:
                QtWidgets.QMessageBox.warning(
                    None, "Perhatian", "Lakukan registrasi blanko terlebih dahulu"
                )
                return
        else:
            msg = " \n".join(bs["errorStack"])
            QtWidgets.QMessageBox.critical(
                None, "GeoKKPWeb", msg
            )
            return

    def _set_button(self, enabled):
        self.btn_save_data.setDisabled(not enabled)
        self.btn_info_process.setDisabled(not enabled)
        self.btn_pause_process.setDisabled(not enabled)

    def _input_gambar_denah(self):
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
            self._ganti_desa,
        )
        fgd.done.connect(self._handle_input_gambar_denah)
        fgd.show()

    def _show_topo_not_found(self, topology):
        layers_config = get_layers_config_by_topology(topology)
        layer_name = "\n".join([layer["Nama Layer"] for layer in layers_config])
        msg = f"Harus ada minimal satu dari layer berikut di project:\n{layer_name}"

        QtWidgets.QMessageBox.critical(None, "Perhatian", msg)

    def _submit(self):
        if self._tipe_berkas == "DAG":
            self._input_gambar_denah()
            return

        if self._old_apartments or self._del_apartments:
            topology = "Gambar_Denah"
        else:
            topology = "Batas_Persil"

        self._layers = select_layer_by_topology(topology)
        if not self._layers:
            self._show_topo_not_found(topology)
            return

        topo_error_message = []
        for layer in self._layers:
            valid, num = quick_check_topology(layer)
            if not valid:
                message = f"Ada {num} topology error di layer {layer.name()}"
                topo_error_message.append(message)

        if topo_error_message:
            QtWidgets.QMessageBox.warning(
                None, "Perhatian", "\n".join(topo_error_message)
            )
            return

        self._create_dataset_integration()
        g_ukur_id = ""
        if self._gambar_ukurs:
            g_ukur_id = str(self._gambar_ukurs[0])

        pd = DesainPersil(
            parent=self,
            nomor_berkas=self._nomor_berkas,
            tahun_berkas=self._tahun_berkas,
            kantor_id=self._kantor_id,
            tipe_kantor_id=self._tipe_kantor_id,
            tipe_berkas=self._tipe_berkas,
            gambar_ukur_id=g_ukur_id,
            wilayah_id=self._wilayah_id,
            tipe_sistem_koordinat=self._system_coordinate,
            new_parcel_number=self._new_parcel_number,
            new_apartment_number=self._new_apartment_number,
            new_parcels=self._new_parcels,
            old_parcels=self._old_parcels,
            new_apartments=self._new_apartments,
            old_apartments=self._old_apartments,
            ganti_desa=self._ganti_desa
        )
        pd.integrasi.connect(self._parcel_designer_clicked)
        pd.show()

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

    def _parcel_designer_clicked(self, pd):
        if pd["ds_parcel"]:
            self._wilayah_id = pd["wilayah_id"]
            lspb = []
            self._sts = {}
            for data in pd["ds_parcel"]["PersilBaru"]:
                spb = {
                    "OID": data["OID"],
                    "Label": data["LABEL"],
                    "Area": float(str(data["AREA"]).replace(",", ".")),
                    "Boundary": data["BOUNDARY"],
                    "Text": data["TEXT"],
                    "Keterangan": data["KETERANGAN"],
                    "Height": data["HEIGHT"],
                    "Orientation": data["ORIENTATION"],
                }
                lspb.append(spb)
            self._sts["PersilBaru"] = lspb

            lspe = []
            self._sts = {}
            for data in pd["ds_parcel"]["PersilEdit"]:
                spe = {
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
                lspe.append(spe)
            self._sts["PersilEdit"] = lspb

            lspi = []
            for data in pd["ds_parcel"]["PersilInduk"]:
                if data["OID"] is None:
                    continue

                spi = {
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
                lspi.append(spi)
            self._sts["PersilInduk"] = lspi

            if self._tipe_berkas in ["SUB", "UNI"]:
                for p in self._del_parcels:
                    row = self._ent_dataset["PersilMati"].new_row()
                    row[0] = str(p)

            self._fill_entity_datatable()
            self._fill_text_entity()
            self._fill_point_entity()
            self._fill_dimensi_entity()

            self._run_integration(pd["reset_302"])

    def _fill_entity_datatable(self):
        pass

    def _fill_text_entity(self):
        pass

    def _fill_point_entity(self):
        pass

    def _fill_dimensi_entity(self):
        pass

    def _run_integration(self, reset302):
        gu_reg_id = ""
        if self._gambar_ukurs:
            gu_reg_id = str(self._gambar_ukurs[0])

        skb = ""
        if self._system_coordinate == "TM3":
            skb = "TM3"
        else:
            skb = "NonTM3"

        user = app_state.get("pegawai", {})
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
            ds = json.loads(response.content)
            if ds["Error"]:
                if ds["Error"][0]["message"].startswith(
                    "Geometri persil dengan ID"
                ) or ds["Error"][0]["message"].startswith(
                    "Geometri apartemen dengan ID"
                ):
                    # TODO: zoom to object
                    msg = str(ds["Error"][0]["message"]).split("|")[0]
                    QtWidgets.QMessageBox.critical(None, "GeoKKP Web", msg)
                else:
                    msg = str(ds["Error"][0]["message"])
                    QtWidgets.QMessageBox.critical(None, "GeoKKP Web", msg)
                return

            self._parcels_ready_2_map = []
            self._new_parcels = []

            result_oid_map = {}
            for persil in ds["PersilBaru"]:
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
            for layer in self._layers:
                field_index = layer.fields().indexOf("label")
                features = layer.getFeatures()
                for feature in features:
                    identifier = f"{layer.id()}|{feature.id()}".encode("utf-8")
                    objectid = hashlib.md5(identifier).hexdigest().upper()
                    if objectid not in result_oid_map:
                        continue

                    layer.startEditing()
                    layer.changeAttributeValue(
                        feature.id(), field_index, result_oid_map[objectid]
                    )
                    layer.commitChanges()

            self.btn_finish_process.setDisabled(False)
            self.btn_create_layout.setDisabled(False)
            self.btn_parcel_mapping.setDisabled(False)

            QtWidgets.QMessageBox.information(
                None,
                "GeoKKP Web",
                "Data telah disimpan ke dalam database. \nLanjutkan ke pencetakan dan plotting peta",
            )
        except Exception as e:
            self._process_available = False
            self._set_button(False)
            self.txt_nomor.setDisabled(False)
            self.txt_tahun.setDisabled(False)
            self.btn_cari.setDisabled(False)

            self.btn_start_process.setDisabled(False)
            self.btn_finish_process.setDisabled(False)
            self.btn_create_layout.setDisabled(False)
            self.btn_parcel_mapping.setDisabled(False)

            self._reset_variables()
            QtWidgets.QMessageBox.information(
                None,
                "Informasi",
                "Proses telah dihentikan, berkas anda akan dikunci oleh sistem",
            )

    def _reset_variables(self):
        self._txt_nomor = ""
        self._txt_tahun = ""
        self._nomor_berkas = ""
        self._tahun_berkas = ""
        self._tipe_berkas = ""
        self._ganti_desa = "0"

        self._wilayah_id = ""
        self._gambar_ukur_id = ""
        self._new_gugus_id = ""
        self._new_parcel_number = ""
        self._old_parcel_number = ""
        self._old_parcels = []
        self._del_parcels = []
        self._old_apartments = []
        self._del_apartments = []
        self._new_parcels = []
        self._new_apartments = []
        self._gambar_ukurs = []
        self._error_stack = []
        self._old_gugus_ids = []
        self._parcels_ready_2_map = []
        self._layers = []

    def _stop_process(self):
        if self._tutup_proses():
            self._process_available = False
            self._set_button(False)
            self.txt_nomor.setDisabled(False)
            self.txt_tahun.setDisabled(False)
            self.btn_cari.setDisabled(False)

            self.btn_start_process.setDisabled(False)
            self.btn_finish_process.setDisabled(True)
            self.btn_create_layout.setDisabled(True)
            self.btn_parcel_mapping.setDisabled(True)

            self._reset_variables()

            QtWidgets.QMessageBox.information(
                None,
                "Informasi",
                "Proses telah dihentikan",
            )
        else:
            QtWidgets.QMessageBox.critical(
                None,
                "Informasi",
                "Proses tidak berhasil dihentikan",
            )

    def _finish_process(self):
        if self._tipe_berkas != "DAG" and not self._parcels_ready_2_map:
            if self._old_apartments or self._del_apartments:
                pass
            else:
                parcels = [str(p) for p in self._parcels_ready_2_map]

                force_mapping = True

                response = endpoints.cek_mapping(parcels)
                already_mapped = json.loads(response.content)
                if not already_mapped:
                    if not force_mapping:
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

        if self._tipe_berkas == "NPG":
            response = endpoints.check_peta_bidang(self._berkas_id)
            d_table = json.loads(response.content)
            jumlah_persil_tanpa_pbt = int(d_table[0]["jumlahpersiltanpapbt"])

            if jumlah_persil_tanpa_pbt:
                QtWidgets.QMessageBox.warning(
                    None,
                    "Selesai Berkas",
                    "Masih ada persil yang belum memiliki Peta Bidang\nSilahkan membuat peta bidang dari menu pencetakan",
                )
                return

        if self._tipe_berkas == "SUB" or self._tipe_berkas == "NPG":
            response = endpoints.check_peta_tematik(self._berkas_id)
            d_table = json.loads(response.content)
            print(d_table)
            jumlah_persil_tanpa_ptbt = int(d_table[0]["JUMLAHPERSILTANPAPTBT"])

            if jumlah_persil_tanpa_ptbt != 0 and d_table[0]["KODESPOPP"] in ("SPOPP-3.13", "SPOPP-3.12.1"):
                QtWidgets.QMessageBox.warning(
                    None,
                    "Selesai Berkas",
                    "Masih ada persil yang belum memiliki Peta Tematik\nSilahkan membuat peta tematik terlebih dahulu",
                )
                return

        response = endpoints.check_di302(self._berkas_id)
        d302_table = json.loads(response.content)

        jumlah_di302_unlinked = int(d302_table[0]["DI302"])
        jumlah_di302a_unlinked = int(d302_table[0]["DI302A"])

        if jumlah_di302_unlinked:
            QtWidgets.QMessageBox.warning(
                None,
                "Selesai Berkas",
                "Masih ada persil yang belum memiliki DI302",
            )
            return

        if jumlah_di302a_unlinked:
            QtWidgets.QMessageBox.warning(
                None,
                "Selesai Berkas",
                "Masih ada persil yang belum memiliki DI302A",
            )
            return

        user = app_state.get("pegawai", {})
        response = endpoints.finish_berkas(
            self._nomor_berkas,
            self._tahun_berkas,
            self._kantor_id,
            self._tipe_kantor_id,
            user.value
        )
        result = response.content.decode("utf-8")

        if result.split(":")[0] == "OK":
            self._process_available = False
            self._set_button(False)
            self.txt_nomor.setDisabled(False)
            self.txt_tahun.setDisabled(False)
            self.btn_cari.setDisabled(False)

            self.btn_start_process.setDisabled(False)
            self.btn_finish_process.setDisabled(True)
            self.btn_create_layout.setDisabled(True)
            self.btn_parcel_mapping.setDisabled(True)

            self._reset_variables()
            QtWidgets.QMessageBox.information(
                None,
                "Selesai Berkas",
                "Proses berkas spasial sudah selesai dan terkirim ke " + result.split(":".ToCharArray())[1],
            )
            self._refresh_grid()
        else:
            QtWidgets.QMessageBox.information(
                None,
                "Error",
                "Proses berkas spasial tidak berhasil diselesaikan",
            )

    def _tutup_proses(self):
        response = endpoints.stop_berkas(self._nomor_berkas, self._tahun_berkas, self._kantor_id)
        return bool(response.content)

    def _update_di_302(self):
        ucl = LinkDI302(self._berkas_id, self._kode_spopp)
        if self._kode_spopp in [
            "SPOPP-3.13",
            "SPOPP-3.12.1",
            "SPOPP-2.03",
            "SPOPP-3.17.3",
        ]:
            ucl = LinkDI302A(self._berkas_id)
        ucl.show()

    def _get_process_info(self):
        gambar_ukur_id = self._gambar_ukurs[0] if self._gambar_ukurs else ""

        pi = InformasiPersil(
            self._nomor_berkas,
            self._tahun_berkas,
            self._kantor_id,
            self._tipe_berkas,
            self._system_coordinate,
            self._new_parcel_number,
            self._wilayah_id,
            gambar_ukur_id,
            self._new_parcels,
            self._old_parcels,
        )
        pi.show()
