from operator import ne
import os
import json
import hashlib
import ast

from qgis.PyQt import QtWidgets, uic

from PyQt5 import QtCore
from qgis.utils import iface
from qgis.core import QgsProject

from .utils import get_nlp, get_nlp_index, readSetting, storeSetting, select_layer_by_regex
from .utils.geometry import get_sdo_point, get_sdo_polygon
from .api import endpoints
from .memo import app_state

from .models.dataset import Dataset

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/desain_gambar_denah.ui")
)

class DesainGambarDenah(QtWidgets.QDialog, FORM_CLASS):

    def __init__(
        self,
        importGambarDenah,
        nomorBerkas,
        tahunBerkas,
        kantorId,
        tipeBerkas,
        guRegid,
        desaId,
        newGugusId,
        newParcelNumber,
        newApartmentNumber,
        newParcels,
        oldParcels,
        newApartments,
        oldApartments,
        gantiDesa,
        current_layers = [],
        parent=iface.mainWindow()):
        
        
        super(DesainGambarDenah, self).__init__(parent)
        self.setupUi(self)

        self._nomorBerkas=nomorBerkas
        self._tahunBerkas=tahunBerkas
        self._tipeBerkas=tipeBerkas
        self._guRegid=guRegid
        self._desaId=desaId
        self._gantiDesa=gantiDesa
        self._kantorId=kantorId
        self._oldParcels=oldParcels
        self._newParcels=newParcels
        self._oldApartments=oldApartments
        self._newApartments=newApartments
        self._newParcelNumber=int(newParcelNumber)
        self._newApartmentNumber=int(newApartmentNumber)
        self._newGugusId=newGugusId
        self._importGambarDenah = importGambarDenah
        self._current_layers = current_layers

        self.cmb_propinsi.currentIndexChanged.connect(
            self._cmb_propinsi_selected_index_changed
        )
        self.cmb_kabupaten.currentIndexChanged.connect(
            self._cmb_kabupaten_selected_index_changed
        )
        self.cmb_kecamatan.currentIndexChanged.connect(
            self._cmb_kecamatan_selected_index_changed
        )

    

        self.firstLoadProp = True
        self.firstLoadKabu = True
        self.firstLoadKeca = True
        self.firstLoadDesa = True

        self.setup_workpanel()

    def CreateDataSetIntegration(self):
        dataset = Dataset()

        table = dataset.add_table("PersilBaru")
        table.add_column("OID")
        table.add_column("LABEL")
        table.add_column("AREA")
        table.add_column("BOUNDARY")
        table.add_column("TEXT")
        table.add_column("KETERANGAN")
        table.add_column("HEIGHT")
        table.add_column("ORIENTATION")

        table = dataset.add_table("PersilEdit")
        table.add_column("OID")
        table.add_column("REGID")
        table.add_column("NIB")
        table.add_column("LUAST")
        table.add_column("LABEL")
        table.add_column("AREA")
        table.add_column("BOUNDARY")
        table.add_column("TEXT")
        table.add_column("KETERANGAN")
        table.add_column("HEIGHT")
        table.add_column("ORIENTATION")

        table = dataset.add_table("PersilInduk")
        table.add_column("OID")
        table.add_column("REGID")
        table.add_column("NIB")
        table.add_column("LUAST")
        table.add_column("LABEL")
        table.add_column("AREA")
        table.add_column("BOUNDARY")
        table.add_column("TEXT")
        table.add_column("KETERANGAN")
        table.add_column("HEIGHT")
        table.add_column("ORIENTATION")

        table = dataset.add_table("PersilMati")
        table.add_column("REGID")
 
        table = dataset.add_table("ApartemenBaru")
        table.add_column("OID")
        table.add_column("LABEL")
        table.add_column("AREA")
        table.add_column("BOUNDARY")
        table.add_column("TEXT")
        table.add_column("KETERANGAN")
        table.add_column("HEIGHT")
        table.add_column("ORIENTATION")
        table.add_column("URUT")

        table = dataset.add_table("Poligon")
        table.add_column("Key")
        table.add_column("Type")
        table.add_column("Label")
        table.add_column("Height")
        table.add_column("Orientation")
        table.add_column("BOUNDARY")
        table.add_column("Text")

        table = dataset.add_table("Garis")
        table.add_column("KEY")
        table.add_column("TYPE")
        table.add_column("LINE")

        table = dataset.add_table("Teks")
        table.add_column("Key")
        table.add_column("Type")
        table.add_column("Height")
        table.add_column("Orientation")
        table.add_column("Label")
        table.add_column("Position")
    
        table = dataset.add_table("Titik")
        table.add_column("Key")
        table.add_column("Type")
        table.add_column("PointOrientation")
        table.add_column("TextOrientation")
        table.add_column("Scale")
        table.add_column("Height")
        table.add_column("Label")
        table.add_column("PointPosition")
        table.add_column("TextPosition")

        table = dataset.add_table("Dimensi")
        table.add_column("Key")
        table.add_column("Type")
        table.add_column("Line")
        table.add_column("Initialpoint")
        table.add_column("Labelpoint")
        table.add_column("Endpoint")
        table.add_column("Initialorientation")
        table.add_column("Labelorientation")
        table.add_column("Endorientation")
        table.add_column("Height")
        table.add_column("Label")

    def setup_workpanel(self):
        kantor = readSetting("kantorterpilih", {})
        if not kantor:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih lokasi kantor lebih dahulu"
            )
            return

        self._kantor_id = kantor["kantorID"]
        self._tipe_kantor_id = str(kantor["tipeKantorId"])
        self.btn_proses.setEnabled(False)

        self.btn_validasi.clicked.connect(self.btnValidate_Click)
        self.btn_proses.clicked.connect(self.btnProcess_Click)

        self._set_cmb_propinsi()

        if(self.firstLoadProp):
            self._set_cmb_kabupaten
            self.firstLoadProp=False

        if(self._importGambarDenah):
            self.cmb_lihat_data.addItem("Apartemen Baru")
            self.FillApartemenDataTableAutomatically()
            self.cmb_lihat_data.setCurrentIndex(0)
            self._currentParcelTable = "ApartemenBaru"
       
        else:
            self.cmb_lihat_data.addItem("Apartemen Edit")
            self._currentParcelTable = "ApartemenEdit"
            self.cmb_lihat_data.setCurrentIndex(0)
            self.FillNewApartments()
            self.cmb_propinsi.setEnabled(False)
            self.cmb_kabupaten.setEnabled(False)
            self.cmb_kecamatan.setEnabled(False)
            self.cmb_desa.setEnabled(False)

    def FillApartemenDataTableAutomatically(self):
        # replacing_qgisproject
        layers = select_layer_by_regex(r"^\(020110\)*")
        if not layers:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Layer Apartemen (020110) tidak bisa ditemukan"
            )
            return
        self._layer = layers[0]

        features = self._layer.getFeatures()
        print(features,"features")

        field_index = self._layer.fields().indexOf("key")
        print("field_index", field_index)

        dataset = Dataset()
        table = dataset.add_table("ApartemenBaru")
        table.add_column("OID")
        table.add_column("LABEL")
        table.add_column("AREA")
        table.add_column("BOUNDARY")
        table.add_column("TEXT")
        table.add_column("KETERANGAN")
        table.add_column("HEIGHT")
        table.add_column("ORIENTATION")
        table.add_column("URUT")

        for feature in features:
            identifier = f"{self._layer.id()}|{feature.id()}".encode("utf-8")
            objectid = hashlib.md5(identifier).hexdigest().upper()

            
            self._layer.startEditing()
            self._layer.changeAttributeValue(
                feature.id(), field_index, objectid
                )
            self._layer.commitChanges()

            point = feature.geometry().pointOnSurface().asPoint()
            teks = get_sdo_point(point)
            poli = get_sdo_polygon(feature)

            if not poli["batas"]:
                    continue

            try:
                height = float(feature.attribute("height"))
            except:
                height = 0

            try:
                orientation = float(feature.attribute("rotation"))
            except:
                orientation = 0

            # orientation = (
            #     float(feature.attribute("rotation"))
            #     if feature.attribute("rotation")
            #     else 0
            # )
            luas_round = str(round(poli["luas"], 3))

            d_row = table.new_row()
            d_row["OID"] = objectid
            d_row["AREA"] = luas_round
            d_row["LABEL"] = ""
            d_row["BOUNDARY"] = poli["batas"]
            d_row["TEXT"] = teks
            d_row["KETERANGAN"] = "Tunggal"
            d_row["HEIGHT"] = height
            d_row["ORIENTATION"] = orientation
            try:
                d_row["URUT"]= int(
                    teks.replace("#", "")
                )
            except:
                d_row["URUT"] = 0

        dataset.render_to_qtable_widget("ApartemenBaru", self.dgv_GambarDenah , [3,4])

    def FillNewApartments(self):
        if(self._newApartments != None and len(self._newApartments) > 0 ):
            _apartemens = []
            for x in range(len(self._newApartments)):
                _apartemens.append(str(self._newApartments[x]))
            print(_apartemens,"apartemen")
            response = endpoints.get_apartments(_apartemens[0])
            dsApartemen = json.loads(response.content)
            print(dsApartemen) 

            # replacing_qgisproject
            layers = select_layer_by_regex(r"^\(020110\)*")
            if not layers:
                QtWidgets.QMessageBox.warning(
                    None, "Kesalahan", "Layer Apartemen (020110) tidak bisa ditemukan"
                )
                return
            layer = layers[0]

            features = layer.getFeatures()
            print(features,"features")

            dataset = Dataset()
            table = dataset.add_table("ApartemenEdit")
            table.add_column("OID")
            table.add_column("REGID")
            table.add_column("NOGD")
            table.add_column("LUAST")
            table.add_column("LABEL")
            table.add_column("AREA")
            table.add_column("BOUNDARY")
            table.add_column("TEXT")
            table.add_column("KETERANGAN")
            table.add_column("HEIGHT")
            table.add_column("ORIENTATION")

            for p in dsApartemen["APARTEMENBARU"]:
                d_row = table.new_row()
                d_row["REGID"] = str(p["UNITRUMAHSUSUNID"])
                d_row["NOGD"] = str(p["NOMOR"])
                d_row["LUAST"] = str(p["LUASTERTULIS"])

            dataset.render_to_qtable_widget("ApartemenEdit", self.dgv_GambarDenah,[5,6,7])

        
            for feature in features:

                identifier = f"{layer.id()}|{feature.id()}".encode("utf-8")
                objectid = hashlib.md5(identifier).hexdigest().upper()

                point = feature.geometry().pointOnSurface().asPoint()
                teks = get_sdo_point(point)
                poli = get_sdo_polygon(feature)

                key = feature.attribute("key") if feature.attribute("key") else ""
                label = feature.attribute("label") if feature.attribute("label") else ""

                luas_round = str(round(poli["luas"], 3))

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
            
                if poli["batas"]:
                    row = {}
                    if self.dgv_GambarDenah.rowCount() > 0:
                        items = self.dgv_GambarDenah.findItems(key,QtCore.Qt.MatchExactly)
                        if(items != []):
                            row = items[0].row()
                            print(row)
                            self.dgv_GambarDenah.setItem(row,0,QtWidgets.QTableWidgetItem(objectid))
                            self.dgv_GambarDenah.setItem(row,4,QtWidgets.QTableWidgetItem(label))
                            self.dgv_GambarDenah.setItem(row,5,QtWidgets.QTableWidgetItem(luas_round))
                            self.dgv_GambarDenah.setItem(row,6,QtWidgets.QTableWidgetItem(str(poli["batas"])))
                            self.dgv_GambarDenah.setItem(row,7,QtWidgets.QTableWidgetItem(str(teks)))
                            self.dgv_GambarDenah.setItem(row,8,QtWidgets.QTableWidgetItem("Tunggal"))
                            self.dgv_GambarDenah.setItem(row,9,QtWidgets.QTableWidgetItem(height))
                            self.dgv_GambarDenah.setItem(row,10,QtWidgets.QTableWidgetItem(orientation))
                        else:
                            total_row = self.dgv_GambarDenah.rowCount()
                            self.dgv_GambarDenah.insertRow(total_row)
                            print(total_row)
                            self.dgv_GambarDenah.setItem(total_row,0,QtWidgets.QTableWidgetItem(objectid))
                            self.dgv_GambarDenah.setItem(total_row,1,QtWidgets.QTableWidgetItem(""))
                            self.dgv_GambarDenah.setItem(total_row,2,QtWidgets.QTableWidgetItem(""))
                            self.dgv_GambarDenah.setItem(total_row,3,QtWidgets.QTableWidgetItem(""))
                            self.dgv_GambarDenah.setItem(total_row,4,QtWidgets.QTableWidgetItem(label))
                            self.dgv_GambarDenah.setItem(total_row,5,QtWidgets.QTableWidgetItem(luas_round))
                            self.dgv_GambarDenah.setItem(total_row,6,QtWidgets.QTableWidgetItem(str(poli["batas"])))
                            self.dgv_GambarDenah.setItem(total_row,7,QtWidgets.QTableWidgetItem(str(teks)))
                            self.dgv_GambarDenah.setItem(total_row,8,QtWidgets.QTableWidgetItem("Tunggal"))
                            self.dgv_GambarDenah.setItem(total_row,9,QtWidgets.QTableWidgetItem(height))
                            self.dgv_GambarDenah.setItem(total_row,10,QtWidgets.QTableWidgetItem(orientation))

    def _cmb_propinsi_selected_index_changed(self, index):
        self._set_cmb_kabupaten()

    def _cmb_kabupaten_selected_index_changed(self, index):
        self._set_cmb_kecamatan()

    def _cmb_kecamatan_selected_index_changed(self, index):
        self._set_cmb_desa()

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
            self.cmb_desa.addItem(des["DESANAMA"], des["DESAID"])

    def btnValidate_Click(self):
        valid =True
        msg = ""

        if(self.validateCoordsExtend() == False):
            valid = False
            if(self.chb_Sistem_Koordinat.isChecked()):
                msg = "Koordinat diluar TM3!"
            else:
                msg = "Koordinat diluar area penggambaran"

        print(self.dgv_GambarDenah.rowCount(),len(self._newApartments) ,self._newApartmentNumber)
        
        if(self._newApartmentNumber > 0):
            if(self.dgv_GambarDenah.rowCount() + len(self._newApartments) > self._newApartmentNumber):
                sisa = self._newApartmentNumber - len(self._newApartments)
                msg = f"Jumlah Apartemen baru tidak sesuai \nAnda telah memasukkan {str(len(self._newApartments))} unit rumah susun ke dalam berkas {self._nomorBerkas}/{self._tahunBerkas} \nHanya {str(sisa)} unit rumah susun lagi yang bisa dimasukkan ke berkas tersebut"
                valid = False

        if(self.cmb_lihat_data.currentText() == "Apartemen Edit"):
            self.dgv_GambarDenah.setColumnHidden(0, False)
            for x in range(self.dgv_GambarDenah.rowCount()):
                if self.dgv_GambarDenah.item(x,2).text() is None:
                    valid = False
                    msg = "Ada Apartemen yang tidak memiliki geometri!"
                    break
                if self.dgv_GambarDenah.item(x,6).text() is None:
                    valid = False
                    msg = "Ada Apartemen yang tidak memiliki REGID!"
                    break
            self.dgv_GambarDenah.setColumnHidden(0, True)

        if valid:
            self.btn_proses.setEnabled(True)
            self.label_status_l.setText("Lakukan Integrasi")
        else:
            self.label_status_l.setText("Ada kesalahan, cek error log")
            self.error_log.setText(msg)
            self.tabWidget.setCurrentIndex(1)

    def validateCoordsExtend(self):
        # replacing_qgisproject
        layers = select_layer_by_regex(r"^\(020110\)*")
        if not layers:
            QtWidgets.QMessageBox.warning(
                None, "Kesalahan", "Layer Apartemen (020110) tidak bisa ditemukan"
            )
            return
        layer = layers[0]
        ext = layer.extent()

        retval = True

        xmin = ext.xMinimum()
        xmax = ext.xMaximum()
        ymin = ext.yMinimum()
        ymax = ext.yMaximum()

        print(xmin,xmax,ymin,ymax)

        if(self.chb_Sistem_Koordinat.isChecked()):
            if(xmin<32000 or xmax > 368000  or ymin < 282000  or ymax > 2166000  ):
                retval = False
        else:
            if(xmin<-2200000 or xmax > 2200000 or ymin < -2200000 or ymax > 2200000 ):
                retval = False

        return retval

    def btnProcess_Click(self):
        prmpt = ""
        if(self.cmb_desa.currentData() is not None):
            prmpt = f"Anda akan melakukan integrasi Unit Rumah Susun di Desa {self.cmb_desa.currentText()}, kecamatan {self.cmb_kecamatan.currentText()}"
            self._desaId = self.cmb_desa.currentData()
        else:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih desa terlebih dahulu!"
            )
            return

        if(self.dgv_GambarDenah.rowCount() > 0):

            result = QtWidgets.QMessageBox.question(self, "Perhatian", prmpt)

            if(result != QtWidgets.QMessageBox.Yes):
                return

            self._newGugusId = ""
        
        skb = ""
        if(self.chb_Sistem_Koordinat.isChecked()):
            skb = "TM3"
        else:
            skb = "NonTM3"

        list_data = []
        self._sts = {}
        self.dgv_GambarDenah.setColumnHidden(0, False)

        if(self.cmb_lihat_data.currentText() == "Apartemen Baru"):
            print(self.dgv_GambarDenah.rowCount())
            for x in range(self.dgv_GambarDenah.rowCount()):
                boundary =  str(self.dgv_GambarDenah.item(x,3).text())
                text = str(self.dgv_GambarDenah.item(x,4).text())
                temp = {
                    "OID": self.dgv_GambarDenah.item(x,0).text(),
                    "Label": self.dgv_GambarDenah.item(x,1).text(),
                    "Area": float(str(self.dgv_GambarDenah.item(x,2).text()).replace(",", ".")),
                    "Boundary": ast.literal_eval(boundary) ,
                    "Text": ast.literal_eval(text),
                    "Keterangan": self.dgv_GambarDenah.item(x,5).text(),
                    "Height": float(str(self.dgv_GambarDenah.item(x,6).text()).replace(",", ".")),
                    "Orientation": float(str(self.dgv_GambarDenah.item(x,7).text()).replace(",", ".")),
                }
                list_data.append(temp)
            self._sts["ApartemenBaru"] = list_data
        else:
            for x in range(self.dgv_GambarDenah.rowCount()):
                boundary =  str(self.dgv_GambarDenah.item(x,6).text())
                text = str(self.dgv_GambarDenah.item(x,7).text())
                temp = {
                    "OID": self.dgv_GambarDenah.item(x,0).text(),
                    "REGID": self.dgv_GambarDenah.item(x,1).text(),
                    "NOGD": self.dgv_GambarDenah.item(x,2).text(),
                    "Luast": float(str(self.dgv_GambarDenah.item(x,3).text()).replace(",", ".")),
                    "Label": self.dgv_GambarDenah.item(x,4).text(),
                    "Area": float(str(self.dgv_GambarDenah.item(x,5).text()).replace(",", ".")),
                    "Boundary": ast.literal_eval(boundary) ,
                    "Text": ast.literal_eval(text),
                    "Keterangan": self.dgv_GambarDenah.item(x,8).text(),
                    "Height": float(str(self.dgv_GambarDenah.item(x,9).text()).replace(",", ".")),
                    "Orientation": float(str(self.dgv_GambarDenah.item(x,10).text()).replace(",", ".")),
                }
                list_data.append(temp)
            self._sts["ApartemenEdit"] = list_data

        self._fill_entity_datatable()
        self._fill_text_entity()
        self._fill_point_entity()
        self._fill_dimensi_entity()

        user = app_state.get("pegawai", {})
        
        user_id = (
            user.value["userId"]
            if user.value and "userId" in user.value.keys() and user.value["userId"]
            else ""
        )

        self._wilayahId = self.cmb_desa.currentData()

        response = endpoints.submit_sdo(
                self._nomorBerkas,
                self._tahunBerkas,
                self._kantorId,
                self._tipe_kantor_id,
                self._wilayahId,
                user_id,
                user_id,
                self._newGugusId,
                self._guRegid,
                skb,
                "",
                False,
                self._sts,
            )
        ds = json.loads(response.content)
        print(ds)

        if not ds:
            QtWidgets.QMessageBox.critical(
                None,
                "Integrasi",
                "Integrasi gagal!\nCek service berkas spatial di server sudah dijalankan!",
            )

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
        
        field_index = self._layer.fields().indexOf("label")
        key = self._layer.fields().indexOf("key")
        print("field_index", field_index)
        features = self._layer.getFeatures()

        for feature in features:

            self._layer.startEditing()
            for apartemen in ds["PersilBaru"]:
                if(feature.attributes()[key] == apartemen["oid"]):
                    self._layer.changeAttributeValue(
                        feature.id(), field_index, apartemen["nib"]
                )
            self._layer.commitChanges()

        QtWidgets.QMessageBox.information(
                None,
                "GeoKKP Web",
                "Unit Rumah Susun telah disimpan dalam database",
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



        

        
        


  
