import os

from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.utils import iface
from qgis.core import Qgis, QgsProject, QgsRasterLayer
from qgis.utils import iface
from owslib.wms import WebMapService

# using utils
from .utils import logMessage, readSetting, loadXYZ, dialogBox, icon


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/layer_tambahan.ui")
)


class AddOtherWMSDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Add Layer Tambahan"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(AddOtherWMSDialog, self).__init__(parent)
        # self.utils = Utilities
        self.setWindowIcon(icon("icon.png"))
        self.setupUi(self)

        self.url = self.capabilitiesLink.text()
        self.populateDaftarWMS()
        self.muatUlang.clicked.connect(self.populateDaftarWMS)
        self.ubahLink.clicked.connect(self.enableCapabilities)
        self.buttonTambahLayer.clicked.connect(self.addToQGIS)
        

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def set_crs(self):
        self._currentcrs = self.selectProj.crs()

    def enableCapabilities(self):
        self.capabilitiesLink.setEnabled(True)

    def populateDaftarWMS(self):
        self.model = QStandardItemModel(self.daftarLayerWMS)
        try:
            wms = WebMapService(self.capabilitiesLink.text(), version='1.3.0')
        except:
            iface.messageBar().pushMessage(
                "Peringatan",
                f"Akses tanpa koneksi VPN. Menu Tambah Layer WMS dinon-aktifkan",
                level=Qgis.Warning,
            )
        else:
            daftarWMS = {name: metadata.title for (name, metadata) in wms.contents.items()}
            for key, value in daftarWMS.items():
                item = QStandardItem(value)
                item.setData(value, 64)
                item.setData(key, 128)
                self.model.sort(Qt.Unchecked, Qt.DescendingOrder)
                self.model.appendRow(item)
            self.daftarLayerWMS.setModel(self.model)

    def addToQGIS(self):
        for index in self.daftarLayerWMS.selectedIndexes():
            layertitle = index.data(64)
            layername = index.data(128)
            urlWithParams = f'url={self.capabilitiesLink.text()}&crs=EPSG:4326&format=image/png&layers={layername}&styles='
            rlayer = QgsRasterLayer(urlWithParams, layertitle, 'wms')
            QgsProject.instance().addMapLayer(rlayer)
            # loadXYZ(urlWithParams, layertitle)

