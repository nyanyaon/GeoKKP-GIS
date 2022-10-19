import os

from qgis.PyQt.QtCore import Qt

from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

try:
    from qgis.gui import QgsMapLayerProxyModel
except ImportError:
    from qgis.core import QgsMapLayerProxyModel

# using utils
from .utils import icon, snap_geometries_to_layer

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/adjust.ui")
)

TARGET_LAYER = "(020100) Batas Persil"


class AdjustDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Parcel Adjust"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):

        super(AdjustDialog, self).__init__(parent)
        self.setupUi(self)
        self.layer_acuan.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.project = QgsProject()
        self._active = False
        self._orig_cursor = None

        self.setWindowIcon(icon("icon.png"))
        self._layer = None
        self._selected_features = None
        self.tolerance.setText("10")
        self.adjustButton.clicked.connect(self.adjust_parcel)

    def showEvent(self, events):
        self._orig_cursor = self.canvas.cursor()
        self.set_identify_layer()
        valid = self.activate_selection()
        if(valid == False):
            print(valid)
            return
        self.canvas.selectionChanged.connect(self.selection_changed)

    def closeEvent(self, events):
        try:
            self.canvas.selectionChanged.disconnect(self.selection_changed)
            self.canvas.setCursor(self._orig_cursor)
        except Exception as e:
            print(str(e))
            return

    def layer_target_not_found(self):
        QtWidgets.QMessageBox.warning(
            None,
            "Layer Batas Persil Tidak ditemukan",
            f"Buat persil di layer {TARGET_LAYER} terlebih dahulu",
        )

    def layer_acuan_not_found(self):
        QtWidgets.QMessageBox.warning(
            None, "Layer Acuan Tidak ditemukan", "Import Layer Acuan terlebih dahulu"
        )

    def selection_changed(self, layer):
        if layer.name() != TARGET_LAYER:
            return

        self._selected_features = layer.selectedFeatures()
        if self._selected_features:
            self.bidang_terpilih.setText(
                f"{len(self._selected_features)} bidang terpilih"
            )
        else:
            self.bidang_terpilih.setText("0 bidang terpilih")

    def set_identify_layer(self):
        for layer in self.project.instance().mapLayers().values():
            if layer.name() == TARGET_LAYER:
                self._layer = layer
                return
        # self.adjustButton.setEnabled(False)
        return 

    def activate_selection(self):
        if not self._layer:
            self.layer_target_not_found()
            return False
        self.canvas.setCursor(QCursor(Qt.PointingHandCursor))
        self.iface.actionSelect().trigger()

    def adjust_parcel(self):
        toleransi = self.tolerance.text()
        selected_layer_index = self.layer_acuan.currentIndex()
        ref_layer = self.layer_acuan.layer(selected_layer_index)
        if not ref_layer and not isinstance(self._layer, QgsVectorLayer):
            self.layer_acuan_not_found()
            return

        out = snap_geometries_to_layer(self._layer, ref_layer, tolerance=toleransi, only_selected=True)

        adjusted_layer = QgsVectorLayer(out, "adjusted", "ogr")
        adjusted_features = adjusted_layer.getFeatures()

        selected_feature_ids = [feature.id() for feature in self._selected_features]
        self._layer.dataProvider().deleteFeatures(selected_feature_ids)
        self._layer.dataProvider().addFeatures(adjusted_features)
        self._layer.triggerRepaint()
