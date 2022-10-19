import os
import json
from pathlib import Path
from ..utils import (
    dialogBox,
    readSetting,
    storeSetting,
    get_epsg_from_tm3_zone,
    logMessage,
    set_project_crs_by_epsg,
)

from qgis.core import QgsCoordinateReferenceSystem  
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../ui/pengaturan.ui")
)

# ==== Defaults ====
folder_data = os.path.join(os.path.dirname(__file__), "../../data/")
folder_config = os.path.join(os.path.dirname(__file__), "../../config/")
folder_template = os.path.join(os.path.dirname(__file__), "../../template/")

from ..api import endpoints
from ..memo import app_state
class SettingsDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for GeoKKP Settings"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)
 
        self.populateEndpoint()
        self.populateTemplate()
        self.populateKonfigurasi()
        self.populateData()
        
        self.pengaturanBasemap()
        self.pengaturanLayer()
        
        self.combo_kantor.currentIndexChanged.connect(self.kantor_changed)
        self.simpanAturServer.clicked.connect(self.aturServer)
        self.editBerkasBasemap.clicked.connect(self.editBerkas)
        self.editBerkasLayer.clicked.connect(self.editLayer)
        self.editBerkasKantor.clicked.connect(self.editKantor)
        self.simpanPengaturan.clicked.connect(self.simpan_pengaturan)

    

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def showEvent(self, events):
        username = app_state.get("username").value
        script_dir = Path(os.path.dirname(__file__)).parents[2]
        file_path = os.path.join(script_dir, 'file.json')

        if(os.path.exists(file_path)):
            with open(file_path, "r") as outfile:
                data = json.load(outfile)

            result = [a for a in data["data_user"] if a["username"] == username]
            if(len(result)==0):
                self.populateKantor()
                self.populateTM3()
            else:
                self.populateKantor(result[0]["kantor"]["nama"])
                self.populateTM3(result[0]["tm3"])
        else:
            self.populateKantor()
            self.populateTM3()
    
    def populateTM3(self,tm3=False):
        index = 0
        self.combo_tm3.clear()
        for i,data in enumerate(range(23830, 23846)):
            tm3code = QgsCoordinateReferenceSystem(data).description().split(" zone ")[1]
            self.combo_tm3.addItem(tm3code)
            if(tm3code and tm3code == tm3):
                index = i
        self.combo_tm3.setCurrentIndex(index)

    def populateKantor(self,kantor=False):
        """
        user entity
        API backend: {}/getEntityByUserName
        """
        
        username = app_state.get("username").value
        if(username is None):
            return
        try:
            response = endpoints.get_entity_by_username(username)
            if response is not None:
                response_json = json.loads(response.content)
                self.list_kantor = response_json
            else:
                dialogBox(
                    "Data Pengguna gagal disimpan ke dalam QGIS",
                    "Koneksi Bermasalah",
                    "Warning",
                )
        except Exception as e:
            print(e)
            dialogBox(
                "Data Pengguna gagal dimuat dari server",
                "Koneksi Bermasalah",
                "Warning",
            )
            return

        self.combo_kantor.clear()
        index = 0
        try:
            for i,data in enumerate(self.list_kantor):
                self.combo_kantor.addItem(data["nama"])
                if(kantor and kantor == data["nama"]):
                    index = i
        except Exception:
            logMessage("Jumlah kantor tidak terbaca")
        self.combo_kantor.setCurrentIndex(index)
        if self.combo_kantor.count() > 0:
            return 
        
    def kantor_changed(self, index):
        self.current_kantor = self.list_kantor[index]
        self.current_kantor_id = self.current_kantor["kantorID"]
        self.current_tipe_kantor_id = self.current_kantor["tipeKantorId"]

    def simpan_pengaturan(self):
        try:
            username = app_state.get("username").value
            self.get_pagawai()
            self.simpan_tm3(self.combo_tm3.currentText())
            self.save_user(username,self.current_kantor,self.combo_tm3.currentText())
            self.close()
        except Exception as e:
            print(e)
            dialogBox("Gagal mengatur CRS Project dan kantor")
        

    def save_user(self,username,kantor,tm3):
        # dataBaru = {
        #     "username": username,
        #     "kantor":kantor,
        #     "tm3":tm3
        # }
        # daftarUser = readSetting("daftarUser")

        # if(daftarUser is None):
        #     daftarUser = []
        #     daftarUser.append(data)
        # else:
        #     isSame = False
        #     NomorIndex = 0 
        #     for index,data in enumerate(daftarUser):
        #         if(data["username"] == username):
        #             isSame = True
        #             NomorIndex = index
        #             break
        #     if(isSame):
        #         daftarUser[NomorIndex] = dataBaru
        #     else:
        #         daftarUser.append(dataBaru)
        # storeSetting("daftarUser", daftarUser)
        dictionary = {
            "username": username,
            "kantor":kantor,
            "tm3":tm3
        }

        script_dir = Path(os.path.dirname(__file__)).parents[2]
        file_path = os.path.join(script_dir, 'file.json')
        try:
            if(os.path.exists(file_path)):
                with open(file_path, "r") as outfile:
                    print(outfile)
                    data = json.load(outfile)
                    print(data)
                isSame = False
                for index,data in enumerate(data["data_user"]):
                    if(data["username"] == username):
                        isSame = True
                        NomorIndex = index
                        break
                if(isSame):
                    data["data_user"][NomorIndex] = dictionary
                else:
                    data["data_user"].append(dictionary)

                with open(file_path, "w") as outfile:
                    json_object = json.dumps(data)
                    outfile.write(json_object)
            else:
                with open(file_path, "w") as outfile:
                    json_object = json.dumps({"data_user":[dictionary]})
                    outfile.write(json_object)
        except Exception as e:
            with open(file_path, "w") as outfile:
                json_object = json.dumps({"data_user":[dictionary]})
                outfile.write(json_object)
            
        # if(daftarUser is None):
        #     daftarUser = []
        #     daftarUser.append(data)
        # else:
        #     isSame = False
        #     NomorIndex = 0 
        #     for index,data in enumerate(daftarUser):
        #         if(data["username"] == username):
        #             isSame = True
        #             NomorIndex = index
        #             break
        #     if(isSame):
        #         daftarUser[NomorIndex] = dataBaru
        #     else:
        #         daftarUser.append(dataBaru)
        
        # Serializing json
        # json_object = json.dumps(dictionary, indent=4)
        
        # # Writing to sample.json
        # with open(file_path, "w") as outfile:
        #     outfile.write(json_object)

    def simpan_tm3(self,tm3):
        selectedTM3 = get_epsg_from_tm3_zone(tm3)
        try:
            print(selectedTM3)
            set_project_crs_by_epsg(selectedTM3)
        except Exception as e:
            logMessage("pengaturan CRS Project Gagal", str(e))
            pass
        dialogBox("Berhasil mengatur CRS Project")

    def populateEndpoint(self):
        endpoints = ["https://geokkptraining.atrbpn.go.id/spatialapi",
                     "http://10.20.22.90:5001/spatialapi",
                    ]
        for i in endpoints:
            self.comboBoxEndpoint.addItem(i)

    def get_pagawai(self,kantor=False):
        if(kantor):
            self.current_kantor = kantor

        kantor_id = self.current_kantor["kantorID"]
        storeSetting("kantorterpilih", self.current_kantor)
        username = app_state.get("username", None)
        if not (username and kantor_id):
            return
        response = endpoints.get_user_entity_by_username(username.value, kantor_id)
        response_json = json.loads(response.content)
        # print("get_user_entity_by_username", response_json)
        app_state.set("pegawai", response_json)

        # add notif for succesful setting loaction
        if response_json["pegawaiID"]:
            QtWidgets.QMessageBox.information(
            None, "GeoKKP - Informasi", "Berhasil mengatur lokasi")

    def populateTemplate(self):
        self.direktoriTemplate.setFilePath(folder_template)


    def populateKonfigurasi(self):
        self.direktoriKonfigurasi.setFilePath(folder_config)


    def populateData(self):
        self.direktoriBatasWilayah.setFilePath(folder_data)


    def aturServer(self):
        # store endpoint configuration
        storeSetting("pengaturan/endpoint", self.comboBoxEndpoint.currentText())
        # store directories configuration
        storeSetting("pengaturan/direktoritemplate", self.direktoriTemplate.filePath())
        storeSetting("pengaturan/direktorikonfigurasi", self.direktoriKonfigurasi.filePath())
        storeSetting("pengaturan/direktoribataswilayah", self.direktoriBatasWilayah.filePath())

    
    def pengaturanBasemap(self):
        dirkonfig = readSetting("pengaturan/direktorikonfigurasi")
        print(dirkonfig)
        if not dirkonfig:
            dirkonfig = folder_config
            logMessage("Mengambil pengaturan basemap dari folder default plugin")
        self.fileBasemap.setFilePath(dirkonfig)
        linktofile = os.path.join(dirkonfig, "basemap.json")
        text=open(linktofile).read()
        self.textEditBasemap.setPlainText(text)


    def editBerkas(self):
        filepath = self.fileBasemap.filePath()
        data = self.textEditBasemap.toPlainText()
        try:
            with open(filepath,'w') as f:
                f.write(data)
        except Exception as e:
            dialogBox("Gagal menyimpan berkas! Periksa log untuk melihat kesalahan")
            logMessage(str(e))


    def pengaturanLayer(self):
        dirkonfig = readSetting("pengaturan/direktorikonfigurasi")
        print(dirkonfig)
        if not dirkonfig:
            dirkonfig = folder_config
            logMessage("Mengambil pengaturan layer dari folder default plugin")
        self.fileLayer.setFilePath(dirkonfig)
        linktofile = os.path.join(dirkonfig, "layers.json")
        text=open(linktofile).read()
        self.textEditLayer.setPlainText(text)


    def editLayer(self):
        filepath = self.fileLayer.filePath()
        data = self.textEditLayer.toPlainText()
        try:
            with open(filepath,'w') as f:
                f.write(data)
        except Exception as e:
            dialogBox("Gagal menyimpan berkas! Periksa log untuk melihat kesalahan")
            logMessage(str(e))


    def pengaturanKantor(self):
        dirkonfig = readSetting("pengaturan/direktorikonfigurasi")
        print(dirkonfig)
        if not dirkonfig:
            dirkonfig = folder_config
            logMessage("Mengambil pengaturan kantor dari folder default plugin")
        self.fileKantor.setFilePath(dirkonfig)
        linktofile = os.path.join(dirkonfig, "daftar_kantor.json")
        text=open(linktofile).read()
        self.textEditKantor.setPlainText(text)


    def editKantor(self):
        filepath = self.fileKantor.filePath()
        data = self.textEditKantor.toPlainText()
        try:
            with open(filepath,'w') as f:
                f.write(data)
        except Exception as e:
            dialogBox("Gagal menyimpan berkas! Periksa log untuk melihat kesalahan")
            logMessage(str(e))

