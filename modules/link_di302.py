import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

from .api import endpoints
from .models.dataset import Dataset

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/link_di302.ui")
)


class LinkDI302(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Link DI302"""

    closingPlugin = pyqtSignal()

    def __init__(self, berkas_id, kode_spopp, parent=iface.mainWindow()):
        super(LinkDI302, self).__init__(parent)
        self.setupUi(self)

        self._berkas_id = berkas_id
        self._kode_spopp = kode_spopp

        self.setup_workpanel()
        self.btn_link.clicked.connect(self._handle_link)
        self.btn_unlink.clicked.connect(self._handle_unlink)
        self.btn_autolink.clicked.connect(self._handle_autolink)
        self.btn_reset_link.clicked.connect(self._handle_reset_link)
        self.setup_workpanel()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setup_workpanel(self):
        self._load_resource()

    def _load_resource(self):
        pengukuran_ulang = False
        if self._kode_spopp in ["SPOPP-3.09.2", "SPOPP-3.18.1", "SPOPP-3.46.3"]:
            pengukuran_ulang = True

        persil_response = endpoints.get_parcel_not_linked_to_302(self._berkas_id, pengukuran_ulang)
        print(json.loads(persil_response.content))
        persil_dataset = Dataset(persil_response.content)
        persil_dataset.render_to_qtable_widget(
            table_name="PERSIL",
            table_widget=self.table_persil,
            hidden_index=[0]
        )

        di302_response = endpoints.get_302_not_linked_to_parcel(self._berkas_id)
        di302_dataset = Dataset(di302_response.content)
        di302_dataset.render_to_qtable_widget(
            table_name="DI302",
            table_widget=self.table_di302,
            hidden_index=[0]
        )

        parcel_linked_response = endpoints.get_parcel_linked_to_302(self._berkas_id)
        parcel_linked_dataset = Dataset(parcel_linked_response.content)
        parcel_linked_dataset.render_to_qtable_widget(
            table_name="PERSIL",
            table_widget=self.table_persil_di302,
            # hidden_index=[0, 1]
        )

    def _handle_link(self):
        self.table_persil.setColumnHidden(0, False)
        selected_persil = self.table_persil.selectedItems()
        self.table_persil.setColumnHidden(0, True)

        self.table_di302.setColumnHidden(0, False)
        selected_di302 = self.table_di302.selectedItems()
        self.table_di302.setColumnHidden(0, True)

        if selected_persil and selected_di302:
            id_persil = selected_persil[0].text()
            nomor_persil = selected_persil[1].text()
            luas_persil = selected_persil[2].text()
            id302 = selected_di302[0].text()

            response = endpoints.update_di302(id302, id_persil, nomor_persil, luas_persil)
            response_str = response.content.decode("utf-8")
            if response_str != "OK":
                QtWidgets.QMessageBox.critical(self, "GeoKKP Web", response_str)
            else:
                self._load_resource()
        else:
            QtWidgets.QMessageBox.warning(
                self, "GeoKKP Web", "Pilih Sebuah Baris Pada Grid 'Persil Belum Terkait Dengan DI302' dan 'DI302 Belum Terkait Dengan Persil'")

    def _handle_unlink(self):
        self.table_persil_di302.setColumnHidden(0, False)
        self.table_persil_di302.setColumnHidden(1, False)
        selected_link = self.table_persil_di302.selectedItems()
        self.table_persil_di302.setColumnHidden(0, True)
        self.table_persil_di302.setColumnHidden(1, True)

        if selected_link:
            id302 = selected_link[1].text()
            response = endpoints.remove_parcel_from_di302(id302)
            response_str = response.content.decode("utf-8")
            print(response_str)
            if response_str != "OK":
                QtWidgets.QMessageBox.critical(self, "GeoKKP Web", response_str)
            else:
                self._load_resource()

    def _handle_autolink(self):
        response = endpoints.autolink_parcel_to_302(self._berkas_id)
        response_str = response.content.decode("utf-8")
        if response_str != "OK":
            QtWidgets.QMessageBox.critical(self, "GeoKKP Web", response_str)
        else:
            self._load_resource()

    def _handle_reset_link(self):
        response = endpoints.unlink_all_parcels_to_di302(self._berkas_id)
        response_str = response.content.decode("utf-8")
        if response_str != "OK":
            QtWidgets.QMessageBox.critical(self, "GeoKKP Web", response_str)
        else:
            self._load_resource()
