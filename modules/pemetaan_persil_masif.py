import os
import json
import processing
import re

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject, QgsRectangle, QgsFeatureRequest
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from .models.dataset import Dataset
from .utils import get_feature_object_id, readSetting, select_layer_by_regex, get_polygon_by_point, add_bintang
from .utils.geometry import get_sdo_point, get_sdo_polygon
from .api import endpoints
from .memo import app_state

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/pemetaan_persil_masif.ui")
)


class UploadPersilMasif(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Pemetaan Persil Masif"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(UploadPersilMasif, self).__init__(parent)
        self.setupUi(self)

        self._kantor_id = ""
        self._tipe_kantor_id = ""

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
            23845,
        ]

        self._ds_parcel = Dataset()
        self._ds_parcel_import = Dataset()
        self._bs_multi_persil = []
        self.ext_geom = {}
        self._polygonizer = {}
        self._parcel_list = []

        self._initialize_dataset()

        self.cmb_propinsi.currentIndexChanged.connect(self._cmb_propinsi_selected_index_changed)
        self.cmb_kabupaten.currentIndexChanged.connect(self._cmb_kabupaten_selected_index_changed)
        self.cmb_kecamatan.currentIndexChanged.connect(self._cmb_kecamatan_selected_index_changed)
        self.cmb_desa.currentIndexChanged.connect(self._cmb_desa_selected_index_changed)

        self.btn_select.clicked.connect(self._btn_select_click)
        self.btn_select_all.clicked.connect(self._btn_select_all_click)
        self.btn_import.clicked.connect(self._btn_import_click)

        self.setup_workpanel()

    def closeEvent(self, event):
        self.closingPlugin.emit()
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

        # TODO: set default cmb with QGIS PROJECT crs

        # TODO: binding source

        self._set_cmb_propinsi()

    def _initialize_dataset(self):
        persil_by_nib = self._ds_parcel.add_table("PersilByNIB")
        persil_by_nib.add_column("OIDNIB", "")
        persil_by_nib.add_column("OIDSU", "")
        persil_by_nib.add_column("OIDHAK", "")
        persil_by_nib.add_column("NIB", "")
        persil_by_nib.add_column("SU", "")
        persil_by_nib.add_column("HAK", "")
        persil_by_nib.add_column("AREA", 0)
        persil_by_nib.add_column("BOUNDARY", {})
        persil_by_nib.add_column("TEXT", {})
        persil_by_nib.add_column("KETERANGAN", "")
        persil_by_nib.add_column("HEIGHT", 1)
        persil_by_nib.add_column("ORIENTATION", 0)

        persil_baru = self._ds_parcel_import.add_table("PersilBaru")
        persil_baru.add_column("PERSILID", "")
        persil_baru.add_column("AREA", 0)
        persil_baru.add_column("BOUNDARY", {})
        persil_baru.add_column("TEXT", {})
        persil_baru.add_column("HEIGHT", 1)
        persil_baru.add_column("ORIENTATION", 0)
        persil_baru.add_column("USERID", "")
        persil_baru.add_column("SRID", "")
        persil_baru.add_column("KANTORID", "")
        persil_baru.add_column("LABEL", "")
        persil_baru.add_column("WILAYAHID", "")\


    def _cmb_propinsi_selected_index_changed(self):
        self._set_cmb_kabupaten()

    def _cmb_kabupaten_selected_index_changed(self):
        self._set_cmb_kecamatan()

    def _cmb_kecamatan_selected_index_changed(self):
        self._set_cmb_desa()

    def _cmb_propinsi_selected_index_changed(self):
        self._set_cmb_kabupaten()

    def _cmb_desa_selected_index_changed(self):
        row = self.cmb_desa.currentData()
        if "ZONATM3" in row and row["ZONATM3"]:
            crs = f"TM3-{row['ZONATM3']}"
            self.cmb_coordinate_system.setCurrentText(crs)
            self.cmb_coordinate_system.setDisabled(True)
        else:
            self.cmb_coordinate_system.setDisabled(False)

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
            self.cmb_desa.addItem(des["DESANAMA"], des)

    def _btn_import_click(self):
        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        if not pegawai or "userId" not in pegawai or "userId" not in pegawai:
            return

        msg = f"Anda akan meng-import bidang tanah pada Peta di desa {self.cmb_desa.currentText()}\nLanjutkan proses?"
        result = QtWidgets.QMessageBox.question(self, "Perhatian", msg)
        if result == QtWidgets.QMessageBox.No:
            return

        # Persil Baru
        success = []
        error_set = set()
        for mp in self._bs_multi_persil:
            wilayah = self.cmb_desa.currentData()
            pp = {
                "Area": round(mp["luas"], 3),
                "Boundary": mp["batas"],
                "Text": mp["text"],
                "Height": mp["height"],
                "Rotation": mp["rotation"],
                "KantorId": self._kantor_id,
                "UserUpdate": pegawai["userId"],
                "WilayahId": wilayah["DESAID"]
            }

            result = ""
            if mp["nib"] != "-":
                pp["Label"] = mp["nib"]
                response = endpoints.update_geometry_persil_by_nib_sdo(pp)
                result = response.content.decode("utf-8")
                mp["keterangan"] = "LinkNib"

            if result != "OK" and mp["hak"]:
                pp["Label"] = mp["hak"]
                response = endpoints.update_geometry_persil_by_hak_sdo(pp)
                result = response.content.decode("utf-8")
                mp["keterangan"] = "LinkHak"

            if result != "OK" and mp["su"]:
                pp["Label"] = mp["su"]
                response = endpoints.update_geometry_persil_by_su_sdo(pp)
                result = response.content.decode("utf-8")
                mp["keterangan"] = "LinkSu"

            print(result)

            if result == "OK":
                # TODO: bintang
                coord = [
                    mp["point"].x(),
                    mp["point"].y()
                ]
                success.append(coord)
            else:
                mp["keterangan"] = result
                error_set.add(result)

        if success:
            add_bintang(success)
        # else:
        #     QtWidgets.QMessageBox.warning(
        #         None, "Perhatian", "\n".join(error_set)
        #     )
        #     return
        self._render_to_table(self._bs_multi_persil)

    def _btn_select_click(self):
        # check topo
        layers = select_layer_by_regex(r"^\((08020(1|2|3))\)*")
        selected_features = {}
        for layer in layers:
            key = layer.id()
            features = list(layer.selectedFeatures())
            selected_features[key] = features

        if not selected_features:
            QtWidgets.QMessageBox.warning(
                None, "Perhatian", "Tidak ada teks terpilih"
            )
            return

        self._fill_multi_persil(selected_features)

    def _fill_multi_persil(self, selected_features):
        parcel_list = []
        jumlah_bidang = 0

        batas_persil_layers = select_layer_by_regex(r"^\(020100\)*")

        if not batas_persil_layers:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Layer batas bidang tanah (020100) tidak bisa ditemukan"
            )
            return

        for layer_id, features in selected_features.items():
            crs_index = self.cmb_coordinate_system.currentIndex()
            epsg = self._srid_code[crs_index]
            jumlah_bidang += len(features)
            for feature in features:
                oid = get_feature_object_id(layer_id, feature.id())
                point = feature.geometry().asPoint()
                print(point.x(), point.y())
                if point.x() < 32000 or point.x() > 368000 or point.y() < 282000 or point.y() > 2166000:
                    QtWidgets.QMessageBox.warning(
                        None, "Perhatian", "Koordinat diluar range TM-3"
                    )
                    return

                feature_iterator = get_polygon_by_point(batas_persil_layers[0], point)
                if not feature_iterator:
                    continue

                selected_poly = feature_iterator[0]

                teks = get_sdo_point(point, epsg)
                poli = get_sdo_polygon(selected_poly, epsg)

                if not poli["batas"]:
                    continue

                txt = feature.attribute("label") if feature.attribute("label") else ""
                height = (
                    float(feature.attribute("height"))
                    if feature.attribute("height")
                    else 1
                )
                orientation = (
                    float(feature.attribute("rotation"))
                    if feature.attribute("rotation")
                    else 0
                )

                poli_oid = get_feature_object_id(batas_persil_layers[0].id(), selected_poly.id())
                found_it = [p for p in parcel_list if p["id"] == poli_oid]
                if not found_it:
                    found_it = {
                        "id": poli_oid,
                        "idsu": "",
                        "idhak": "",
                        "nib": "",
                        "hak": "",
                        "su": "",
                        "keterangan": "",
                        "luas": poli["luas"],
                        "batas": poli["batas"],
                        "text": teks,
                        "height": height,
                        "rotation": orientation,
                        "point": point
                    }
                    parcel_list.append(found_it)

                if layer_id.startswith("_080201_"):
                    str_pattern = r"^(?!00000)[0-9]{5}$"
                    if txt:
                        if not re.match(str_pattern, txt):
                            found_it["keterangan"] = "salah nib"
                        found_it["nib"] = txt
                elif layer_id.startswith("_080202_"):
                    str_pattern = r"^(SU|GS|SUS|PLL|GT)[.](?!00000)[0-9]{5}[/](19|20)[0-9]{2}$"
                    if txt:
                        if not re.match(str_pattern, txt):
                            found_it["keterangan"] = "salah su"
                        found_it["idsu"] = oid
                        found_it["su"] = txt
                else:
                    str_pattern = r"^[MUBPLW][.]((?!0)[0-9]{1,5})$"
                    if txt:
                        if not re.match(str_pattern, txt):
                            found_it["keterangan"] = "salah hak"
                        found_it["idhak"] = oid
                        found_it["hak"] = txt

        self._bs_multi_persil = parcel_list
        self.tssl_status.setText(f"Jumlah Bidang: {jumlah_bidang}")
        self._render_to_table(parcel_list)

    def _render_to_table(self, parcel_list):
        # render to table
        dataset = Dataset()
        table = dataset.add_table("persil")
        table.add_column("NIB")
        table.add_column("Hak")
        table.add_column("Surat Ukur")
        table.add_column("Luas")
        table.add_column("Keterangan")

        for parcel in parcel_list:
            row = table.new_row()
            row["NIB"] = parcel["nib"]
            row["Hak"] = parcel["hak"]
            row["Surat Ukur"] = parcel["su"]
            row["Luas"] = round(parcel["luas"], 2)
            row["Keterangan"] = parcel["keterangan"]

        table.render_to_qtable_widget(
            table_widget=self.dgv_parcel_by_nib
        )

    def _btn_select_all_click(self):
        layers = select_layer_by_regex(r"^\((08020(1|2|3))\)*")
        selected_features = {}
        for layer in layers:
            key = layer.id()
            features = list(layer.getFeatures())
            selected_features[key] = features

        if not selected_features:
            QtWidgets.QMessageBox.warning(
                None, "Perhatian", "Tidak ada teks terpilih"
            )
            return

        self._fill_multi_persil(selected_features)
