import os
import math

from qgis.PyQt import QtWidgets, uic    # , QtXml
from qgis.core import QgsProject, QgsPointXY, QgsFeature, QgsGeometry, QgsVectorLayer, Qgis

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.gui import QgsVertexMarker, QgsMessageBar

from .maptools import MapTool
# using utils
from .utils import icon


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/triangulation.ui'))


class TriangulationDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Peta Bidang """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(TriangulationDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(icon("icon.png"))

        self.list_vm = []

        self.dialog_bar = QgsMessageBar()
        self.dialog_bar.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.layout().insertWidget(0, self.dialog_bar)  # , 0, 1, 1)

    def on_btn_titik_1t_pressed(self):
        try:
            self.iface.mapCanvas().scene().removeItem(self.vm_1)
        except: # noqa
            pass
        self.vm_1 = self.create_vertex_marker()
        self.list_vm.append(self.vm_1)
        self.point_tool_1 = MapTool(self.canvas, self.vm_1)
        self.point_tool_1.map_clicked.connect(self.update_titik_1)

        self.point_tool_1.isEmittingPoint = True
        self.iface.mapCanvas().setMapTool(self.point_tool_1)

    def update_titik_1(self, x, y):
        self.point_1 = QgsPointXY(x, y)
        self.coord_point_1t.setText(str(x) + ',' + str(y))
        self.iface.mapCanvas().unsetMapTool(self.point_tool_1)

    def on_btn_titik_2t_pressed(self):
        try:
            self.iface.mapCanvas().scene().removeItem(self.vm_2)
        except: # noqa
            pass
        self.vm_2 = self.create_vertex_marker()
        self.list_vm.append(self.vm_2)
        self.point_tool_2 = MapTool(self.canvas, self.vm_2)
        self.point_tool_2.map_clicked.connect(self.update_titik_2)

        self.point_tool_2.isEmittingPoint = True
        self.iface.mapCanvas().setMapTool(self.point_tool_2)

    def update_titik_2(self, x, y):
        self.point_2 = QgsPointXY(x, y)
        self.coord_point_2t.setText(str(x) + ',' + str(y))
        self.iface.mapCanvas().unsetMapTool(self.point_tool_2)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def on_btn_cancel_pressed(self):
        print('cancel triggered')
        self.clear()
        self.close()

    def on_btn_ok_pressed(self):
        # create a memory vector
        project_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        project_epsg = project_crs.authid()
        vl = QgsVectorLayer("Point?crs="+project_epsg, "trilateration point", "memory")

        p1 = self.point_1
        p2 = self.point_2

        az1 = self.detect_az_format(self.azimuth_1.text())
        az2 = self.detect_az_format(self.azimuth_2.text())

        if az1 and az2:
            pt = self.triangulate(p1, p2, az1, az2)

            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(pt))

            vl.startEditing()
            vl.addFeatures([feat])
            vl.commitChanges()

            QgsProject.instance().addMapLayer(vl)
            self.clear()
            self.close()
        else:
            pass

    def triangulate(self, p1, p2, az1, az2):
        x1 = p1.x()
        y1 = p1.y()

        x2 = p2.x()
        y2 = p2.y()

        m1 = 1/math.tan(math.radians(az1))
        m2 = 1/math.tan(math.radians(az2))

        a1 = 1
        b1 = -1/m1
        c1 = -b1*y1 - a1*x1

        a2 = 1
        b2 = -1/m2
        c2 = -b2*y2 - a2*x2

        print('abcm1', a1, b1, c1, m1)
        print('abcm2', a2, b2, c2, m2)

        x3 = ((b1*c2)-(b2*c1))/((a1*b2)-(a2*b1))
        y3 = ((c1*a2)-(c2*a1))/((a1*b2)-(a2*b1))

        print('p3', x3, y3)

        return QgsPointXY(x3, y3)

    def create_vertex_marker(self, type='BOX'):
        vm = QgsVertexMarker(self.canvas)

        if type == 'BOX':
            icon_type = QgsVertexMarker.ICON_BOX
        elif type == 'CIRCLE':
            icon_type = QgsVertexMarker.ICON_CIRCLE
        elif type == 'CROSS':
            icon_type = QgsVertexMarker.ICON_CROSS
        else:
            icon_type = QgsVertexMarker.ICON_X

        vm.setIconType(icon_type)
        vm.setPenWidth(3)
        vm.setIconSize(7)
        return vm

    def clear(self):
        self.coord_point_1t.clear()
        self.coord_point_2t.clear()

        self.azimuth_1.clear()
        self.azimuth_2.clear()

        for vm in self.list_vm:
            try:
                self.iface.mapCanvas().scene().removeItem(vm)
            except: # noqa
                pass

    def detect_az_format(self, az_str):
        az_split = az_str.split(' ')
        if len(az_split) == 3:
            d = float(az_split[0])
            m = float(az_split[1])
            s = float(az_split[2])

            return d + (m/60) + (s/3600)
        elif len(az_split) == 1:
            return float(az_str)
        else:
            message = "Format tidak dikenali. Gunakan spasi sebagai pemisah."
            self.dialog_bar.pushMessage("Warning", message, level=Qgis.Warning)
            return
