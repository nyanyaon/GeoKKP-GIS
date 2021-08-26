import os
import json

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import QTreeWidgetItem
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem


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

data_basemap = readSetting("geokkp/basemaps")


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/basemap.ui'))


class AddBasemapDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Add Basemap from List """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(AddBasemapDialog, self).__init__(parent)
        # self.utils = Utilities
        self.setWindowIcon(icon("icon.png"))
        self.setupUi(self)

        self.populateDaftarBasemap(data_basemap)

        self.buttonTambahLayer.clicked.connect(self.addToQGIS)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def set_crs(self):
        self._currentcrs = self.selectProj.crs()

    def populateDaftarBasemap(self, data):
        if data:
            items = []
            model = QStandardItemModel(self.daftarBasemap)
            #for row in data.items():
            ##    item = QStandardItem(str(row[1]))
            #    model.appendRow(item)
            #self.listUser.setModel(mode    l)
            for key, values in data.items():
                for count, value in enumerate(values):
                    item = QStandardItem(value["nama"])
                    item.setText('Item text')
                    item.setIcon(some_QIcon)
                    model.appendRow(item)
            self.daftarBasemap.setModel(model)


            #print(value["nama"])

            #item = QTreeWidgetItem([key])
            #for count, value in enumerate(values):
            ##    nama_layer =  value["Nama Layer"]
            #    tipe_layer =  value["Tipe Layer"]
            #    style_path =  value["Style Path"]
            #    child = QTreeWidgetItem([nama_layer, tipe_layer, style_path])
            #    child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            #    child.setCheckState(0, Qt.Unchecked)
            #    item.addChild(child)
            #items.append(item)
        #self.daftarLayer.insertTopLevelItems(0, items)
        #self.daftarLayer.itemChanged.connect(self.treeWidgetItemChanged)


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
