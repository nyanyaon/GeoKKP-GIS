import os
import re
import requests
import json


from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import QUrl, QUrlQuery, pyqtSignal, QByteArray
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface
from qgis.core import QgsMessageLog, Qgis
from qgis.gui import QgsMessageBar

from .utils import storeSetting, readSetting



from .networkaccessmanager import NetworkAccessManager, RequestsException
from qgis.core import QgsNetworkAccessManager, QgsAuthManager



FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/login.ui'))


class LoginDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Login """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)

        #replace Request with built in QGIS Network httplib2
        self.nam = NetworkAccessManager()
        #self.nam = QgsNetworkAccessManager(self)

        # API URL: ganti dengan API terbaru pada versi production
        self.baseURL = "http://10.20.22.90:5001/spatialapi"
        self.mockURL = "https://daac4efe-c84b-4901-81a7-3a80278986ed.mock.pstmn.io"

        self.bar = QgsMessageBar()

        #login action
        self.buttonBoxLogin.clicked.connect(self.doLoginRequest)
        if self.checkboxSaveLogin.isChecked:
            self.isSaved = True
        else:
            self.isSaved = False


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
    
    def closedone(self):
        self.close()

    @staticmethod
    def url_with_param(url, params) -> str:
        """
        Construct URL
        """
        url = QUrl(url)
        q = QUrlQuery(url)
        for key, value in params.items():
            q.addQueryItem(key, value)
        url.setQuery(q)
        return url.url()


    def doLoginRequest(self):
        """
        Login using requests
        API backend: {}/validateUser
        """

        username = self.inputUsername.text()
        password = self.inputPassword.text()

        formaturl = '{}/validateUser'.format(self.baseURL)
        #formaturl = '{}/validateUser'.format(self.mockURL)

        payload = json.dumps({
            "providerName": "OracleMembershipProvider",
            "applicationName": "KKPWeb",
            "username": username,
            "password": password,
            "versi": "4.3.0.0"
        })

        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request("POST", formaturl, headers=headers, data=payload)
            response_json = response.json()
            print(response_json)
            status = response_json['status']
            informasi = response_json['information']
            if not status:
                message = QMessageBox()
                message.setIcon(QMessageBox.Information)
                message.setText(informasi)
                message.setWindowTitle("Peringatan")
                message.setStandardButtons(QMessageBox.Ok)
                message.exec()
                #message.buttonClicked.connect(msgButtonClick)
                
                #FOR DEBUG ONLY
                print("bypass username:", username)
                self.profilUser(username)
                
            else:
                print(status)
                if self.isSaved:
                    storeSetting("geokkp/isLoggedIn", status)
                    print("Informasi pengguna disimpan")
                    self.iface.messageBar().pushMessage("Login Pengguna Berhasil:", username, level=Qgis.Success)
                self.closedone()
        except:
            pass

    def profilUser(self, username):
        """
        user entity 
        API backend: {}/getEntityByUserName
        """

        formaturl = '{}/getEntityByUserName'.format(self.baseURL)

        payload = json.dumps({
            "username": username
        })
        headers = {
         'Content-Type': 'application/json'
        }

        response = requests.request("POST", formaturl, headers=headers, data=payload)
        response_json = response.json()
        print(response_json[0]["nama"])
        storeSetting("geokkp/jumlahkantor", len(response_json))
        storeSetting("geokkp/listkantor", response_json)
        self.iface.messageBar().pushMessage("Simpan Data:", "Data kantor pengguna berhasil disimpan", level=Qgis.Success)

        
            
    







        


        
