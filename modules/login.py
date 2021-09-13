import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface
from qgis.core import Qgis
from qgis.gui import QgsMessageBar

from .utils import (
    storeSetting,
    logMessage,
    get_saved_credentials,
    save_credentials
)

from .api import endpoints
from .memo import app_state


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/login.ui'))


class LoginDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Login """

    closingPlugin = pyqtSignal()
    loginChanged = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)

        self.bar = QgsMessageBar()

        # login action
        self.buttonBoxLogin.clicked.connect(self.doLoginRequest)

    def _autofill_credentials(self):
        credentials = get_saved_credentials()
        if set(['username', 'password']).issubset(credentials.keys()):
            self.inputUsername.setText(credentials['username'])
            self.inputPassword.setText(credentials['password'])

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
        logMessage(f'{username}, {password}')
        try:
            response = endpoints.login(username, password)
            content = json.loads(response.content)
            if not content['status']:
                message = QMessageBox(parent=self)
                message.setIcon(QMessageBox.Information)
                message.setText(content['information'])
                message.setWindowTitle("Peringatan")
                message.setStandardButtons(QMessageBox.Ok)
                message.exec()
            else:
                if self.checkboxSaveLogin.isChecked():
                    save_credentials(username, password)
                    storeSetting("geokkp/isLoggedIn", content['status'])
                logMessage(str(content))
                self.iface.messageBar().pushMessage("Login Pengguna Berhasil:", username, level=Qgis.Success)
                self.loginChanged.emit()
                app_state.set('username', username)
                app_state.set('logged_in', True)
                self.accept()
                self.getKantorProfile(username)
        except Exception:
            message = QMessageBox(parent=self)
            message.setIcon(QMessageBox.Critical)
            message.setText("Kesalahan koneksi. Periksa sambungan Anda ke server GeoKKP")
            message.setWindowTitle("Koneksi bermasalah")
            message.setStandardButtons(QMessageBox.Ok)
            message.exec()

    def getKantorProfile(self, username):
        """
        user entity
        API backend: {}/getEntityByUserName
        """
        try:
            response = endpoints.get_entity_by_username(username)
            response_json = json.loads(response.content)
            storeSetting("geokkp/jumlahkantor", len(response_json))
            storeSetting("geokkp/listkantor", response_json)
            logMessage(
                "Data kantor pengguna berhasil disimpan",
                level=Qgis.Success
            )
        except Exception as e: # noqa
            print("ada error ketika login", e)
            message2 = QMessageBox(parent=self)
            message2.setIcon(QMessageBox.Warning)
            message2.setText("Data Pengguna gagal dimuat dari server")
            message2.setWindowTitle("Terjadi Kesalahan")
            message2.setStandardButtons(QMessageBox.Ok)
            message2.exec()
            