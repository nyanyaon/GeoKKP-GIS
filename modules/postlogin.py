
import os

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.core import (
    QgsProject,
    QgsSettings
)

from .utils import storeSetting

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/postlogin2.ui'))


class PostLoginDock(QtWidgets.QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        """Constructor."""
        super(PostLoginDock, self).__init__(parent)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.setupUi(self)
        self.project = QgsProject
        self.settings = QgsSettings()

        # read settings: Jumlah Kantah Terdaftar
        jumlahKantor = self.settings.value("geokkp/jumlahkantor")
        print(jumlahKantor)
        self.populateKantah(jumlahKantor)

    def populateKantah(self, jumlahKantor):
        jsonKantor = self.settings.value("geokkp/listkantor")
        self.indexkantor = 0
        if int(jumlahKantor) > 1:
            kantah = {}
            for item in jsonKantor:
                nama = item.pop('nama')
                kantah[nama] = item
            self._kantahs = kantah

            print(jsonKantor)
            self.labelSatuKantah_3.hide()
            for n in range(len(jumlahKantor)):
                self.comboBoxKantah_3.addItems(self._kantahs.keys())
        else:
            self.labelBeberapaKantah_4.hide()
            self.comboBoxKantah_3.addItems(jsonKantor[0])

        self.buttonLanjut_3.clicked.connect(self.simpan)

    def simpan(self):
        idkantorTerpilih = self.comboBoxKantah_3.currentText()
        print("menyimpan kantor "+idkantorTerpilih)
        storeSetting("geokkp/kantorterpilih", idkantorTerpilih)
        self.accept()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
