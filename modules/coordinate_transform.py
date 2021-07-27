import os

from qgis.PyQt.QtGui import QIcon

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

# using utils
from .utils import icon

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/coordtrans.ui'))


class CoordinateTransformDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for coordinate transformation. """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(CoordinateTransformDialog, self).__init__(parent)
        self.setWindowIcon(icon("icon.png"))
        self.setupUi(self)

        # Set copy icon
        copy_icon = QIcon(':/images/themes/default/mActionEditCopy.svg')
        self.latlong_copy_button.setIcon(copy_icon)
        self.utm_copy_button.setIcon(copy_icon)
        self.tm3_copy_button.setIcon(copy_icon)

        # Set copy icon
        copy_icon = QIcon(':/images/themes/default/transformation.svg')
        self.latlong_convert_button.setIcon(copy_icon)
        self.utm_convert_button.setIcon(copy_icon)
        self.tm3_convert_button.setIcon(copy_icon)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
