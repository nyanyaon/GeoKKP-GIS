import configparser
import os
import json
from pathlib import Path

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.core import Qgis, QgsProject, QgsRectangle
from qgis.gui import QgsMessageBar

from .utils import (
    add_google_basemap,
    get_project_crs,
    set_project_crs_by_epsg,
    storeSetting,
    readSetting,
    dialogBox,
    get_saved_credentials,
    save_credentials,
)

from .api import endpoints
from .memo import app_state
from .postlogin import PostLoginDock
from .settings.settings_widgets import SettingsDialog


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/login.ui")
)


class LoginDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Login"""

    closingPlugin = pyqtSignal()
    loginChanged = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)

        self.settingPage = SettingsDialog()
        self.bar = QgsMessageBar()

        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), "..", 'metadata.txt'))
        version = config.get('general', 'version')        
        self.teksVersi.setText("<p>Versi <a href='https://github.com/danylaksono/GeoKKP-GIS'> \
            <span style='text-decoration: underline; color:#009da5;'>" + version + "</span></a></p>")
        # login action
        self.buttonBoxLogin.clicked.connect(self.doLoginRequest)

    def _autofill_credentials(self):
        credentials = get_saved_credentials()
        if set(["username", "password"]).issubset(credentials.keys()):
            self.inputUsername.setText(credentials["username"])
            self.inputPassword.setText(credentials["password"])

    def showEvent(self, event):
        self._autofill_credentials()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def closedone(self):
        self.close()

    def doLoginRequest(self):
        """
        Login using requests
        API backend: {}/validateUser
        """
        username = self.inputUsername.text()
        password = self.inputPassword.text()
        
        # logMessage(f"{username}, {password}")
        try:
            response = endpoints.login(username, password)
            content = json.loads(response.content)
            if not content["status"]:
                dialogBox(
                    content["information"],
                )
            else:
                if self.checkboxSaveLogin.isChecked():
                    save_credentials(username, password)
                    storeSetting("isLoggedIn", content["status"])
                # logMessage(str(content))
                self.iface.messageBar().pushMessage(
                    "Login Pengguna Berhasil:", username, level=Qgis.Success
                )
                self.loginChanged.emit()
                app_state.set("username", username)
                # self.getKantorProfile(username)
                # self.get_user(username)
                # daftarUser = readSetting("daftarUser")
                self.postuserlogin()
                script_dir = Path(os.path.dirname(__file__)).parents[1]
                file_path = os.path.join(script_dir, 'file.json')
                try:
                    if(os.path.exists(file_path)):
                        print(file_path,"file_path")
                        with open(file_path, "r") as outfile:
                            data = json.load(outfile)
                            print(data,"datauser")
                        
                        result = [a for a in data["data_user"] if a["username"] == username]
                        if(len(result)==0):
                            self.settingPage.show()
                        else:
                            self.settingPage.get_pagawai(result[0]["kantor"])
                            self.settingPage.simpan_tm3(result[0]["tm3"])
                    else:
                        self.settingPage.show()
                except Exception as e:
                    self.settingPage.show()   

        except Exception as e:
            print(e)
            dialogBox(
                "Kesalahan koneksi. Periksa sambungan Anda ke server GeoKKP",
                "Koneksi Bermasalah",
                "Warning",
            )

    def get_geo_profile(self, kantor_id):
        try:
            response = endpoints.get_is_e_sertifikat(kantor_id)
            is_e_sertifikat = response.content == "1"
            storeSetting("isESertifikat", is_e_sertifikat)
        except Exception as e:
            # print(e)
            dialogBox(
                "Gagal mengambil status data e-sertifikat dari server",
                "Koneksi Bermasalah",
                "Warning",
            )

    def get_user(self, username):
        response = endpoints.get_user_by_username(username)
        response_json = json.loads(response.content)
        # print("get_user_by_username", response_json)
        app_state.set("user", response_json)

    def getKantorProfile(self, username):
        """
        user entity
        API backend: {}/getEntityByUserName
        """
        try:
            response = endpoints.get_entity_by_username(username)
        except Exception as e:
            # print(e)
            dialogBox(
                "Data Pengguna gagal dimuat dari server",
                "Koneksi Bermasalah",
                "Warning",
            )

        if response is not None:
            response_json = json.loads(response.content)
            storeSetting("jumlahkantor", len(response_json))
            storeSetting("listkantor", response_json)
            if self.postlogin.populateKantah(response_json):
                self.postuserlogin()
        else:
            dialogBox(
                "Data Pengguna gagal disimpan ke dalam QGIS",
                "Koneksi Bermasalah",
                "Warning",
            )

    def postuserlogin(self,epsg = "EPSG:4326"):
        """
        what to do when user is logged in
        """   
        # print(get_project_crs())
        set_project_crs_by_epsg(epsg)
        rect = QgsRectangle(95.0146, -10.92107, 140.9771, 5.9101)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()
        self.accept()
        app_state.set("logged_in", True)

