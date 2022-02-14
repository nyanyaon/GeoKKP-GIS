from asyncio.windows_events import NULL
from contextlib import nullcontext
import os
import json
import re
from urllib import response


from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.utils import iface
from qgis.core import QgsRectangle
from qgis.core import (
    QgsProject,
    QgsPointXY,
    QgsFeature,
    QgsGeometry,
    QgsVectorLayer,
    Qgis,
)
from qgis.core import QgsRectangle, QgsMapLayer
from qgis.gui import QgsVertexMarker, QgsMapTool, QgsRubberBand
from .api import endpoints
from .utils import readSetting, get_epsg_from_tm3_zone, get_layer_config, sdo_to_layer
from .models.dataset import Dataset
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
        self.nud_radius.setText("100")
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
        print(x, y)
        layers = self.canvas.layers()
        w = self.canvas.mapUnitsPerPixel() * 3
        rect = QgsRectangle(x - w, y - w, x + w, y + w)
        for layer in layers:
            if layer.type() == QgsMapLayer.RasterLayer:
                continue
            lRect = self.canvas.mapSettings().mapToLayerCoordinates(layer, rect)
            layer.selectByRect(lRect, False)
        self.canvas.scene().removeItem(self.vm_1)
        self.point_tool_1.deactivate()
        self.canvas.unsetMapTool(self.point_tool_1)
