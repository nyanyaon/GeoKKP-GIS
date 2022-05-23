import os
import json

from qgis.PyQt import QtWidgets, uic
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../../ui/link_pbt/link_pbt.ui")
)


STACKWIDGET_LOKASI = 0
STACKWIDGET_RUTIN = 1


class LinkPBT(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Link Peta Bidang"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(LinkPBT, self).__init__(parent)
        self.setupUi(self)

        self.tabWidget.currentChanged.connect(self._handle_tab_changed)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setup_workpanel(self):
        pass

    def _handle_tab_changed(self, index):
        current_tab = self.tabWidget.widget(index)
        current_tab.setup_workpanel()
