import os
import json
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QTreeWidgetItem
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QVariant
from qgis.utils import iface
from qgis.core import QgsWkbTypes, QgsFields, QgsField

from .utils import logMessage, readSetting, add_layer, icon


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/convert_layer.ui")
)


class ConvertLayerDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Add Layers from List"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(ConvertLayerDialog, self).__init__(parent)
        # self.utils = Utilities
        self.setWindowIcon(icon("icon.png"))
        self._currentcrs = None
        self.setupUi(self)

        data_layer = readSetting("layers")
        try:
            self.populateDaftarLayer(data_layer)
        except Exception:
            logMessage("daftar layer gagal dimuat")

        self.cariDaftarLayer.valueChanged.connect(self.findLayer)
        self.btn_ubah_layer.clicked.connect(self.addToQGIS)

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
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            for count, value in enumerate(values):
                nama_layer = value["Nama Layer"]
                tipe_layer = value["Tipe Layer"]
                style_path = value["Style Path"]
                try:
                    attr_theme = str(value["Attributes"][0])
                except IndexError:
                    attr_theme = None
                # child.setFlags(child.flags() | Qt.ItemIsSelectable)
                child = QTreeWidgetItem(
                    [nama_layer, tipe_layer, style_path, attr_theme]
                )
                item.addChild(child)
            items.append(item)
        self.daftarLayer.insertTopLevelItems(0, items)

    def findLayer(self):
        textto_find = self.cariDaftarLayer.value()
        items = self.daftarLayer.findItems(
            textto_find, Qt.MatchContains | Qt.MatchRecursive
        )
        for item in items:
            item.setSelected(True)
            self.daftarLayer.setCurrentItem(item)
            self.daftarLayer.scrollToItem(
                item, QtWidgets.QAbstractItemView.PositionAtTop
            )

    def deleteSelection(self):
        root = self.daftarLayer.invisibleRootItem()
        group_count = root.childCount()
        for group in range(group_count):
            groupItem = root.child(group)
            layer_count = groupItem.childCount()
            for layer in range(layer_count):
                item = groupItem.child(layer)
                if item is not None:
                    item.setSelected(False)

    def addSelectedLayer(self):
        root = self.daftarLayer.invisibleRootItem()
        for item in self.daftarLayer.selectedItems():
            root.removeChild(item)
            self.layerTerpilih.insertTopLevelItem(0, item)

    def deleteSelectedLayer(self):
        root = self.layerTerpilih.invisibleRootItem()
        for item in self.layerTerpilih.selectedItems():
            root.removeChild(item)
            self.daftarLayer.insertTopLevelItem(0, item)

    def adjust_features_attribute(self, features, fields=None):
        field_list = QgsFields()
        if not fields:
            field_list.append(QgsField("ID", QVariant.String))
            field_list.append(QgsField("Keterangan", QVariant.String))
        else:
            for key, value in fields.items():
                if value == "String":
                    field_type = QVariant.String
                elif value == "Int":
                    field_type = QVariant.Int
                elif value == "Double":
                    field_type = QVariant.Double
                field = QgsField(key, field_type)
                field_list.append(field)

        for feature in features:
            feature.setFields(field_list)
            yield feature

    def addToQGIS(self):
        active_layers = iface.layerTreeView().selectedLayers()
        if not active_layers:
            QtWidgets.QMessageBox.critical(
                None, "Pilih layer sumber", "Pilih layer yang akan di konversi di panel legenda"
            )
            return

        selected = self.daftarLayer.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.critical(
                None, "Pilih layer target", "Pilih layer tujuan pada list di atas"
            )
            return

        target_layer_name = selected[0].text(0)
        target_layer_type = selected[0].text(1)
        target_layer_symbology = selected[0].text(2)
        if selected[0].text(3):
            target_fields = json.loads(selected[0].text(3).replace("'", '"'))
        else:
            target_fields = None

        for source_layer in active_layers:
            source_layer_type = QgsWkbTypes.displayString(source_layer.wkbType())
            if source_layer_type.lower() != target_layer_type.lower():
                msg = f"Tipe geometry layer {source_layer.name()} ({source_layer_type}) tidak sesuai dengan {target_layer_name} ({target_layer_type})!"
                QtWidgets.QMessageBox.critical(
                    None, "Tipe Geometry tidak sesuai", msg
                )
                return

        layer = add_layer(target_layer_name, target_layer_type, target_layer_symbology, target_fields)
        provider = layer.dataProvider()

        for source_layer in active_layers:
            source_feature = source_layer.getSelectedFeatures() if self.chk_selected_only.isChecked() else source_layer.getFeatures()
            adjusted_feature = self.adjust_features_attribute(source_feature, target_fields)
            provider.addFeatures(adjusted_feature)
        layer.commitChanges()
        self.accept()
