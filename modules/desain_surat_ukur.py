import os

from qgis.PyQt import QtWidgets, uic

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/desain_surat_ukur.ui")
)

from .import_surat_ukur import ImportSuratUkur

STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class DesainSuratUkur(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Desain PBT"""

    closingPlugin = pyqtSignal()
    processed = pyqtSignal(object)

    def __init__(
        self,
        parent=iface.mainWindow(),
        tipe=None,
        nomor=None,
        tahun=None,
        old_parcel=[],
        old_apartment=[],
        desa_id=None,
        per_desa=None,
        old_gugus_id=[],
    ):
        super(DesainSuratUkur, self).__init__(parent)

        self._parent = parent
        self._old_parcel = old_parcel
        self._old_apartment = old_apartment
        self._desa_id = desa_id
        self._per_desa = per_desa
        self._old_gugus_id = old_gugus_id
        self._tipe = tipe
        self._nomor = nomor
        self._tahun = tahun

        self.setupUi(self)
        self.setup_workpanel()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setup_workpanel(self):
        layout = QtWidgets.QVBoxLayout(self.tab_desain)
        isu = ImportSuratUkur(
            self._parent,
            self._old_parcel,
            self._old_apartment,
            self._desa_id,
            self._per_desa,
            self._old_gugus_id,     
            )
        isu.writeErrorLog.connect(self._handle_write_error)
        isu.writeRightStatus.connect(self._handle_write_right_status)
        isu.writeLeftStatus.connect(self._handle_write_left_status)
        isu.changeTabIndex.connect(self._handle_change_tab_index)
        isu.processed.connect(self._handle_processed)

        layout.addWidget(isu)
        self.tab_desain.layout().addLayout(layout)

    def _handle_write_error(self, error):
        self.error_log.setText(error)

    def _handle_write_right_status(self, status):
        self.label_status_r.setText(status)

    def _handle_write_left_status(self, status):
        self.label_status_l.setText(status)

    def _handle_change_tab_index(self, index):
        self.tabWidget.setCurrentIndex(index)

    def _handle_processed(self, payload):
        print("desain processed", payload)
        self.processed.emit(payload)
