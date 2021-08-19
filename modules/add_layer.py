import os
import json

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import QTreeWidgetItem
from qgis.gui import QgsRubberBand

from qgis.core import (
    QgsCoordinateTransform,
    QgsRectangle,
    QgsPoint,
    QgsPointXY,
    QgsGeometry,
    QgsWkbTypes,
    QgsProject)
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from .utils import readSetting, logMessage

# using utils
from .utils import icon

data_layer = readSetting("geokkp/layers")

data_layer2 = {"Layer Administrasi" : [
		"(10100) Batas Negara",
		"(10200) Batas Propinsi",
		"(10300) Batas Kabupaten Kotamadya",
		"(10400) Batas Kecamatan",
		"(10500) Batas Kelurahan",
		"(10600) Batas RW",
		"(10700) Batas RT"	
	],
	"Layer Kadastral": [
		"(20100) Batas Persil",
		"(20200) Batas Sub Persil",
		"(20300) Garis Garis Gambar Ukur",
		"(20400) Dimensi Pengukuran",
		"(20500) Pagar Tembok",
		"(20600) Pagar Besi",
		"(20700) Pagar Kayu",
		"(20800) Pagar Bambu",
		"(20900) Pagar Hidup"	
	],
	"Layer Perairan": [
		"(30100) Batas Sungai",
		"(30200) Garis Tengah Sungai",
		"(30300) Batas Saluran Selokan",
		"(30400) Garis Tengah Saluran Selokan",
		"(30500) Danau",
		"(30600) Rawa",
		"(30700) Empang Kolam",
		"(30800) Batas Pantai",
		"(30900) Dam",
		"(31000) Galian"
	],
	"Layer Transportasi": [
		"(40100) Batas Jalan Diperkeras",
		"(40200) Garis Tengah Jalan Diperkeras",
		"(40300) Batas Trotoar",
		"(40400) Batas Jalan Tanah",
		"(40500) Garis Tengah Jalan Tanah",
		"(40600) Batas Jalan Tanah Di Pemukiman",
		"(40700) Garis Tengah Jalan Tanah Di Pemukiman",
		"(40800) Batas Jalan Setapak Di Sawah",
		"(40900) Garis Tengah Jalan Setapak Di Sawah",
		"(41000) Batas Rel Kereta Api",
		"(41100) Garis Tengah Rel Kereta Api",
		"(41200) Batas Rel Lori",
		"(41300) Garis Tengah Rel Lori",
		"(41400) Batas Jembatan",
		"(41500) Garis Tengah Jembatan"	
	],
	"Layer Titik Tinggi Geodesi" : [
		"(50100) Titik Tinggi Geodesi BPN",
		"(50200) Titik Tinggi Geodesi Instansi Lain"	
	],
	"Layer Titik Dasar Teknis" : [
		"(60100) Titik Dasar Teknis Orde 0",
		"(60200) Titik Dasar Teknis Orde 1",
		"(60300) Titik Dasar Teknis Orde 2",
		"(60400) Titik Dasar Teknis Orde 3",
		"(60500) Titik Dasar Teknis Orde 4",
		"(60600) Titik Dasar Teknis Perapatan",
		"(60700) Titik Dasar Teknis Instansi Lain",
		"(60800) Titik Pengukuran"
	],
	"Layer Bangunan": [
		"(70100) Bangunan Rumah",
		"(70200) Bangunan Bertingkat",
		"(70300) Menara Transmisi",
		"(70400) Tiang Listrik",
		"(70500) Tiang Telepon",
		"(70600) Pipa",
		"(70700) Bangunan Tidak Permanen"
	],
	"Layer Teks": [
		"(80101) Nama Negara",
		"(80102) Nama Propinsi",
		"(80103) Nama Kabupaten Kotamadya",
		"(80104) Nama Kecamatan",
		"(80105) Nama Desa",
		"(80106) Nama RW",
		"(80107) Nama RT",
		"(80201) NIB",
		"(80202) Nomor SU",
		"(80203) Nomor Hak",
		"(80204) Kode Sub Persil",
		"(80301) Nama Sungai",
		"(80302) Nama Saluran Selokan",
		"(80303) Nama Danau",
		"(80304) Nama Rawa",
		"(80305) Nama Empang Kolam",
		"(80306) Nama Pantai",
		"(80307) Nama Dam",
		"(80308) Nama Galian",
		"(80401) Nama Jalan Diperkeras",
		"(80402) Nama Jalan Tanah",
		"(80403) Nama Jalan Setapak Di Pemukiman",
		"(80404) Nama Jalan Setapak Di Sawah",
		"(80405) Nama Rel Kereta Api",
		"(80406) Nama Rel Lori",
		"(80407) Nama Jembatan",
		"(80501) Identitas Titik Tinggi Geodesi BPN",
		"(80502) Identitas Titik Tinggi Geodesi Instansi Lain",
		"(80601) Identitas Titik Dasar Teknis Orde 0",
		"(80602) Identitas Titik Dasar Teknis Orde 1",
		"(80603) Identitas Titik Dasar Teknis Orde 2",
		"(80604) Identitas Titik Dasar Teknis Orde 3",
		"(80605) Identitas Titik Dasar Teknis Orde 4",
		"(80606) Identitas Titik Dasar Teknis Perapatan",
		"(80607) Identitas Titik Dasar Teknis Instansi Lain",
		"(80608) Identitas Titik Pengukuran",
		"(80701) Identitas Bangunan Rumah",
		"(80702) Identitas Bangunan Bertingkat",
		"(80703) Identitas Menara Transmisi",
		"(80704) Identitas Tiang Listrik",
		"(80705) Identitas Tiang Telepon",
		"(80706) Identitas Pipa",
		"(80707) Identitas Bangunan Tidak Permanen",
		"(80901) Nama Kebun",
		"(80902) Nama Sawah",
		"(80903) Nama Tegalan Tanah Kosong",
		"(80904) Nama Hutan"
	],
	"Layer Penggunaan Lahan": [
		"(90100) Kebun",
		"(90200) Sawah",
		"(90300) Tegalan Tanah Kosong",
		"(90400) Hutan"
	],
	"Layer Kontur": [
		"(100100) Garis Kontur",
		"(100200) Garis Kontur Indeks"
	],
	"Layer Citra": [
		"(120100) Layer Citra Foto Udara"
	]
}



FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/addlayerv2.ui'))


class AddLayerDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Add Layers from List """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(AddLayerDialog, self).__init__(parent)
        # self.utils = Utilities
        self.setWindowIcon(icon("icon.png"))
        
        self._currentcrs = None
        self.setupUi(self)


        self.itemChecklist = {'Item12': {'ItemEnabled': True}}

        # self.populateDaftarLayer(data_layer)        

        
        self.cariDaftarLayer.valueChanged.connect(self.findLayer)
        #self.pushButtonAdd.clicked.connect(self.addSelectedLayer)
        #self.hapusSeleksi.clicked.connect(self.deleteSelection)
        #self.pushButtonDelete.clicked.connect(self.deleteSelectedLayer)
        self.pushButtonAddtoQGIS.clicked.connect(self.addToQGIS)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def set_crs(self):
        self._currentcrs = self.selectProj.crs()
        # print(self._currentcrs.description())

    
    def populateDaftarLayer(self, data):
        items = []
        for key, values in data.items():
            item = QTreeWidgetItem([key])
            for count, value in enumerate(values):
                nama_layer =  value["Nama Layer"]
                tipe_layer =  value["Tipe Layer"]
                style_path =  value["Style Path"]
                child = QTreeWidgetItem([nama_layer, tipe_layer, style_path])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)
                item.addChild(child)
            items.append(item)
        self.daftarLayer.insertTopLevelItems(0, items)
        #self.daftarLayer.itemChanged.connect(self.treeWidgetItemChanged)

    def findLayer(self):
        textto_find = self.cariDaftarLayer.value()
        items = self.daftarLayer.findItems(textto_find, Qt.MatchContains | Qt.MatchRecursive)
        for item in items:
            #print(item.text(1))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
            item.setSelected(True)
            self.daftarLayer.setCurrentItem(item)
            self.daftarLayer.scrollToItem(item, QtWidgets.QAbstractItemView.PositionAtTop)
            

    def deleteSelection(self):
        root = self.daftarLayer.invisibleRootItem()
        group_count = root.childCount()
        for group in range(group_count):
            groupItem = root.child(group)
            layer_count = groupItem.childCount()
            #print(layer_count)
            for layer in range(layer_count):
                item = groupItem.child(layer)
                if item is not None:
                    #print(item.text(0))
                    item.setSelected(False)                

    def addSelectedLayer(self):
        #self.layerTerpilih.setColumnCount(1)
        root = self.daftarLayer.invisibleRootItem()
        for item in self.daftarLayer.selectedItems():
            #print(item.text(0))
            root.removeChild(item)
            self.layerTerpilih.insertTopLevelItem(0, item)
        
        #items = self.daftarLayer.selectedItems()
        #for i in range(len(items)):
        #    print(items[i].text(0))
        #    self.layerTerpilih.insertTopLevelItem(0, items[i])

    def deleteSelectedLayer(self):
        root = self.layerTerpilih.invisibleRootItem()
        for item in self.layerTerpilih.selectedItems():
            root.removeChild(item)
            self.daftarLayer.insertTopLevelItem(0, item)
        #self.layerTerpilih.clear()

    def addToQGIS(self):
        
        root = self.daftarLayer.invisibleRootItem()
        group_count = root.childCount()
        for group in range(group_count):
            groupItem = root.child(group)
            layer_count = groupItem.childCount()
            for layer in range(layer_count):
                item = groupItem.child(layer)
                if item.checkState(0) != 0:
                    print(item.text(0), item.text(1), item.text(2), item.text(3))
                

   
        



