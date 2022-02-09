import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/input_denah.ui")
)


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class InputDenah(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Input Denah"""

    closingPlugin = pyqtSignal()
    done = pyqtSignal()

    def __init__(self, nomor_berkas, tahun_berkas, berkas_id, kantor_id, tipe_berkas, desa_id, new_parcel_number, new_apartment_number, new_parcels, old_parcels, new_apartments, old_apartments, ganti_desa, parent=iface.mainWindow()):
        super(InputDenah, self).__init__(parent)
        self.setupUi(self)

        self._nomor_berkas = nomor_berkas
        self._tahun_berkas = tahun_berkas
        self._berkas_id = berkas_id
        self._kantor_id = kantor_id
        self._tipe_berkas = tipe_berkas
        self._desa_id = desa_id
        self._new_parcel_number = new_parcel_number
        self._new_apartment_number = new_apartment_number
        self._new_parcels = new_parcels
        self._old_parcels = old_parcels
        self._new_apartments = new_apartments
        self._old_apartments = old_apartments
        self._ganti_desa = ganti_desa

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()

    def setup_workpanel(self):
        pass
