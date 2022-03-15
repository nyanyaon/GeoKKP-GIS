import os
import json
from urllib import response

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from ...utils import (
    readSetting,
    get_project_crs,
    sdo_to_layer,
    get_layer_config,
    parse_sdo_geometry,
)
from ...api import endpoints
from ...models.dataset import Dataset
from ...create_pbt import CreatePBT
from ...memo import app_state
from ...desain_pbt import DesainPBT

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../../ui/workpanel/tab_invent.ui")
)


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1

class TabInvent(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(TabInvent, self).__init__(parent)
        self.setupUi(self)

        self._start = 0
        self._limit = 20
        self._count = -1

        self.btn_cari.clicked.connect(self.btnCari_Click)
        self.btn_start.clicked.connect(self.prepare_berkas)
        self.btn_create.clicked.connect(self.createPBT)
        self.btn_close.clicked.connect(self.stop_proses)
        self.btn_finish.clicked.connect(self.finish_process)

        self._submitted_parcels = []
        self.dvg_invent.doubleClicked.connect(self.prepare_berkas)
        self.btn_save.clicked.connect(self.submit)

        self.btn_save.setEnabled(False)
        self.btn_unggah.setEnabled(False)
        self.btn_layout.setEnabled(False)
        self.btn_close.setEnabled(False)
        self.btn_finish.setEnabled(False)

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

        response = endpoints.get_program_invent_by_kantor(self._kantor_id)
        program_invent = json.loads(response.content)

        self.cmb_kegiatan.clear()
        self.cmb_kegiatan.addItem("*","")
        print(program_invent)
        for program in program_invent["PROGRAM"]:
            self.cmb_kegiatan.addItem(program["NAMA"],program["PROGRAMID"])

    def submit(self):
        layer = QgsProject.instance().mapLayersByName("(Lb_Rincikan) Garis Rincikan")[0]
        self.petaBidang = DesainPBT(self.pbt,"TM3",True,current_layers=layer)
        self.petaBidang.show()
    
    def btnCari_Click(self):
        self._start = 0 
        self._count = -1
        self._txtNomor = self.txt_nomor.text()
        self._txtTahun = self.txt_tahun.text()
        self._txtKegiatan = self.cmb_kegiatan.currentData()

        self.btn_first.setEnabled(False)
        self.btn_last.setEnabled(False)

        self.RefreshGrid()

    def RefreshGrid(self):
        
        response = endpoints.get_pbt_for_apbn(
            nomor_pbt=self._txtNomor,
            tahun_pbt=self._txtTahun,
            kantor_id=self._kantor_id,
            proyek=self._txtKegiatan,
            tipe_pbt="PBTI",
            start=self._start,
            limit=self._limit,
            count=self._count)
        self.dset = json.loads(response.content)
        print(self.dset,"data")

        if(self._count == -1):
            self._count = self.dset["JUMLAHTOTAL"][0]["COUNT(1)"]

        if self._count > 0:
            if self._start + self._limit >= self._count:
                page = f"{self._start + 1} - {self._count} dari {self._count}"
                self.txt_paging.setText(page)
                self.btn_next.setDisabled(True)
            else:
                page = f"{self._start + 1} - {self._start + self._limit} dari {self._count}"
                self.txt_paging.setText(page)
                self.btn_next.setDisabled(False)
        else:
            self.txt_paging.setText("0")
            self.btn_next.setDisabled(True)
            self.btn_prev.setDisabled(True)

        if self._start == 0 or self._count == 0:
            self.btn_prev.setDisabled(True)
        else:
            self.btn_prev.setDisabled(False)

        if(self.dset["PBTAPBN"] != None and len(self.dset["PBTAPBN"]) > 0):
            dataset = Dataset()
            table = dataset.add_table("PBTAPBN")
            table.add_column("DOKUMENPENGUKURANID")
            table.add_column("NOMOR")
            table.add_column("PRODUK")
            table.add_column("LINTOR")
            table.add_column("ROWNUMS")

            for produk in self.dset["PBTAPBN"]:
                d_row = table.new_row()
                d_row["DOKUMENPENGUKURANID"] = produk["DOKUMENPENGUKURANID"]
                d_row["NOMOR"] = produk["NOMOR"]
                d_row["PRODUK"] = produk["PRODUK"]
                d_row["LINTOR"] = produk["LINTOR"]
                d_row["ROWNUMS"] = produk["ROWNUMS"]

            dataset.render_to_qtable_widget("PBTAPBN",self.dvg_invent,[0,4])

    def createPBT(self):
        self.pbti = CreatePBT("PBTI")
        self.pbti.show()
        self.pbti.processed.connect(self.createPBTHandler)

    def createPBTHandler(self,payload):
        print(payload)
        if(payload["myPBT"]["PBT"]["errorStack"] is None or len(payload["myPBT"]["PBT"]["errorStack"])):
            self.txt_nomor.setText(payload["myPBT"]["PBT"]["nomor"])
            self.txt_tahun.setText(payload["myPBT"]["PBT"]["tahun"])

            self._start = 0
            self._count = -1
            self._txtNomor = self.txt_nomor.text()
            self._txtTahun = self.txt_tahun.text()
            self._txtKegiatan = payload["myPBT"]["PBT"]["programId"]

            self.btn_first.setEnabled(True)
            self.btn_last.setEnabled(True)

            self.RefreshGrid()

            self._processAvailable = True

            self.pbt = payload["myPBT"]["PBT"]
            self._currentDokumenPengukuranId = payload["myPBT"]["PBT"]["dokumenPengukuranId"]
            self.btn_save.setEnabled(True)
            self.btn_layout.setEnabled(True)
            self.btn_close.setEnabled(True)
            self.btn_unggah.setEnabled(True)
            self.btn_finish.setEnabled(True)

            self.txt_nomor.setEnabled(False)
            self.txt_tahun.setEnabled(False)
            self.btn_cari.setEnabled(False)
            self.btn_create.setEnabled(False)
            self.btn_start.setEnabled(False)

            self.pbti.close()

            QtWidgets.QMessageBox.information(
                None, "GeoKKP", f"Peta bidang telah dibaut dengan nomor : {payload['myPBT']['PBT']['nomor']} / {payload['myPBT']['PBT']['tahun']}"
            )

        else:
            self.pbti.close()

            QtWidgets.QMessageBox.information(
                None, "GeoKKP", payload["myPBT"]["PBT"]["errorStack"][0]
            )

    def prepare_berkas(self):
        item = self.dvg_invent.selectedItems()

        username_state = app_state.get("username", "")
        username = username_state.value

        if(len(item) != 0):

            dataSelect = []
            self.dvg_invent.setColumnHidden(0, False)
            for x in range(self.dvg_invent.columnCount()):
                dataSelect.append(self.dvg_invent.item(item[0].row(),x).text())
            self.dvg_invent.setColumnHidden(0, True)

            self._currentDokumenPengukuranId = dataSelect[0]

            response = endpoints.start_edit_pbt_for_apbn(self._currentDokumenPengukuranId,username)
            self.pbt = json.loads(response.content)
            print(self.pbt)

            if(self.pbt["penggunaSpasial"] is None or self.pbt["penggunaSpasial"] == username):
                self._processAvailable = True
                gugus_ids = self.pbt["gugusId"]
                print(gugus_ids)
                if(gugus_ids != ""):
                    self._load_berkas_spasial(gugus_ids, False)
                disable_link = bool(self.pbt["mitraKerjaid"])
                self._txtNomor = self.txt_nomor.text()
                self._txtTahun = self.txt_tahun.text()
                self.btn_save.setEnabled(True)
                self.btn_layout.setEnabled(True)
                self.btn_close.setEnabled(True)
                self.btn_unggah.setEnabled(disable_link)
                self.btn_finish.setEnabled(True)

                self.txt_nomor.setEnabled(False)
                self.txt_tahun.setEnabled(False)
                self.btn_cari.setEnabled(False)
                self.btn_create.setEnabled(False)
                self.btn_start.setEnabled(False)

            else:
                user = self.pbt["penggunaSpasial"]
                QtWidgets.QMessageBox.warning(
                    None, "Perhatian", f"Peta bidang sedang digunakan oleh {user}"
                )
        else:
            QtWidgets.QMessageBox.warning(
                None,
                "Perhatian",
                f"Pilih Sebuah Berkas Yang Akan Diproses",
            )
    
    def _load_berkas_spasial(self, gugus_ids, riwayat=False):
        response_spatial_sdo = endpoints.get_spatial_document_sdo([gugus_ids],riwayat)
        response_spatial_sdo_json = json.loads(response_spatial_sdo.content)
        print(response_spatial_sdo_json)

        # response = endpoints.get_rincikan_by_pbt(self._currentDokumenPengukuranId)
        # response_json = json.loads(response.content)

        if not response_spatial_sdo_json["status"]:
            QtWidgets.QMessageBox.critical(None, "Error", "Proses Unduh Geometri gagal")
            return

        epsg = get_project_crs()
        layer_config = get_layer_config("Lb_Rincikan")

        nama = []
        if response_spatial_sdo_json["geoKkpPolygons"]:
            for index,feature in enumerate(response_spatial_sdo_json["geoKkpPolygons"]):
                # for label in response_json["RINCIKANBARU"]:
                #     if(label["PERSILINVENTID"] == feature["key"]):
                #         response_spatial_sdo_json["geoKkpPolygons"][index]["label"] = label["NOMOR"]
                #         break
                response_spatial_sdo_json["geoKkpPolygons"][index]["pemilik"] = ""
                geometryPoly = parse_sdo_geometry(feature["boundary"]["sdoElemInfo"],feature["boundary"]["sdoOrdinates"])
                for feature in response_spatial_sdo_json["geoKkpTekss"]:
                    geometryPoint = parse_sdo_geometry(feature["position"]["sdoElemInfo"],feature["position"]["sdoOrdinates"])
                    if(geometryPoly.contains(geometryPoint)):
                        if(feature["type"] == "TeksNama"):
                            response_spatial_sdo_json["geoKkpPolygons"][index]["pemilik"] = feature["label"]
                        else:
                            response_spatial_sdo_json["geoKkpPolygons"][index]["label"] = feature["label"]
                            

            layer = sdo_to_layer(
                response_spatial_sdo_json["geoKkpPolygons"],
                name=layer_config["Nama Layer"],
                symbol=layer_config["Style Path"],
                crs=epsg,
                coords_field="boundary",
            )

        # layer_config = get_layer_config("Tn_Rincikan")
        # if response_spatial_sdo_json["geoKkpTekss"] != []:
        #     layer = sdo_to_layer(
        #         response_spatial_sdo_json["geoKkpTekss"],
        #         name=layer_config["Nama Layer"],
        #         symbol=layer_config["Style Path"],
        #         crs=epsg,
        #         coords_field="position",
        #     )
            
        iface.actionZoomToLayer().trigger()

    def tutup_proses(self):
        response = endpoints.stop_pbt(self._currentDokumenPengukuranId)
        result = json.loads(response.content)
        return result

    def stop_proses(self):
        if(self.tutup_proses()):
            self._processAvailable = False
            self.btn_start.setEnabled(True)
            self.btn_create.setEnabled(True)
            self.btn_save.setEnabled(False)
            self.btn_unggah.setEnabled(False)
            self.btn_layout.setEnabled(False)
            self.btn_close.setEnabled(False)
            self.btn_finish.setEnabled(False)

            self.btn_cari.setEnabled(True)
            self.txt_tahun.setEnabled(True)
            self.txt_nomor.setEnabled(True)

            pbt = None

            QtWidgets.QMessageBox.information(
                None, "GeoKKP", "Proses spasial sudah dihentikan"
            )

        else:
            QtWidgets.QMessageBox.information(
                None, "GeoKKP", "Proses spasial tidak dapat dihentikan"
            )

    def finish_process(self):
        if self._submitted_parcels:
            parcels = [str(f) for f in self._submitted_parcels]
            force_mapping = True

            already_mapped = endpoints.cek_mapping(parcels)
            print(already_mapped.content)

            if already_mapped.content.lower() != "true":
                if not force_mapping:
                    result = QtWidgets.QMessageBox.question(
                        self,
                        "Selesai Berkas",
                        "Persil belum dipetakan\nApakah akan menyelesaikan berkas?",
                    )
                    if result != QtWidgets.QMessageBox.Yes:
                        return
                else:
                    QtWidgets.QMessageBox.information(
                        None,
                        "Selesai Berkas",
                        "Persil belum dipetakan\nUntuk menyelesaikan berkas lakukan proses Map Placing terlebih dahulu",
                    )

        response = endpoints.finish_pbt(self._current_document_pengukuran_id)
        if response.content.decode("utf-8").split(":")[0] == "OK":
            self._processAvailable = False
            self.btn_start.setEnabled(True)
            self.btn_create.setEnabled(True)
            self.btn_save.setEnabled(False)
            self.btn_unggah.setEnabled(False)
            self.btn_layout.setEnabled(False)
            self.btn_close.setEnabled(False)
            self.btn_finish.setEnabled(False)

            self._pbt = None
            QtWidgets.QMessageBox.information(
                None,
                "Informasi",
                "Proses spasial sudah selesai",
            )
            self._cari_berkas_apbn()
        else:
            QtWidgets.QMessageBox.critical(
                None,
                "Error",
                response.content.decode("utf-8"),
            )

            

        



            
        

