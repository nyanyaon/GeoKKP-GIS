import os
from osgeo import ogr


from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtWidgets import QLineEdit
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

# using utils
from .utils import icon, readSetting, dialogBox, get_tm3_zone

adm_district_file = os.path.join(
    os.path.dirname(__file__), '../data/idn_adm_lv2.json')

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/pengaturan_lokasi.ui'))


class PengaturanLokasiDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Kotak Dialog Pengaturan dan Pencarian Lokasi  """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(PengaturanLokasiDialog, self).__init__(parent)
        self.setWindowIcon(icon("icon.png"))
        self.setupUi(self)

        # setup crs
        self._currentcrs = None

        self.list_kantor_dict = readSetting("list_kantor_id")

        if self.list_kantor_dict is not None:
            # print(type(self.list_kantor_dict), "=========================")
            self.setPropinsi()
        else:
            dialogBox("Data kantor tidak dapat dibaca dari server", type="Warning")

        # buttons and forms
        self.cari_propinsi.currentIndexChanged.connect(self.setKabupaten)
        self.cari_kabupaten.currentIndexChanged.connect(self.setEPSG)
        self.terapkan_btsadmin.clicked.connect(self.plot_lokasi)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def set_crs(self):
        self._currentcrs = self.selectProj.crs()
        # print(self._currentcrs.description())

    def setPropinsi(self):
        """ Isi kolom propinsi """
        self.cari_propinsi.clear()
        propinsi = []
        for key, value in self.list_kantor_dict.items():
            if key not in propinsi:
                propinsi.append(key)
        # print(propinsi)
        self.cari_propinsi.addItems(propinsi)
        edit = QLineEdit(self)
        self.cari_propinsi.setLineEdit(edit)
        self.cari_propinsi.setCurrentText('')
        # completer = QCompleter(propinsi)
        # self.cari_propinsi.setCompleter(completer)

    def setKabupaten(self):
        """ Isi kolom kabupaten """
        self.cari_kabupaten.clear()
        kabupaten = []
        currentProvince = self.cari_propinsi.currentText()
        for key, value in self.list_kantor_dict.items():
            if key == currentProvince:
                for item in value:
                    # print(item["WAK"])
                    kabupaten.append(item["WAK"])
            else:
                pass
        # print(kabupaten)
        self.cari_kabupaten.addItems(kabupaten)
        edit = QLineEdit(self)
        self.cari_kabupaten.setLineEdit(edit)
        self.cari_kabupaten.setCurrentText('')
        # completer = QCompleter(kabupaten)
        # self.cari_kabupaten.setCompleter(completer)

    def setEPSG(self):
        currentKabupaten = self.cari_kabupaten.currentText()
        # print(currentKabupaten)
        driver = ogr.GetDriverByName("TopoJSON")
        dataSource = driver.Open(adm_district_file, 0)
        layer = dataSource.GetLayer()

        layer.SetAttributeFilter(f"WAK = '{currentKabupaten}'")

        for feature in layer:
            # print(feature.GetField("WAK"))
            geom = feature.GetGeometryRef()
            # print(geom.Centroid().GetX())
            long = geom.Centroid().GetX()
            zone = get_tm3_zone(long)
            self.btsadmin_tm3.setText(zone)
        layer.ResetReading()

    def plot_lokasi(self):
        """ Eksekusi pencarian lokasi """
        adm_district_file
        self.iface.mainWindow().blockSignals(True)
        


        
