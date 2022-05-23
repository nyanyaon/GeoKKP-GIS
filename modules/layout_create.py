from enum import Flag
import os

from .models.dataset import Dataset
from .api import endpoints

from qgis.PyQt import QtWidgets, uic, QtXml
from qgis.core import QgsProject, QgsPrintLayout, QgsReadWriteContext, Qgis, QgsExpressionContextUtils

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.gui import QgsMessageBar

# using utils
from .utils import icon, readSetting

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/layout_create.ui")
)


class CreateLayoutDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Layouting"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        """
        TODO :
        __init__(self, need_dok_pengukuran_id, variables, parent=iface.mainWindow())

        need_dok_pengukuran_id : butuh dokumenPengukuranId tidak?
        jika ya:
            string dokumenPengukuranid,
            ArrayList newParcels,
            bool hitungLembar,
            bool isRutin
        jika tidak, maka variables berupa:
            string tipeBerkas,
            ArrayList newParcels,
            ArrayList newApartment,
            string berkasId,
            string nomorBerkas,
            string tahunBerkas,
            string kodeSpopp,
            bool hitungLembar,
            bool isRutin
        """

        super(CreateLayoutDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(icon("icon.png"))

        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.project = QgsProject.instance()
        # self.read_settings()
        self.variables_to_set = None

        self.layout_data = readSetting("layout")

        self.cb_layout_type.currentIndexChanged.connect(self.pick_size)
        self.cb_layout_size.currentIndexChanged.connect(self.pick_layout)

        self.cb_layout_scale.clear()
        self.cb_layout_scale.addItem("250", 250)
        self.cb_layout_scale.addItem("500", 500)
        self.cb_layout_scale.addItem("750", 750)
        self.cb_layout_scale.addItem("1000", 1000)
        self.cb_layout_scale.addItem("2500", 2500)
        self.cb_layout_scale.addItem("10000", 10000)

        # if need_dok_pengukuran_id == True:
        #     self._dokumen_pengukuran_id = variables["dokumenPengukuranid"],
        #     self._new_parcels = variables["newParcels"]
        #     self._hitung_lembar = variables["hitungLembar"]
        #     self._is_rutin = variables["isRutin"]
        # elif need_dok_pengukuran_id == False:
        #     self._tipe_berkas = variables["tipeBerkas"]
        #     self._new_parcels = variables["newParcels"]
        #     self._new_apartment = variables["newApartment"]
        #     self._berkas_id = variables["berkasId"]
        #     self._nomor_berkas = variables["nomorBerkas"]
        #     self._tahun_berkas = variables["tahunBerkas"]
        #     self._kode_spopp = variables["kodeSpopp"]
        #     self._hitung_lembar = variables["hitungLembar"]
        #     self._is_rutin = variables["isRutin"]
        # else:
            
        self.tipe_layout()
        # TODO self.print_list_load()
        # self.pick_size()
        # self.pick_layout()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
    
    # TODO create print list for features
    # def print_list_load(self):
    #     self.table_cetak.clear()
    #     self.table_cetak.setRowCount(0)
    #     self.table_cetak.setColumnCount(0)

    #     print (self._new_parcels)
    #     if not self._is_rutin:
    #         # self.btn_create_pbt.setVisible(False)
    #         # self.btn_print.setVisible(True)
    #         if self._new_parcels:
    #             response = endpoints.get_parcels(self._new_parcels)
    #             print(response.content())
    #             ds_persil = Dataset(response.content())
    #             ds_persil.render_to_qtable_widget("PERSILBARU",self.table_cetak,[0,2,3,4,5])

    #     # TODO elif tipe berkas = "DAG"
    #     else:
    #         if self._new_parcels:
    #             response = endpoints.get_parcels(self._new_parcels)
    #             print(response.content())
    #             ds_persil = Dataset(response.content())
    #             ds_persil.render_to_qtable_widget("PERSILBARU",self.table_cetak,[0,2,3,4,5])

    def tipe_layout(self):
        self.cb_layout_type.clear()
        tipe_layout = []
        for key, values in self.layout_data.items():
            tipe_layout.append(key)
        self.cb_layout_type.addItems(tipe_layout)

    def pick_size(self):
        self.cb_layout_size.clear()
        choosen_layout = self.cb_layout_type.currentText()
        ukuran_layout = []
        for key, value in self.layout_data.items():
            if key == choosen_layout:
                for layout_size in value:
                    ukuran_layout.append(layout_size["Ukuran"])
        self.cb_layout_size.addItems(ukuran_layout)

    def pick_layout(self):
        choosen_layout = self.cb_layout_type.currentText()
        choosen_size = self.cb_layout_size.currentText()
        for key, value in self.layout_data.items():
            if key == choosen_layout:
                for item in value:
                    if item["Ukuran"] == choosen_size:
                        self.layout_name = item["Lokasi"]
        self.layout_path_default = os.path.join(
            os.path.dirname(__file__), "../template/", self.layout_name
        )
        layout, layout_exist = self.read_layout(self.layout_path_default)

    def read_layout(self, layout_path):
        layout_exist = False
        layout = None
        project = QgsProject.instance()
        if os.path.exists(layout_path):
            layout = QgsPrintLayout(project)
            with open(layout_path) as qpt_file:
                qpt_content = qpt_file.read()
            doc = QtXml.QDomDocument()
            doc.setContent(qpt_content)

            layout_items, _ = layout.loadFromTemplate(doc, QgsReadWriteContext())
            # check if there is any layout with the same name
            for existing_layout in self.project.layoutManager().printLayouts():
                if existing_layout.name() == layout.name():
                    layout_exist = True
                    layout = existing_layout
        # else:
        # TODO : "Warning", "Template default tidak ditemukan pada direktori plugin."

        return layout, layout_exist
    
    def set_project_variable(self, variables):
        if not variables:
            return
        for var in variables:
            QgsExpressionContextUtils.setProjectVariable(var,variables[var])

    def on_btn_open_layout_pressed(self):
        # add project variables
        # TODO add project variables
        self.set_project_variable(self.variables_to_set)

        qpt_path = self.layout_path_default
        layout, layout_exist = self.read_layout(qpt_path)

        if layout:
            if not layout_exist:
                self.project.layoutManager().addLayout(layout)
        else:
            return
        
        # set extent sesuai dengan fitur terpilih atau canvas
        selected_item = self.table_cetak.selectedItems()
        if selected_item:
            # TODO selected_item extent and remove the canvas extent below
            canvas = iface.mapCanvas()
            extent = canvas.extent()
            pass
        else:
            canvas = iface.mapCanvas()
            extent = canvas.extent()

        map_item = layout.itemById('muka-peta')
        # make sure that it is a map_item
        if type(map_item).__name__ == "QgsLayoutItemMap":
            # zoom to extent
            map_item.zoomToExtent(extent)
            # set scale
            selected_scale = self.cb_layout_scale.currentData()
            print(f"selected scale : {selected_scale}")
            map_item.setScale(selected_scale)
        
        # set mata angin path
        mata_angin = layout.itemById('mata-angin')
        if mata_angin and type(mata_angin).__name__ == "QgsLayoutItemPicture":
            mata_angin_path = os.path.join(os.path.dirname(__file__), "../template/north_arrow.svg")
            mata_angin.setPicturePath(mata_angin_path)
        
        # set logo bpn path
        logo_bpn = layout.itemById('logo-bpn')
        if mata_angin and type(logo_bpn).__name__ == "QgsLayoutItemPicture":
            logo_bpn_path = os.path.join(os.path.dirname(__file__), "../template/logoatrbpn.png")
            logo_bpn.setPicturePath(logo_bpn_path)

        self.iface.openLayoutDesigner(layout)
            # self.close()

    def on_btn_cancel_pressed(self):
        self.close()