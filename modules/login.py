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
            self.profilKantor(username)
            self.loginChanged.emit()
            app_state.set('username', username)
            app_state.set('logged_in', True)
            self.accept()

    def profilKantor(self, username):
        """
        user entity
        API backend: {}/getUserEntityByUserName
        """

        response = endpoints.get_entity_by_username(username)
        response_json = json.loads(response.content)
        # print(response_json[0]["nama"])
        storeSetting("geokkp/jumlahkantor", len(response_json))
        storeSetting("geokkp/listkantor", response_json)
        self.iface.messageBar().pushMessage(
            "Simpan Data:",
            "Data kantor pengguna berhasil disimpan",
            level=Qgis.Success
        )
