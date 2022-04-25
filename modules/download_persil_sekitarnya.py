from audioop import mul
import math
import os
import json
import re
from tokenize import Double
from urllib import response


from qgis.PyQt import QtWidgets, uic

from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.utils import iface
from qgis.core import QgsRectangle
from qgis.core import (
    QgsProject,
)
from qgis.core import QgsRectangle, QgsMapLayer
from qgis.gui import QgsVertexMarker, QgsMapTool
from .api import endpoints
from .utils import readSetting, get_epsg_from_tm3_zone, get_layer_config, sdo_to_layer
from .maptools import MapTool

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/download_persil_sekitarnya.ui")
)


class DownloadPersilSekitar(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(DownloadPersilSekitar, self).__init__(parent)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.setupUi(self)

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

        self.list_vm = []

        self.cmb_propinsi.currentIndexChanged.connect(
            self._cmb_propinsi_selected_index_changed
        )
        self.cmb_kabupaten.currentIndexChanged.connect(
            self._cmb_kabupaten_selected_index_changed
        )
        self.cmb_kecamatan.currentIndexChanged.connect(
            self._cmb_kecamatan_selected_index_changed
        )
        self.radius.setText("100")
        self.btn_titik_tengah.clicked.connect(self.btnDownload_Click)

        self.setup_workpanel()

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

        self.cmb_coordinate_system.clear()
        self.cmb_coordinate_system.addItem("TM3-46.2",84.5)
        self.cmb_coordinate_system.addItem("TM3-47.1",87.5)
        self.cmb_coordinate_system.addItem("TM3-47.2",90.5)
        self.cmb_coordinate_system.addItem("TM3-48.1",93.5)
        self.cmb_coordinate_system.addItem("TM3-48.2",96.5)
        self.cmb_coordinate_system.addItem("TM3-49.1",99.5)
        self.cmb_coordinate_system.addItem("TM3-49.2",112.5)
        self.cmb_coordinate_system.addItem("TM3-50.1",115.5)
        self.cmb_coordinate_system.addItem("TM3-50.2",118.5)
        self.cmb_coordinate_system.addItem("TM3-51.1",121.5)
        self.cmb_coordinate_system.addItem("TM3-51.2",124.5)
        self.cmb_coordinate_system.addItem("TM3-52.1",127.5)
        self.cmb_coordinate_system.addItem("TM3-52.2",130.5)
        self.cmb_coordinate_system.addItem("TM3-53.1",133.5)
        self.cmb_coordinate_system.addItem("TM3-53.2",136.5)
        self.cmb_coordinate_system.addItem("TM3-54.1",139.5)

        self.cmb_coordinate_system.setCurrentIndex(7)

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

    def create_vertex_marker(self, type="CROSS"):
        vm = QgsVertexMarker(self.canvas)

        vm.setPenWidth(3)
        vm.setIconSize(7)
        return vm

    def btnDownload_Click(self):
        self.active = False
        QgsMapTool.__init__(self, self.canvas)

        self.vm_1 = self.create_vertex_marker()
        self.point_tool_1 = MapTool(self.canvas, self.vm_1)
        self.point_tool_1.map_clicked.connect(self.update_titik_1)
        self.canvas.setCursor(Qt.CrossCursor)
        self.canvas.setMapTool(self.point_tool_1)
        
    def update_titik_1(self, x, y):
        layers = self.canvas.layers()
        w = self.canvas.mapUnitsPerPixel() * 3
        rect = QgsRectangle(x - w, y - w, x + w, y + w)

        srid = self.cmb_coordinate_system.currentIndex()
        srs = str(self.srid_code[srid])
        lintang = self.cmb_coordinate_system.currentData()

        nilaiRadius = float(self.radius.text())
        print(nilaiRadius)
        hitungBawah = 0
        hitungAtas = 0

        for layer in layers:
            if layer.type() == QgsMapLayer.RasterLayer:
                continue
            lRect = self.canvas.mapSettings().mapToLayerCoordinates(layer, rect)
            layer.selectByRect(lRect, False)
            features = layer.selectedFeatures()
            if(features != []):
                koordinatX = features[0].geometry().centroid().asPoint().x()
                koordinatY = features[0].geometry().centroid().asPoint().y()
                hitungBawah = self.worldCoordinate(6378137,0.0033528106646687913,0.9999,200000,1500000,lintang,0,koordinatX-nilaiRadius,koordinatY-nilaiRadius)
                hitungAtas = self.worldCoordinate(6378137,0.0033528106646687913,0.9999,200000,1500000,lintang,0,koordinatX+nilaiRadius,koordinatY+nilaiRadius)
            
        if(hitungBawah == 0):
            hitungBawah = self.worldCoordinate(6378137,0.0033528106646687913,0.9999,200000,1500000,lintang,0,x-nilaiRadius,y-nilaiRadius)
            hitungAtas = self.worldCoordinate(6378137,0.0033528106646687913,0.9999,200000,1500000,lintang,0,x+nilaiRadius,y+nilaiRadius)

        self.canvas.scene().removeItem(self.vm_1)
        self.point_tool_1.deactivate()
        self.canvas.unsetMapTool(self.point_tool_1)

        response = endpoints.parcel_window_sdo(str(hitungBawah["x"]),str(hitungBawah["y"]),str(hitungAtas["x"]),str(hitungAtas["y"]),str(srs))
        persil = json.loads(response.content)
        for index,persilFeature in enumerate(persil["persils"]):
            persil["persils"][index]["label"] = persilFeature["nomor"]
        self._draw(persil)
        

    def _draw(self, upr):
        # print(upr)
        crs = self.cmb_coordinate_system.currentText()
        zone = crs.replace("TM3-", "")
        epsg = get_epsg_from_tm3_zone(zone)

        if upr["persils"]:
            if upr["persils"]:
                layer_config = get_layer_config("020100")
                print(layer_config)
                layer = sdo_to_layer(
                    upr["persils"],
                    name=layer_config["Nama Layer"],
                    symbol=layer_config["Style Path"],
                    crs=epsg,
                    coords_field="boundary",
                )
        
    def worldCoordinate(self,a,flat,k0,fe,fn,LonOri,LatOri,E,N):
        fecc = 2*flat - math.pow(flat,2)
        secc = fecc / (1 - fecc)

        m0 = self.CalculateM(a,fecc,LatOri)
        m1 = m0 + (N - fn) / k0
        Mu1 = m1 / (a*(1-fecc/4 - 3*math.pow(fecc,2)/64 - 5*math.pow(fecc,3)/256))
        e1 = (1 - math.pow((1-fecc),0.5))/(1+math.pow((1-fecc),0.5))

        lat1 = Mu1 + (3*e1/2 - 27*math.pow(e1,3)/32)*math.sin(2*Mu1) + (21*math.pow(e1,2)/16 - 55*math.pow(e1,4)/32)*math.sin(4*Mu1)+(151*math.pow(e1,3)/96)*math.sin(6*Mu1)+(1097*math.pow(e1,4)/512)*math.sin(8*Mu1)
        rho1 = a * (1 - fecc)/math.pow(1-fecc*math.pow(math.sin(lat1),2),1.5)
        v1 = a / math.pow(1-fecc*math.pow(math.sin(lat1),2),0.5)

        t1 = math.pow(math.tan(lat1),2)
        c1 = secc*math.pow(math.cos(lat1),2)
        d = (E - fe ) / (v1 * k0)

        lat = lat1 - (v1*math.tan(lat1)/rho1)*(math.pow(d,2)/2 - (5+3*t1+10*c1-4*math.pow(c1,2)-9*secc)*math.pow(d,4)/24+(61+90*t1+298*c1+45*math.pow(t1,2)-25*secc-3*math.pow(c1,2))*math.pow(d,6)/720)
        lon = self.convertRadian(LonOri) + (d - (1+2*t1)*math.pow(d,3)/6+(5-2*c1+28*t1-3*math.pow(c1,2)+8*secc+24*math.pow(t1,2))*math.pow(d,5)/120)/math.cos(lat1)

        koordinat = {
            "x":lon*180/math.pi,
            "y":lat*180/math.pi
        }

        return koordinat

    def convertRadian(self,angle):
        rad = angle*math.pi/180
        return rad

    def CalculateM(self,a,fecc,LatOri):
        w = (1 - fecc/4 - 3*math.pow(fecc,2)/64 - 5*math.pow(fecc,3)/256)*self.convertRadian(LatOri)
        x = (3*fecc/8 + 3*math.pow(fecc,2)/32 + 45*math.pow(fecc,3)/1024)*math.sin(2*self.convertRadian(LatOri))
        y = (15*math.pow(fecc,2)/256 + 45*math.pow(fecc,3)/1024) * math.sin(4*self.convertRadian(LatOri))
        z = (35*math.pow(fecc,3)/3072)* math.sin(6*self.convertRadian(LatOri))
        m = a * (w-x+y-z)
        return m
