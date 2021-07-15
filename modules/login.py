import os
import re
import requests
import json


from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import QUrl, QUrlQuery, pyqtSignal, QByteArray
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface
from qgis.core import QgsMessageLog, Qgis

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
        #self.mockURL = "https://daac4efe-c84b-4901-81a7-3a80278986ed.mock.pstmn.io"

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
        """

        username = self.inputUsername.text()
        password = self.inputPassword.text()

        formaturl = '{}/validateUser'.format(self.baseURL)

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

        response = requests.request("POST", formaturl, headers=headers, data=payload)
        response_json = response.json()
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
        else:
            print(status)
            if self.isSaved:
                storeSetting("isLoggedIn", status)
                print("Informasi pengguna disimpan")
            self.closedone()


















    # TODO: use qgis networkmanager instead of request
    def doLogin(self):
        """
        Login ke API GeoKKP dengan username dan password
        Versi API: 4.3.0.0
        """

        self.HEADERS = {b'Content-Type': b'application/json'}
        
        username = self.inputUsername.text()
        password = self.inputPassword.text()

        formaturl = '{}/validateUser'.format(self.baseURL)
        params = {           
                "providerName": "OracleMembershipProvider",
                "applicationName": "KKPWeb",
                "username": "permenas",
                "password": "permenas2016",
                "versi": "4.3.0.0"
            }

        url_detail = self.url_with_param(formaturl, params)

        params = QByteArray()
        #params.addQueryItem("providerName", "OracleMembershipProvider")
        #params.append("applicationName", "KKPWeb")
        params.append("username=permenas&")
        params.append("password=permenas2016")
        #params.append("versi", "4.3.0.0")

        #data = params.encodedQuery()
        
        try:
            (response, content) = self.nam.request(formaturl, method="POST", body=params, headers=self.HEADERS)
            print("test print")
            print('xx response: {}'.format(response))
            print('xx content: {}'.format(content))
        except:
            # pass dulu
            # Handle exception
            errno, strerror = RequestsException.args
            print('!!!!!!!!!!! EXCEPTION !!!!!!!!!!!!!: \n{}\n{}'. format(errno, strerror))
            pass



        


        
