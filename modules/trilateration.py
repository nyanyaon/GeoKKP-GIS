import os
import math

from qgis.PyQt import QtWidgets, uic
from qgis.core import (
    QgsProject,
    # QgsPrintLayout,
    # QgsReadWriteContext,
    # QgsExpressionContextUtils,
    QgsPointXY,
    QgsFeature,
    QgsGeometry,
    QgsVectorLayer
)


from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.gui import QgsVertexMarker

from .maptools import MapTool
# using utils
from .utils import icon


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/trilateration.ui'))


class TrilaterationDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Peta Bidang """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(TrilaterationDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(icon("icon.png"))

        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.connect(self.rejected)

        self.list_vm = []

    def on_btn_titik_1_pressed(self):
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
        self.coord_point_1.setText(str(x) + ',' + str(y))
        self.iface.mapCanvas().unsetMapTool(self.point_tool_1)

    def on_btn_titik_2_pressed(self):
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
        self.coord_point_2.setText(str(x) + ',' + str(y))
        self.iface.mapCanvas().unsetMapTool(self.point_tool_2)

    def on_btn_titik_3_pressed(self):
        try:
            self.iface.mapCanvas().scene().removeItem(self.vm_3)
        except: # noqa
            pass
        self.vm_3 = self.create_vertex_marker()
        self.list_vm.append(self.vm_3)
        self.point_tool_3 = MapTool(self.canvas, self.vm_3)
        self.point_tool_3.map_clicked.connect(self.update_titik_3)

        self.point_tool_3.isEmittingPoint = True
        self.iface.mapCanvas().setMapTool(self.point_tool_3)

    def update_titik_3(self, x, y):
        self.point_3 = QgsPointXY(x, y)
        self.coord_point_3.setText(str(x) + ',' + str(y))
        self.iface.mapCanvas().unsetMapTool(self.point_tool_3)

    # --------------------------

    def on_btn_titik_1a_pressed(self):
        try:
            self.iface.mapCanvas().scene().removeItem(self.vm_1a)
        except: # noqa
            pass
        self.vm_1a = self.create_vertex_marker()
        self.list_vm.append(self.vm_1a)
        self.point_tool_1a = MapTool(self.canvas, self.vm_1a)
        self.point_tool_1a.map_clicked.connect(self.update_titik_1a)

        self.point_tool_1a.isEmittingPoint = True
        self.iface.mapCanvas().setMapTool(self.point_tool_1a)

    def update_titik_1a(self, x, y):
        self.point_1a = QgsPointXY(x, y)
        self.coord_point_1a.setText(str(x) + ',' + str(y))
        self.iface.mapCanvas().unsetMapTool(self.point_tool_1a)

    def on_btn_titik_2a_pressed(self):
        try:
            self.iface.mapCanvas().scene().removeItem(self.vm_2a)
        except: # noqa
            pass
        self.vm_2a = self.create_vertex_marker()
        self.list_vm.append(self.vm_2a)
        self.point_tool_2a = MapTool(self.canvas, self.vm_2a)
        self.point_tool_2a.map_clicked.connect(self.update_titik_2a)

        self.point_tool_2a.isEmittingPoint = True
        self.iface.mapCanvas().setMapTool(self.point_tool_2a)

    def update_titik_2a(self, x, y):
        self.point_2a = QgsPointXY(x, y)
        self.coord_point_2a.setText(str(x) + ',' + str(y))
        self.iface.mapCanvas().unsetMapTool(self.point_tool_2a)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()  

    def rejected(self):
        print('cancel triggered')
        self.clear()
        self.reject()
            
    def accepted(self):
        # self.accept()
        # dist_12 = math.sqrt(self.point_1.sqrDist(self.point_2))
        # dist_23 = math.sqrt(self.point_2.sqrDist(self.point_3))
        # dist_13 = math.sqrt(self.point_1.sqrDist(self.point_3))

        # create a memory vector
        project_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        project_epsg = project_crs.authid()
        vl = QgsVectorLayer("Point?crs="+project_epsg, "trilateration point", "memory")

        if self.tabWidget.currentIndex() == 0:
            # Two points result in two point option
            # Distance
            d1 = float(self.distance_1a.text())
            d2 = float(self.distance_2a.text())
            a, b = self.two_points(self.point_1a, self.point_2a, d1, d2)

            # show result as vertex marker
            # self.vm_a = self.create_vertex_marker('CROSS')
            # self.list_vm.append(self.vm_a)
            # self.vm_b = self.create_vertex_marker('CROSS')
            # self.list_vm.append(self.vm_b)

            # self.vm_a.setCenter(a)
            # self.vm_b.setCenter(b)
         
            feat_a = QgsFeature()
            feat_a.setGeometry(QgsGeometry.fromPointXY(a))
            feat_b = QgsFeature()
            feat_b.setGeometry(QgsGeometry.fromPointXY(b))

            vl.startEditing()
            vl.addFeatures([feat_a, feat_b])
            vl.commitChanges()       

        else:
            # three points result in a single points option
            # distance
            d1 = float(self.distance_1.text())
            d2 = float(self.distance_2.text())
            d3 = float(self.distance_3.text())

            p1 = self.point_1
            p2 = self.point_2
            p3 = self.point_3

            pt = self.three_points(p1, p2, p3, d1, d2, d3)

            feat_pt = QgsFeature()
            feat_pt.setGeometry(QgsGeometry.fromPointXY(pt))

            vl.startEditing()
            vl.addFeatures([feat_pt])
            vl.commitChanges()
        
        QgsProject.instance().addMapLayer(vl)
        self.clear()   

        print('accept triggered on tab ' + str(self.tabWidget.currentIndex()))

    def two_points(self, p1, p2, d1, d2):
        '''Calculate two solutions of two points trilateration.'''
        d = math.sqrt(p1.sqrDist(p2))

        a = (d1*d1 - d2*d2 + d*d)/(2*d)
        h = math.sqrt(d1*d1 - a*a)
        
        x1 = p1.x()
        y1 = p1.y()

        x2 = p2.x()
        y2 = p2.y()

        xo = x1 + a*(x2-x1)/d
        yo = y1 + a*(y2-y1)/d
        
        x3a = xo + h*(y2-y1)/d
        y3a = yo - h*(x2-x1)/d

        x3b = xo - h*(y2-y1)/d
        y3b = yo + h*(x2-x1)/d
        
        print(a, h, d)

        return QgsPointXY(x3a, y3a), QgsPointXY(x3b, y3b)

    def three_points(self, p1, p2, p3, d1, d2, d3):

        x1 = p1.x()
        y1 = p1.y()
        x2 = p2.x()
        y2 = p2.y()
        x3 = p3.x()
        y3 = p3.y()

        m = x1-x2
        n = y2-y1
        o = x1*x1 - x2*x2
        p = y1*y1 - y2*y2
        q = d2*d2 - d1*d1

        r = x1-x3 
        s = y3-y1
        t = x1*x1 - x3*x3
        u = y1*y1 - y3*y3
        v = d3*d3 - d1*d1

        y = (r*(o+p+q) - m*(t+u+v))/(2*(s*m - n*r))
        x = (2*y*n + o + p + q)/(2*m)

        return QgsPointXY(x, y)

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
        self.coord_point_1a.clear()
        self.coord_point_2a.clear()

        self.coord_point_1.clear()
        self.coord_point_2.clear()
        self.coord_point_3.clear()

        self.distance_1a.clear()
        self.distance_2a.clear()
        self.distance_1.clear()
        self.distance_2.clear()
        self.distance_3.clear()

        for vm in self.list_vm:
            try:
                self.iface.mapCanvas().scene().removeItem(vm)
            except: # noqa
                pass
