import os
from functools import partial

from qgis.PyQt.QtGui import QIcon

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QApplication, QDialog
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

from qgis.core import (
    QgsCoordinateTransform,
    QgsProject,
    QgsCoordinateReferenceSystem)

# using utils
from .utils import icon, parse_raw_coordinate

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/coordtrans.ui'))


class CoordinateTransformDialog(QDialog, FORM_CLASS):
    """ Dialog for coordinate transformation. """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(CoordinateTransformDialog, self).__init__(parent)
        self.setWindowIcon(icon("icon.png"))
        self.setupUi(self)

        # Clipboard
        self.clipboard = QApplication.clipboard()

        # Line edit
        self.lineedits = [
            self.latlong_lineedit,
            self.utm_lineedit,
            self.tm3_lineedit,
        ]

        # Copy buttons
        self.copy_buttons = [
            self.latlong_copy_button,
            self.utm_copy_button,
            self.tm3_copy_button
        ]

        self.transform_buttons = [
            self.latlong_convert_button,
            self.utm_convert_button,
            self.tm3_convert_button
        ]

        # CRS
        self.names = [
            "Lat long",  # lat long
            "UTM",  # UTM ?
            "TM3",  # TM3 ?
        ]

        # CRS
        # TODO: cek CRSnya sudah benar atau tidak
        self.coordinate_systems = [
            QgsCoordinateReferenceSystem("EPSG:4326"),  # lat long
            QgsCoordinateReferenceSystem("EPSG:32749"),  # UTM ?
            QgsCoordinateReferenceSystem("EPSG:3857"),  # TM3 ?
        ]

        # Copy icon
        copy_icon = QIcon(':/images/themes/default/mActionEditCopy.svg')
        # Transform icon
        transform_icon = QIcon(':/images/themes/default/transformation.svg')

        # Connect the transform buttons
        for i in range(len(self.transform_buttons)):
            self.transform_buttons[i].setIcon(transform_icon)
            self.transform_buttons[i].clicked.connect(partial(self.transform_clicked, i))
            self.transform_buttons[i].setToolTip("Transformasi koordinat dari %s" % self.names[i])

        # Connect the copy buttons
        for i in range(len(self.copy_buttons)):
            self.copy_buttons[i].setIcon(copy_icon)
            self.copy_buttons[i].clicked.connect(partial(self.copy_clicked, i))
            self.copy_buttons[i].setToolTip("Salin koordinat dari %s" % self.names[i])

    def transform_coordinate(self, source_crs, target_crs, point):
        trans = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
        new_point = trans.transform(point)
        return new_point

    def parse_coordinate(self, lineedit_index):
        coordinate_text = self.lineedits[lineedit_index].text()
        points = parse_raw_coordinate(coordinate_text)
        # TODO: Extend with more than one coordinates
        first_point = next(points)
        return first_point

    def transform_clicked(self, button_index):
        point = self.parse_coordinate(button_index)

        for i in range(len(self.coordinate_systems)):
            if i != button_index:
                new_point = self.transform_coordinate(
                            self.coordinate_systems[button_index], self.coordinate_systems[i], point)
                self.lineedits[i].setText("%f, %f" % (new_point.x(), new_point.y()))

    def copy_clicked(self, button_index):
        text = self.lineedits[button_index].text()
        self.clipboard.setText(text)
        self.iface.statusBarIface().showMessage(
            "'{}' dari {} berhasil disalin".format(text, self.names[button_index]), 3000)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
