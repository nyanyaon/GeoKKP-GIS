import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from ..utils import readSetting
from ..memo import app_state
from ..api import endpoints
from ..models.dataset import Dataset

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../ui/link_pbt/input_berkas.ui")
)


class InputBerkasPBT(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Link Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, dokumen_pengukuran_id, pbt, parent=iface.mainWindow()):
        super(InputBerkasPBT, self).__init__(parent)
        self.setupUi(self)

        self._start = 0
        self._limit = 20
        self._count = -1

        self._txt_nomor = ""
        self._txt_tahun = ""
        self._kantor_id = ""

        self._dokumen_pengukuran_id = dokumen_pengukuran_id
        self._pbt = pbt
        self._current_parcel = ""
        self._current_berkas = ""
        self._current_nomor = ""
        self._current_luas = ""
        self._dset = {}
        self._ds = {}

        self.btn_cari.clicked.connect(self._btn_cari_click)
        self.btn_first.clicked.connect(self._btn_first_click)
        self.btn_last.clicked.connect(self._btn_last_click)
        self.btn_prev.clicked.connect(self._btn_prev_click)
        self.btn_cari.clicked.connect(self._btn_cari_click)
        self.btn_link.clicked.connect(self._btn_link_click)
        self.dgv_new_parcels.itemSelectionChanged.connect(self._dgv_new_parcels_selection_changed)
        self.dgv_inbox.itemSelectionChanged.connect(self._dgv_inbox_selection_changed)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.stackedWidget.setCurrentIndex(0)
        event.accept()

    def setup_workpanel(self):
        kantor = readSetting("kantorterpilih", {})
        if not kantor:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Pilih lokasi kantor lebih dahulu"
            )
            return
        self._kantor_id = kantor["kantorID"]

        response = endpoints.get_unlinked_pbt_berkas(self._dokumen_pengukuran_id)
        self._ds = Dataset(response.content)
        self._ds.render_to_qtable_widget(
            table_name="PERSIL",
            table_widget=self.dgv_new_parcels,
            hidden_index=[0, 4]
        )

    def _btn_cari_click(self):
        self._start = 0
        self._count = -1
        self._txt_nomor = self.txt_nomor.text()
        self._txt_tahun = self.txt_tahun.text()
        self.btn_first.setDisabled(True)
        self.btn_last.setDisabled(True)

        self._refresh_grid()

    def _refresh_grid(self):
        response = endpoints.get_berkas_for_apbn(
            self._txt_nomor,
            self._txt_tahun,
            self._kantor_id,
            self._pbt["programId"],
            self._start,
            self._limit,
            self._count
        )
        self._dset = Dataset(response.content)

        if self._count > 0:
            if self._start + self._limit >= self._count:
                page = f"{self._start + 1} - {self._count} dari {self._count}"
                self.txt_paging.setText(page)
                self.btn_next.setDisabled(True)
            else:
                page = f"{self._start + 1} - {self._start + self._limit} dari {self._count}"
                self.txt_paging.setText(page)
                self.btn_next.setDisabled(True)
        else:
            self.txt_paging.setText("0")
            self.btn_next.setDisabled(True)
            self.btn_prev.setDisabled(True)

        if self._start == 0 or self._count == 0:
            self.btn_prev.setDisabled(True)
        else:
            self.btn_prev.setDisabled(False)

        if self._dset["BERKASAPBN"]:
            self._dset.render_to_qtable_widget(
                table_name="BERKASAPBN",
                table_widget=self.dgv_inbox,
                hidden_index=[0, 7]
            )

    def _btn_first_click(self):
        self._start = 0
        self.btn_prev.setDisabled(True)
        self.btn_next.setDisabled(False)
        self._refresh_grid()

    def _btn_prev_click(self):
        self._start -= self._limit
        if self._start <= 0:
            self.btn_prev.setDisabled(True)
        self.btn_next.setDisabled(False)
        self._refresh_grid()

    def _btn_next_click(self):
        self._start += self._limit
        if self._start + self._limit >= self._count:
            self.btn_next.setDisabled(True)
        self.btn_prev.setDisabled(False)
        self._refresh_grid()

    def _btn_last_click(self):
        self._start = (self._count // self._limit) * self._limit
        if self._start >= self._count:
            self._start -= self._limit
            self.btn_prev.setDisabled(True)
        else:
            self.btn_prev.setDisabled(False)

        self.btn_next.setDisabled(True)
        self.btn_first.setDisabled(False)
        self._refresh_grid()

    def _dgv_new_parcels_selection_changed(self):
        self.dgv_new_parcels.setColumnHidden(0, False)
        self.dgv_new_parcels.setColumnHidden(4, False)
        selected_row = self.dgv_new_parcels.selectedItems()
        self.dgv_new_parcels.setColumnHidden(0, True)
        self.dgv_new_parcels.setColumnHidden(4, True)

        if not selected_row:
            self._current_parcel = ""
            return

        if self._ds["PERSIL"]:
            self._current_parcel = selected_row[0].text()
            self._current_nomor = selected_row[1].text()
            self._current_luas = selected_row[2].text()
            self.lbl_parcel.setText(self._current_nomor)

    def _dgv_inbox_selection_changed(self):
        self.dgv_inbox.setColumnHidden(0, False)
        self.dgv_inbox.setColumnHidden(7, False)
        selected_row = self.dgv_inbox.selectedItems()
        self.dgv_inbox.setColumnHidden(0, True)
        self.dgv_inbox.setColumnHidden(7, True)

        if not selected_row:
            self._current_berkas = ""
            return

        if self._dset["BERKASAPBN"]:
            self._current_berkas = selected_row[0].text()
            label = f"{selected_row[1].text()}/{selected_row[2].text()}"
            self.lbl_berkas.setText(label)

    def _btn_link_click(self):
        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        if not pegawai or "userId" not in pegawai or "pegawaiID" not in pegawai:
            return

        if self.dgv_inbox.selectedItems() and self.dgv_new_parcels.selectedItems():
            response = endpoints.entry_persil_ke_berkas_apbn(
                self._current_parcel,
                self._current_nomor,
                self._current_luas,
                self._current_berkas,
                self._dokumen_pengukuran_id,
                self._kantor_id,
                pegawai["userId"]
            )
            response_text = response.content.decode("utf-8")

            if response_text != "OK":
                QtWidgets.QMessageBox.critical(self, "Error", response_text)
            else:
                for index, row in enumerate(self._ds["PERSIL"].rows):
                    if row["PERSILID"] == self._current_parcel:
                        del self._ds["PERSIL"].rows[index]
                        break
                self._ds["PERSIL"].reload_qtable_widget(self.dgv_new_parcels)

                for index, row in enumerate(self._dset["BERKASAPBN"].rows):
                    if row["BERKASID"] == self._current_berkas:
                        del self._dset["BERKASAPBN"].rows[index]
                        break
                self._dset["BERKASAPBN"].reload_qtable_widget(self.dgv_inbox)

        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Silahkan memilih sebuah persil dan berkas untuk dipasangkan")
