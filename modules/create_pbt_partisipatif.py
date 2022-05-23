# from asyncio.windows_events import NULL
import os
import json
import hashlib

from qgis.PyQt import QtWidgets, uic, QtGui
from qgis.core import QgsProject, QgsWkbTypes, QgsVectorLayer, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/create_pbt_partisipatif.ui")
)

from .utils import readSetting, storeSetting
from .utils.geometry import get_sdo_point, get_sdo_polygon
from .api import endpoints
from .memo import app_state
from .models.dataset import Dataset


class CreatePBTPartisipatif(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Create Peta Bidang Tanah Partisipatif"""

    closingPlugin = pyqtSignal()
    DialogResult = pyqtSignal()

    def __init__(
        self,
        upr,
        tanda_terima_id,
        wilayah_id,
        gugus_id,
        nomor_tanda_terima,
        nama_desa,
        nama_kecamatan,
        jml_bidang,
        parent=iface.mainWindow()
    ):
        super(CreatePBTPartisipatif, self).__init__(parent)
        self.setupUi(self)

        self._wilayah_id = ""
        self._tanda_terima_id = ""
        self._gugus_id = ""
        self._nomor_tanda_terima = ""
        self._jml_bidang = ""
        self._nama_desa = ""
        self._nama_kecamatan = ""
        self._jml_no_nub = 0
        self._jml_setuju = 0
        self._ent_dataset = NULL
        self._ds_result_submit = NULL
        self._upr = NULL
        self._sts = NULL # SDO to submit

        self.srid_code = [
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

        self._current_kantor_id = ""
        self._current_tipe_kantor_id = ""
        
        self._wilayah_id = wilayah_id
        self._tanda_terima_id = tanda_terima_id
        self._gugus_id = gugus_id
        self._nomor_tanda_terima = nomor_tanda_terima
        self._jml_bidang = jml_bidang
        self._nama_desa = nama_desa
        self._nama_kecamatan = nama_kecamatan
        self._upr = upr
        self._parent = parent

        self._create_dataset_integration()

        self.setup_workpanel()

        self.btn_process.clicked.connect(self._btn_process_click)
        self.btn_validasi.clicked.connect(self._btn_validasi_click)
        self.btn_close.clicked.connect(self.close)

        self.cbx_diluar_wilayah.stateChanged.connect(self._cbx_diluar_wilayah_handler)
        self.cbx_tidak_lengkap.stateChanged.connect(self._cbx_tidak_lengkap_handler)
        self.cbx_overlap.stateChanged.connect(self._cbx_overlap_handler)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setup_workpanel(self):
        current_kantor = readSetting("kantorterpilih", {})
        if not current_kantor or "kantorID" not in current_kantor:
            return

        self._current_kantor_id = current_kantor["kantorID"]
        self._current_tipe_kantor_id = str(current_kantor["tipeKantorId"])

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

        # TODO: set cmb coord system same with config file
        self.cmb_coordinate_system.setCurrentIndex(7)

        self.lbl_tanda_terima.setText(self._nomor_tanda_terima)
        self.lbl_jml_bidang.setText(self._jml_bidang)
        self.lbl_nama_wilayah.setText(self._nama_desa)
        self.lbl_kecamatan.setText(self._nama_kecamatan)

        self.btn_validasi.setEnabled(True)
        self.btn_process.setEnabled(False)

        self._fill_new_rincikan()
        self._fill_persil_partisipatif()

        # TODO: sort by nub desc

        self._ent_dataset.render_to_qtable_widget("PersilPartisipatif", self.dgv_parcel, [5,6,7,8])

        # setuju = str(self._jml_setuju)
        self.lbl_jml_disetujui.setText(str(self._jml_setuju))
        ditolak = int(self._jml_bidang) - self._jml_setuju
        self.lbl_jml_ditolak.setText(str(ditolak))



    
    def _create_dataset_integration(self):
        self._ent_dataset = Dataset()

        persil_partisipatif = self._ent_dataset.add_table("PersilPartisipatif")
        persil_partisipatif.add_column("OID")
        persil_partisipatif.add_column("PERSILPMID")
        persil_partisipatif.add_column("NUB") #int
        persil_partisipatif.add_column("LUASPM")
        persil_partisipatif.add_column("AREA")
        persil_partisipatif.add_column("BOUNDARY")
        persil_partisipatif.add_column("TEXT")
        persil_partisipatif.add_column("HEIGHT")
        persil_partisipatif.add_column("ORIENTATION")
        persil_partisipatif.add_column("STATUS")
        persil_partisipatif.add_column("KETERANGAN")

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

    def _cbx_diluar_wilayah_handler(self):
        if self.cbx_diluar_wilayah.isChecked():
            self.txt_catatan.append("Diluar batas desa, ")
        else:
            text = self.txt_catatan.toPlainText()
            texts = text.replace("Diluar batas desa, ","")
            self.txt_catatan.setText(texts)

    def _cbx_tidak_lengkap_handler(self):
        if self.cbx_tidak_lengkap.isChecked():
            self.txt_catatan.append("Gambar tidak lengkap, ")
        else:
            text = self.txt_catatan.toPlainText()
            texts = text.replace("Gambar tidak lengkap, ","")
            self.txt_catatan.setText(texts)

    def _cbx_overlap_handler(self):
        if self.cbx_overlap.isChecked():
            self.txt_catatan.append("Bidang overlap, ")
        else:
            text = self.txt_catatan.toPlainText()
            texts = text.replace("Bidang overlap, ","")
            self.txt_catatan.setText(texts)

    def _fill_new_rincikan(self):
        table = self._ent_dataset["PersilPartisipatif"]
        for dr in self._upr["persils"]:
            a_row = table.new_row()
            a_row["PERSILPMID"] = dr["key"]
            a_row["NUB"] = dr["nomor"]
            a_row["LUASPM"] = dr["luasTertulis"]
            a_row["STATUS"] = "Ditolak"
        
    def _fill_persil_partisipatif(self):
        print(f"validate layer : {self._parent._validate_layers}")
        for layer in self._parent._validate_layers:
            try:
                layer.id()
            except RuntimeError:
                continue
            
            # TODO: filter for layer batas persil
            if not layer.name().startswith("(020100)"):
                print("not batas persil")
                continue

            if not "nomor" in [i.name() for i in layer.fields()]:
                continue

            features = layer.getFeatures()
            for feature in features:
                identifier = f"{layer.id()}|{feature.id()}".encode("utf-8")
                objectid = hashlib.md5(identifier).hexdigest().upper()

                nomor = feature.attribute("nomor")
                print(nomor,type(nomor))
                try:
                    nomor_int = int(nomor)
                    print("NUB INTEGER :",nomor_int)
                except:
                    QtWidgets.QMessageBox.warning(
                        None, "GeoKKP", "Nomor Urut Bidang harus angka!"
                    )
                    return

                point = feature.geometry().pointOnSurface().asPoint()
                teks = get_sdo_point(point)
                poli = get_sdo_polygon(feature)

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

                print("poli:",poli)
                if poli["batas"]:
                    dr = {}
                    if self._ent_dataset["PersilPartisipatif"].rows:
                        for index, row in enumerate(self._ent_dataset["PersilPartisipatif"].rows):
                            print("NUB :",row["NUB"],type(row["NUB"]))
                            print("nomor :",nomor,type(nomor))
                            if row["NUB"] == nomor:
                                dr = row
                        print(dr)
                    
                    luas_round = str(round(poli["luas"], 3))

                    if dr:
                        dr["OID"] = objectid
                        dr["AREA"] = luas_round
                        dr["BOUNDARY"] = poli["batas"]
                        dr["TEXT"] = teks
                        dr["HEIGHT"] = height
                        dr["ORIENTATION"] = orientation
                        dr["STATUS"] = "Diterima"
                        self._jml_setuju += 1
                    else:
                        ar = self._ent_dataset["PersilPartisipatif"].new_row()
                        ar["OID"] = objectid
                        ar["AREA"] = luas_round
                        ar["BOUNDARY"] = poli["batas"]
                        ar["TEXT"] = teks
                        ar["HEIGHT"] = height
                        ar["ORIENTATION"] = orientation
                        ar["STATUS"] = "NONUB"
                        self._jml_no_nub += 1

                else:
                    continue

    def _btn_validasi_click(self):
        valid = True
        msg = ""

        if not self._validate_extent():
            valid = False
            msg += "\nKoordinat diluar TM3!"
        
        if self._jml_no_nub > 0:
            valid = False
            msg += "\nAda bidang NUB tidak sesuai!"

        if self._jml_setuju < 1:
            valid = False
            msg += "\nTidak ada bidang yang disetujui!"

        if valid:
            self.btn_process.setEnabled(True)
            self.label_status_l.setText("Silahkan simpan data")
        else:
            self.label_status_l.setText("Ada kesalahan, cek error log")
            self.error_log.setText(msg)
            self.tab_penerimaan.setCurrentIndex(2)


    def _validate_extent(self):
        min_x = 0
        min_y = 0
        max_x = 0
        max_y = 0
        for layer in self._parent._validate_layers:
            if not layer.name().startswith("(020100)"):
                continue
            extent = layer.extent()
            min_x = min(min_x, extent.xMinimum())
            min_y = min(min_y, extent.yMinimum())
            max_x = max(max_x, extent.xMaximum())
            max_y = max(max_y, extent.xMaximum())

        return not (
            min_x < 32000 - 10000
            and max_x > 368000 + 10000
            and min_y < 282000 - 10000
            and max_y > 2166000 + 10000
        )

    def _btn_process_click(self):
        msg = f"Anda akan melakukan integrasi di {self._nama_desa} \nApakah anda akan melanjutkan?"
        dr = QtWidgets.QMessageBox.question(
            None,
            'Perhatian', 
            msg, QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No)
        if dr != QtWidgets.QMessageBox.Yes:
            return
        
        self.btn_process.setEnabled(False)
        self.btn_validasi.setEnabled(False)

        self._sts = {}
        self._fill_entity_data_table()
        self._fill_text_entity()
        # TODO:
        # self._fill_point_entity()
        # self._dimensi_entity()
        
        lspb = []
        for drow in self._ent_dataset["PersilPartisipatif"].rows:
            print(drow)
            spb = {}
            if drow["STATUS"] == "Diterima":
                spb["OID"] = drow["OID"]
                spb["Label"] = drow["NUB"]
                spb["Keterangan"] = drow["PERSILPMID"]
                spb["Area"] = float(drow["AREA"].replace(",", ".")) if drow["AREA"] else 0
                spb["Boundary"] = drow["BOUNDARY"]
                spb["Text"] = drow["TEXT"]
                spb["Height"] = drow["HEIGHT"]
                spb["Orientation"] = drow["ORIENTATION"]

                lspb.append(spb)
        
        self._sts["PersilBaru"] = lspb

        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        user_id = pegawai["userId"] if "userId" in pegawai else ""
        try:
            response = endpoints.submit_ptsl_pm_sdo(
                self._tanda_terima_id,
                self._current_kantor_id,
                self._wilayah_id,
                "",
                str(self.srid_code),
                "",
                user_id,
                str(self._jml_setuju),
                self._sts,
            )
            self._ds_result_submit = json.loads(response.content)
            print(self._ds_result_submit)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "GeoKKP", f"Spatial servis error: {str(e)}")
            return
        
        if len(self._ds_result_submit["Error"]) > 0:
            if self._ds_result_submit["Error"][0][0].startswith("Geometri persil dengan ID"):
                to_key = str(self._ds_result_submit["Error"][0][0])
                key = to_key.split("|")[1]
                oid = key

                # TODO: set label for error feature

                msg = self._ds_result_submit["Error"][0][0].replace("|", " ")
                QtWidgets.QMessageBox.critical(self, "GeoKKP", msg)
                return
            else:
                msg = self._ds_result_submit["Error"][0][0]
                QtWidgets.QMessageBox.critical(self, "GeoKKP", msg)
                return
        else:
            # TODO: self._draw_result()

            result_oid_map = {}
            for row in self._ds_result_submit["PersilBaru"]:
                result_oid_map[row["oid"]] = row["nib"]

            for layer in self._parent._validate_layers:
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
                
                # set label to fieldName "label"
                settings = QgsPalLayerSettings()
                settings.fieldName = "label"
                labeling = QgsVectorLayerSimpleLabeling(settings)
                layer.setLabeling(labeling)
                layer.triggerRepaint()
            
            self.DialogResult.emit()

            sub_msg = str(self._ds_result_submit["Sukses"][0]["message"])
            msg = f"Peta Bidang Partisipatif sukses dibuat.\n{sub_msg}\nSelanjutnya silahkan buka PBT dari panel Pelayanan Massal!"
            QtWidgets.QMessageBox.information(self, "GeoKKP", msg)
        
        self.btn_validasi.setEnabled(True)
        self.close()

    def _fill_entity_data_table(self):
        layers = self._parent._validate_layers

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

                if line and (code.startswith("08") or object_type == "GarisLain"):
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
        layers = self._parent._validate_layers

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

                if point and (code.startswith("08") or layer.name().upper().startswith("TN_")):
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





            





