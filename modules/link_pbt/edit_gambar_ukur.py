from datetime import datetime
import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QDate, Qt
from qgis.utils import iface

from ..api import endpoints
from ..memo import app_state
from ..utils import readSetting, storeSetting
from ..models.dataset import Dataset

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../ui/link_pbt/edit_gambar_ukur.ui")
)

# NOTE: sometime got KKPWebServiceNetCore.Services.SpatialRepo.SpatialRepository.WithConnection() experienced a SQL exception (not a timeout)


class EditGambarUkur(QtWidgets.QWidget, FORM_CLASS):
    """Dialog for Link Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, dokumen_pengukuran_id, pbt, parent=iface.mainWindow()):
        super(EditGambarUkur, self).__init__(parent)
        self.setupUi(self)

        self._start = 0
        self._limit = 20
        self._count = -1

        self._nomor_berkas = ""
        self._tahun_berkas = ""

        self._ds_petugas_ukur = {}
        self._d_set = {}

        self._kantor_id = ""
        self._dokumen_pengukuran_id = dokumen_pengukuran_id
        self._gambar_ukur_id = ""
        self._current_berkas = ""
        self._pbt = pbt

        self._gset_petugas_ukur = {}
        self._gset_tetangga = {}

        self.btn_cari.clicked.connect(self._btn_cari_click)
        self.dgv_berkas.itemSelectionChanged.connect(self._dgv_berkas_selection_changed)
        self.btn_first.clicked.connect(self._btn_first_click)
        self.btn_last.clicked.connect(self._btn_last_click)
        self.btn_prev.clicked.connect(self._btn_prev_click)
        self.btn_next.clicked.connect(self._btn_next_click)
        self.dgv_petugas_ukur.itemSelectionChanged.connect(self._dgv_petugas_ukur_selection_changed)
        self.dgv_tetangga.itemSelectionChanged.connect(self._dgv_tetangga_selection_changed)
        self.btn_add_petugas_ukur.clicked.connect(self._btn_add_petugas_ukur_click)
        self.btn_add_tetangga.clicked.connect(self._btn_add_tetangga_click)
        self.btn_update_petugas_ukur.clicked.connect(self._btn_update_petugas_ukur_click)
        self.btn_update_tetangga.clicked.connect(self._btn_update_tetangga_click)

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

        self._nomor_berkas = ""
        self._tahun_berkas = ""

        self.btn_first.setDisabled(True)
        self.btn_last.setDisabled(True)

        petugas_ukur = readSetting("petugasukur", {})
        if not petugas_ukur:
            response = endpoints.get_petugas_ukur(self._kantor_id)
            petugas_ukur = json.loads(response.content)
            storeSetting("petugas_ukur", petugas_ukur)
        self._ds_petugas_ukur = petugas_ukur

        for item in self._ds_petugas_ukur["PETUGASUKUR"]:
            self.cmb_petugas_ukur.addItem(item["NAMA"], item["PEGAWAIID"])

        self.cmb_mata_angin.addItem("Utara")
        self.cmb_mata_angin.addItem("Timur")
        self.cmb_mata_angin.addItem("Selatan")
        self.cmb_mata_angin.addItem("Barat")

        self.cmb_mata_angin.setCurrentIndex(0)

        if self.dgv_berkas.rowCount() == 0:
            self.btn_add_petugas_ukur.setDisabled(True)
            self.btn_add_tetangga.setDisabled(True)
            self.btn_update_petugas_ukur.setDisabled(True)
            self.btn_update_tetangga.setDisabled(True)

    def _refresh_grid_berkas(self):
        response = endpoints.get_berkas_apbn_by_pbt_id(
            self._nomor_berkas,
            self._tahun_berkas,
            self._dokumen_pengukuran_id,
            self._start,
            self._limit,
            self._count
        )

        self._d_set = Dataset(response.content)
        print(self._d_set["JUMLAHTOTAL"].rows)

        if self._count == -1:
            self._count = int(self._d_set["JUMLAHTOTAL"].rows[0]["COUNT(*)"])

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

        if "BERKASAPBN" in self._d_set and self._d_set["BERKASAPBN"]:
            self._d_set.render_to_qtable_widget(
                table_name="BERKASAPBN",
                table_widget=self.dgv_berkas,
                hidden_index=[3, 0]
            )

    def _dgv_berkas_selection_changed(self):
        selected_row = self._d_set["BERKASAPBN"].get_selected_qtable_widget()
        if not selected_row:
            return

        if self._d_set["BERKASAPBN"]:
            self._current_berkas = selected_row[0].text()

            response = endpoints.get_gambar_ukur_apbn_by_berkas(self._current_berkas)
            g_set = Dataset(response.content)

            if g_set["PETUGASUKUR"].rows:
                self.btn_update_petugas_ukur.setDisabled(False)
            else:
                self.btn_update_petugas_ukur.setDisabled(True)

            if g_set["TETANGGA"].rows:
                self.btn_update_tetangga.setDisabled(True)
            else:
                self.btn_update_tetangga.setDisabled(False)

            if g_set["GAMBARUKUR"].rows:
                self._gambar_ukur_id = g_set["GAMBARUKUR"].rows[0]["DOKUMENPENGUKURANID"]
                g_set.render_to_qtable_widget(
                    table_name="PETUGASUKUR",
                    table_widget=self.dgv_petugas_ukur,
                    hidden_index=[0]
                )

                if "TETANGGA" in g_set and g_set["TETANGGA"].rows:
                    g_set.render_to_qtable_widget(
                        table_name="TETANGGA",
                        table_widget=self.dgv_tetangga,
                        hidden_index=[0]
                    )

                nomor_gu = f"{g_set['GAMBARUKUR'].rows[0]['NOMOR']}/{g_set['GAMBARUKUR'].rows[0]['TAHUN']}"
                self.lbl_nomor_gu.setText(nomor_gu)

                self.btn_add_petugas_ukur.setDisabled(False)
                self.btn_add_tetangga.setDisabled(False)
            else:
                self._gambar_ukur_id = ""

                self.btn_add_petugas_ukur.setDisabled(True)
                self.btn_add_tetangga.setDisabled(True)
                self.btn_update_petugas_ukur.setDisabled(True)
                self.btn_update_tetangga.setDisabled(True)

                self.dgv_petugas_ukur.setRowCount(0)
                self.dgv_tetangga.setRowCount(0)
                self.lbl_nomor_gu.setText("Berkas Belum memiliki Gambar Ukur")

    def _btn_first_click(self):
        self._start = 0
        self.btn_prev.setDisabled(True)
        self.btn_next.setDisabled(False)
        self._refresh_grid_berkas()

    def _btn_prev_click(self):
        self._start -= self._limit
        if self._start <= 0:
            self.btn_prev.setDisabled(True)
        self.btn_next.setDisabled(False)
        self._refresh_grid_berkas()

    def _btn_next_click(self):
        self._start += self._limit
        if self._start + self._limit >= self._count:
            self.btn_next.etDisabled(True)
        self.btn_prev.setDisabled(False)
        self._refresh_grid_berkas()

    def _btn_last_click(self):
        self._start = (self._count // self._limit) * self._limit
        if self._start >= self._count:
            self._start -= self._limit
            self.btn_prev.setDisabled(True)
        else:
            self.btn_Prev.setDisabled(False)

        self.btn_next.setDisabled(True)
        self.btn_first.setDisabled(False)
        self._refresh_grid_berkas()

    def _btn_add_petugas_ukur_click(self):
        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        if not pegawai or "userId" not in pegawai or "userId" not in pegawai:
            return

        mulai_pengukuran = self.dtp_mulai.date().toString("dd/MM/yyyy")
        selesai_pengukuran = self.dtp_selesai.date().toString("dd/MM/yyyy")

        response = endpoints.add_petugas_ukur_gu(
            self._gambar_ukur_id,
            self.cmb_petugas_ukur.currentData(),
            mulai_pengukuran,
            selesai_pengukuran,
            pegawai["userId"]
        )
        print(response.content)
        self._gset_petugas_ukur = Dataset(response.content)
        self._gset_petugas_ukur.render_to_qtable_widget(
            table_name="PETUGASUKUR",
            table_widget=self.dgv_petugas_ukur
        )

    def _btn_add_tetangga_click(self):
        pegawai_state = app_state.get("pegawai", {})
        pegawai = pegawai_state.value
        if not pegawai or "userId" not in pegawai or "userId" not in pegawai:
            return

        response = endpoints.add_tetangga_gu(
            self._gambar_ukur_id,
            self.cmb_mata_angin.currentText(),
            self.txt_tetangga.text(),
            pegawai["userId"]
        )
        self._gset_tetangga = Dataset(response.content)
        self._gset_tetangga.render_to_qtable_widget(
            table_name="TETANGGA",
            table_widget=self.dgv_tetangga
        )

    def _dgv_petugas_ukur_selection_changed(self):
        self.dgv_petugas_ukur.setColumnHidden(0, False)
        selected_row = self.dgv_petugas_ukur.selectedItems()
        self.dgv_petugas_ukur.setColumnHidden(0, True)

        if not selected_row:
            self.btn_update_petugas_ukur.setDisabled(True)
            self.dtp_mulai.clear()
            self.dtp_selesai.clear()
            return
        else:
            self.btn_update_petugas_ukur.setDisabled(False)
            now = datetime.now().strftime("%d/%m/%Y")
            mulai_pengukuran = (now)
            selesai_pengukuran = (now)

            if not selected_row[2].text():
                self.dtp_mulai.clear()
            else:
                mulai_pengukuran = selected_row[2].text()
                q_mulai_pengukuran = QDate().fromString(mulai_pengukuran, "dd/mm/YYYY")
                self.dtp_mulai.setDate(q_mulai_pengukuran)

            if not selected_row[3].text():
                self.dtp_selesai.clear()
            else:
                selesai_pengukuran = selected_row[3].text()
                q_selesai_pengukuran = QDate().fromString(selesai_pengukuran, "dd/mm/YYYY")
                self.dtp_mulai.setDate(q_selesai_pengukuran)

    def _dgv_tetangga_selection_changed(self):
        self.dgv_tetangga.setColumnHidden(0, False)
        selected_row = self.dgv_tetangga.selectedItems()
        self.dgv_tetangga.setColumnHidden(0, True)

        if selected_row:
            self.btn_update_tetangga.setDisabled(False)
            self.txt_tetangga.setText(selected_row[2].text())
            self.cmb_mata_angin.setCurrentText(selected_row[1].text())
        else:
            self.btn_update_tetangga.setDisabled(True)
            self.txt_tetangga.setText("")
            self.cmb_mata_angin.setCurrentText("Utara")

    def keyPressEvent(self, event):
        if self.dgv_petugas_ukur.hasFocus() and event.key() == Qt.Key_Delete:
            selected_row = self._gset_petugas_ukur["PETUGASUKUR"].get_selected_qtable_widget()
            if not selected_row:
                event.accept()
                return

            result = QtWidgets.QMessageBox.question(self, "GeoKKPWeb", "Anda akan menghapus petugas ukur?")
            if result == QtWidgets.QMessageBox.Yes:
                response = endpoints.delete_gu_petugas_ukur(selected_row[0].text(), self._gambar_ukur_id)
                self._gset_petugas_ukur = Dataset(response.content)
                self._gset_petugas_ukur.render_to_qtable_widget(
                    table_name="PETUGASUKUR",
                    table_widget=self.dgv_petugas_ukur
                )

        elif self.dgv_tetangga.hasFocus() and event.key() == Qt.Key_Delete:
            selected_row = self._gset_tetangga["TETANGGA"].get_selected_qtable_widget()
            if not selected_row:
                event.accept()
                return

            result = QtWidgets.QMessageBox.question(self, "GeoKKPWeb", "Anda akan menghapus nama tetangga?")
            if result == QtWidgets.QMessageBox.Yes:
                response = endpoints.delete_tetangga(selected_row[0].text(), self._gambar_ukur_id)
                self._gset_tetangga = Dataset(response.content)
                self._gset_tetangga.render_to_qtable_widget(
                    table_name="TETANGGA",
                    table_widget=self.dgv_tetangga
                )

        event.accept()

    def _btn_update_petugas_ukur_click(self):
        selected_row = self._gset_petugas_ukur["PETUGASUKUR"].get_selected_qtable_widget()
        if not selected_row:
            QtWidgets.QMessageBox.warning(self, "GeoKKPWeb", "Pilih seorang petugas ukur dari grid")
            return

        mulai_pengukuran = self.dtp_mulai.date().toString("dd/MM/yyyy")
        selesai_pengukuran = self.dtp_selesai.date().toString("dd/MM/yyyy")

        response = endpoints.update_petugas_ukur_gu(
            selected_row[0].text(),
            self._gambar_ukur_id,
            self.cmb_petugas_ukur.currentData(),
            mulai_pengukuran,
            selesai_pengukuran
        )
        self._gset_petugas_ukur = Dataset(response.content)
        self._gset_petugas_ukur.render_to_qtable_widget(
            table_name="PETUGASUKUR",
            table_widget=self.dgv_petugas_ukur
        )

    def _btn_update_tetangga_click(self):
        selected_row = self._gset_tetangga["TETANGGA"].get_selected_qtable_widget()
        if not selected_row:
            return

        response = endpoints.update_tetangga(
            selected_row[0].text(),
            self.cmb_mata_angin.currentText(),
            self.txt_tetangga.text(),
            self._gambar_ukur_id
        )

        self._gset_tetangga = Dataset(response.content)
        self._gset_tetangga.render_to_qtable_widget(
            table_name="TETANGGA",
            table_widget=self.dgv_tetangga
        )

    def _btn_cari_click(self):
        self._start = 0
        self._limit = 20
        self._count = -1

        self._nomor_berkas = self.txt_nomor.text()
        self._tahun_berkas = self.txt_tahun.text()

        self._refresh_grid_berkas()
