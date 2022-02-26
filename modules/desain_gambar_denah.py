import os
import json
import hashlib

from qgis.PyQt import QtWidgets, uic

from qgis.PyQt.QtCore import pyqtSignal
from PyQt5 import QtCore
from qgis.utils import iface

from .utils import get_nlp, get_nlp_index, readSetting, storeSetting
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
        pass

    def FillNewApartments(self):
        if(self._newApartments != None and len(self._newApartments) > 0 ):
            _apartemens = []
            for x in range(len(self._newApartments)):
                _apartemens.append(str(self._newApartments[x]))
            print(_apartemens,"apartemen")
            response = endpoints.get_apartments(_apartemens[0])
            dsApartemen = json.loads(response.content)
            print(dsApartemen) 
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
            table.add_column("HEIGHT")
            table.add_column("ORIENTATION")
            table.add_column("URUT")

            for p in dsApartemen["APARTEMENBARU"]:
                d_row = table.new_row()
                d_row["REGID"] = str(p["UNITRUMAHSUSUNID"])
                d_row["NOGD"] = str(p["NOMOR"])
                d_row["LUAST"] = str(p["LUASTERTULIS"])

            dataset.render_to_qtable_widget("ApartemenEdit", self.dgv_GambarDenah)

            for layer in self._current_layers:
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

                    nomor = feature.attribute("label") if feature.attribute("label") else ""
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
                        if self.dgv_GambarDenah.rowCount() > 0:
                            items = self.dgv_GambarDenah.findItems(nomor,QtCore.Qt.MatchExactly)
                            print(items[0].text(),len(items))
                            # filtered = [
                            #     f
                            #     for f in self.dgv_GambarDenah
                            #     if f["NOGD"] == nomor
                            # ]

                            # if filtered:
                            #     row = filtered[0]

      



    def GetSdoPoint(self):
        pass
    
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

  
