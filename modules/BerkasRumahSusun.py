import os
import json
import hashlib
from urllib import response

from qgis.PyQt import QtWidgets, uic

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.core import QgsProject

from .utils import get_nlp, get_nlp_index, readSetting, storeSetting
from .utils.geometry import get_sdo_point, get_sdo_polygon
from .api import endpoints
from .memo import app_state
from .models.dataset import Dataset

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/berkas_rumah_susun.ui")
)

class BerkasRumahSusun(QtWidgets.QDialog, FORM_CLASS):

    startBerkas = pyqtSignal(object)

    def __init__(self,parent=iface.mainWindow()):
        super(BerkasRumahSusun, self).__init__(parent)
        self.setupUi(self)
        self._limit = 20
        self._start = 0
        self._count = -1

        self.btn_cari.clicked.connect(self.btnCari_Click)
        self.btn_next.clicked.connect(self.btnNext_click)
        self.btn_prev.clicked.connect(self.btnPrev_click)
        self.btn_first.clicked.connect(self.btnFirst_click)
        self.btn_last.clicked.connect(self.btnLast_click)
        self.dvg_inbox.doubleClicked.connect(self.dvgInbox_DoubleClick)

    def btnCari_Click(self):
        self._start = 0
        self._count = -1
        self._txtNomor = self.txt_nomor.text()
        self._txtTahun = self.txt_tahun.text()

        self.btn_first.setEnabled(True)
        self.btn_last.setEnabled(True)
        self.refresh_grid()

    def refresh_grid(self):
        kantor = readSetting("kantorterpilih", {})
        self._kantor_id = kantor["kantorID"]
        self._tipe_kantor_id = str(kantor["tipeKantorId"])
        response = endpoints.getBerkasHMSRS(self._txtNomor,self._txtTahun,self._kantor_id,self._start,self._limit,self._count)
        self.dSet = json.loads(response.content)
        print(self.dSet)

        if(self._count == -1 ):
            self._count = int(str(self.dSet["JUMLAHTOTAL"][0]["COUNT(1)"]))
        
        if (self._count > 0 ):
            print(self._start,self._count,self._limit)
            if(self._start + self._limit >= self._count):
                self.txt_paging.setText(str(self._start)+" - " + str(self._count) + " dari " + str(self._count))
                self.btn_next.setEnabled(False)
            else:
                self.txt_paging.setText(str(self._start)+" - " + str(self._count + self._start) + " dari " + str(self._count))
                self.btn_next.setEnabled(True)
        else:
            self.txt_paging.setText("0")
            self.btn_next.setEnabled(False)
            self.btn_prev.setEnabled(False)

        if(self._start == 0 or self._count == 0):
            self.btn_prev.setEnabled(False)
        else:
            self.btn_prev.setEnabled(True)

        if(self.dSet["BERKASSPATIAL"] != None and len(self.dSet["BERKASSPATIAL"]) > 0):
            dataset = Dataset()
            table = dataset.add_table("BERKASSPATIAL")
            table.add_column("BERKASID")
            table.add_column("NOMOR")
            table.add_column("TAHUN")
            table.add_column("OPERASISPASIAL")
            table.add_column("ROWNUMS")

            for p in self.dSet["BERKASSPATIAL"]:
                d_row = table.new_row()
                d_row["BERKASID"] = p["BERKASID"]
                d_row["NOMOR"] = p["NOMOR"]
                d_row["TAHUN"] = p["TAHUN"]
                d_row["OPERASISPASIAL"] = p["OPERASISPASIAL"]
                d_row["ROWNUMS"] = p["ROWNUMS"]

            dataset.render_to_qtable_widget("BERKASSPATIAL", self.dvg_inbox,[0,4])

    def btnFirst_click(self):
        self._start = 0
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)
        self.refresh_grid()

    def btnPrev_click(self):
        self._start = self._start - self._limit 
        if(self._start <= 0):
            self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(True)

        self.refresh_grid()

    def btnNext_click(self):
        self._start = self._limit + self._start
        if(self._start + self._limit >= self._count):
            self.btn_next.setEnabled = False
        self.btn_prev.setEnabled(True)
        self.refresh_grid()

    def btnLast_click(self):
        self._start = self._count // self._limit * self._limit
        if self._start >= self._count:
            self._start -= self._limit
            self.btn_prev.setEnabled(False)
        else:
            self.btn_prev.setEnabled(True)
        self.btn_next.setEnabled(False)
        self.refresh_grid()

    def dvgInbox_DoubleClick(self):
        self.dvg_inbox.setColumnHidden(0, False)
        item = self.dvg_inbox.selectedItems()
        self.dvg_inbox.setColumnHidden(0, True)
        row = item[0].row()
        dataSelect = []
        self.dvg_inbox.setColumnHidden(0, False)
        for x in range(self.dvg_inbox.columnCount()):
            dataSelect.append(self.dvg_inbox.item(row,x).text())
        self.dvg_inbox.setColumnHidden(0, True)
        self._nomorBerkas = dataSelect[1]
        self._tahunBerkas = dataSelect[2]
        self._tipeBerkas = dataSelect[3]
        self._berkasId = dataSelect[0]

        self.StartBerkas()

    def StartBerkas(self):

        try:
            self._layer = QgsProject.instance().mapLayersByName("(020110) Apartemen")[0]
        except:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", "Layer (020110) Apartemen tidak ditemukan"
            )
            return

        username_state = app_state.get("username", "")
        username = username_state.value
        response = endpoints.start_berkas_spasial(self._nomorBerkas,self._tahunBerkas,self._kantor_id,self._tipe_kantor_id,username)
        self._bs = json.loads(response.content)
       
        if(self._bs["errorStack"] == []):
            self._bs["nomorBerkas"] = self._nomorBerkas
            self._bs["tahunBerkas"] = self._tahunBerkas
            self._bs["berkasId"] = self._berkasId
            self.startBerkas.emit(self._bs)
            self.close()
        else:
            QtWidgets.QMessageBox.warning(
                None, "GeoKKP", self._bs["errorStack"][0]
            )
            return

 
