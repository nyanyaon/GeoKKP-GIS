import os
import math

from qgis.PyQt import QtWidgets, uic, QtXml, QtGui, QtCore

from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry, QgsVectorLayer
)

from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMessageBar, QgsRubberBand

from .maptools import MapTool

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/dimension_distance.ui'))

class DrawDimensionDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Peta Bidang """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(DrawDimensionDialog, self).__init__(parent)
        self.setupUi(self)

    def on_btnDrawDist_pressed(self):
        self.drawtool = DrawTool(self.canvas)

        self.iface.mapCanvas().setMapTool(self.drawtool)
        self.drawtool.finished_adding.connect(self.finished)
    
    def finished(self, geom):
        self.iface.mapCanvas().unsetMapTool(self.drawtool)
        print(geom.length())
        

    def on_btnEditDist_pressed(self):
        print("Edit pressed")

    def on_btnEraseDist_pressed(self):
        self.iface.mapCanvas().unsetMapTool(self.drawtool)
        print("Erase pressed")

class DrawTool(QgsMapTool):

    finished_adding = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas

        self.isEmittingPoint = True

        self.add_mode = False
        self.move_mode = False

        self.vm_1 = self.create_vertex_marker('CROSS')
        self.vm_2 = self.create_vertex_marker('CIRCLE')
        
        self.rb_draw = self.create_rubberband()
        self.rb_main = self.create_rubberband()
        self.rb_start = self.create_rubberband('DASH_LINE')
        self.rb_end = self.create_rubberband('DASH_LINE')

        self.list_vm = []
        self.list_vm.append(self.vm_1)
        self.list_vm.append(self.vm_2)

        self.click_counter = 0

    def reset(self):
        self.isEmittingPoint = False
    
    def canvasMoveEvent(self, event):
        point_snap = self.snapping_point(event.pos())
        if self.click_counter == 0: # proceed to add start point
            self.vm_1.setCenter(point_snap)
        
        elif self.click_counter == 1: # proceed to add end point
            self.vm_2.setCenter(point_snap)
            list_point = [self.start_point, point_snap]
            draw_geom = QgsGeometry().fromPolylineXY(list_point)
            self.rb_draw.setToGeometry(draw_geom)
        
        elif self.click_counter == 2: # proceed to start offsetting
            p = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            sqrdist, pt, nid, side = self.main_geom.closestSegmentWithContext(p)
            dist = math.sqrt(sqrdist)
            self.offset_geom = self.main_geom.offsetCurve(-side*dist, 6, 1, 1)
            _, offset_start, _, _ = self.offset_geom.closestSegmentWithContext(self.start_point)
            _, offset_end, _, _ = self.offset_geom.closestSegmentWithContext(self.end_point)
            start_point_list = [self.start_point, offset_start]
            end_point_list = [self.end_point, offset_end]
            self.start_geom = QgsGeometry.fromPolylineXY(start_point_list)
            self.end_geom = QgsGeometry.fromPolylineXY(end_point_list)
            self.rb_start.setToGeometry(self.start_geom)
            self.rb_end.setToGeometry(self.end_geom)
            self.rb_main.setToGeometry(self.offset_geom)

    def canvasReleaseEvent(self, event):
        self.click_counter += 1
        self.point_snap = self.snapping_point(event.pos())
        
        if self.click_counter == 1: # indicates finished adding first point
            self.add_mode = True
            self.move_mode = False
            print("Canvas clicked for the first time")
            self.vm_1.setCenter(self.point_snap)
            self.start_point = self.point_snap

        elif self.click_counter == 2: # indicates finished adding second point
            self.vm_2.setCenter(self.point_snap)
            self.end_point = self.point_snap
            print("Canvas clicked for the second time")
            list_point_main = [self.start_point, self.end_point]
            self.main_geom = QgsGeometry().fromPolylineXY(list_point_main)
            self.rb_main.setToGeometry(self.main_geom)
            self.add_mode = False
            self.move_mode = True
        
        elif self.click_counter == 3: #indicates finished offsetting line
            print("Canvas clicked for the third time")
            print("resetting counter to zero")
            self.canvas.scene().removeItem(self.vm_1)
            self.canvas.scene().removeItem(self.vm_2)
            self.finished_adding.emit(self.offset_geom)
            self.click_counter = 0

        
        # self.map_clicked.emit(self.point_snap.x(), self.point_snap.y())

    def canvasDoubleCLickEvent(self, event):
        print("canvas doubleclicked")

    def snapping_point(self, point):
        snapped = self.canvas.snappingUtils().snapToMap(point)
        if snapped.isValid():
            return snapped.point()
        else:
            return self.canvas.getCoordinateTransform().toMapCoordinates(point) 
    
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

    def create_rubberband(self, line_style = 'SOLID_LINE'):
        rb = QgsRubberBand(self.canvas, False)
        rb.setStrokeColor(QtGui.QColor(128, 128, 128, 180)) # grey
        rb.setFillColor(QtGui.QColor(0, 0, 0, 0))
        rb.setWidth(1)
        if line_style == 'DASH_LINE':
            rb.setLineStyle(QtCore.Qt.DashLine)
        elif line_style == 'SOLID_LINE':
            rb.setLineStyle(QtCore.Qt.SolidLine)
        elif line_style == 'DOT_LINE':
            rb.setLineStyle(QtCore.Qt.DotLine)
        return rb
