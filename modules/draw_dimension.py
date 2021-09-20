import os
import math

from qgis.PyQt import QtWidgets, uic, QtXml, QtGui, QtCore

from qgis.core import (
    QgsCircle, QgsPoint, QgsPointXY, QgsFeature, QgsGeometry, QgsVectorLayer,
    QgsCircularString, QgsFeature, QgsField, QgsFields
)

from qgis.PyQt.QtCore import pyqtSignal, QVariant
from qgis.utils import iface
from qgis.gui import (
    QgsMapTool, QgsVertexMarker, QgsMessageBar, QgsRubberBand,
    QgsGeometryRubberBand
)

from .maptools import MapTool

# ----------------------------------------------------------- #
#                      Angle Dimension                        #
# ----------------------------------------------------------- #
class DimensionAngleTool(QgsMapTool):

    completed = pyqtSignal(QgsFeature)

    def __init__(self, iface):
        QgsMapTool.__init__(self, iface)
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.vm_center = create_vertex_marker(self.canvas, 'CIRCLE')
        self.vm_1 = create_vertex_marker(self.canvas, 'CROSS')
        self.vm_1.hide()
        self.vm_2 = create_vertex_marker(self.canvas, 'CROSS')
        self.vm_2.hide()

        self.rb_buffer = create_rubberband(self.canvas, 'SOLID')
        self.geomrb_buffer = create_geom_rubberband(self.canvas, 'SOLID')
        self.geomrb_short_arc = create_geom_rubberband(self.canvas, 'DOT_LINE')
        self.geomrb_long_arc = create_geom_rubberband(self.canvas, 'DOT_LINE')

        self.click_counter = 0

    def canvasMoveEvent(self, event):
        point_snap, status = snapping_point(self.canvas, event.pos())
        if self.click_counter == 0: # add center point
            self.vm_center.setCenter(point_snap)
        
        elif self.click_counter == 1: # create estimate buffer
            cur_pt = QgsPoint(point_snap)
            circle = QgsCircle.fromCenterPoint(self.center_pt, cur_pt)
            self.circular_string = circle.toCircularString()
            self.geomrb_buffer.setGeometry(self.circular_string)

        elif self.click_counter == 2: # get first arc point
            cur_pt = QgsPoint(point_snap)
            _, start_arc, _, _ = self.circular_string.closestSegment(cur_pt)
            self.vm_1.show()
            self.vm_1.setCenter(QgsPointXY(start_arc))
            
        elif self.click_counter == 3: # get second arc point
            cur_pt = QgsPoint(point_snap)
            _, end_arc, _, _ = self.circular_string.closestSegment(cur_pt)
            self.vm_2.show()
            self.vm_2.setCenter(QgsPointXY(end_arc))

        elif self.click_counter == 4: # choose segment
            p = QgsPoint(point_snap)
            
            nearest_arc = self.check_arc(p, self.shortest_arc, self.longest_arc)
            self.canvas.refresh()
            self.final_arc = nearest_arc

    def check_arc(self, point_check, short_arc, long_arc):
        a1, b1, c1, d1 = short_arc.closestSegment(point_check)
        a2, b2, c2, d2 = long_arc.closestSegment(point_check)

        if a1 < a2:
            arc_highlight(self.geomrb_short_arc)
            arc_dehighlight(self.geomrb_long_arc)
            return short_arc
        elif a1 > a2:
            arc_highlight(self.geomrb_long_arc)
            arc_dehighlight(self.geomrb_short_arc)
            return long_arc

    def canvasReleaseEvent(self, event):
        self.click_counter += 1
        point_snap, _ = snapping_point(self.canvas, event.pos())
        cur_pt = QgsPoint(point_snap)
        if self.click_counter == 1: # center point stored
            self.center_pt = QgsPoint(point_snap)
            # self.center_geom = QgsGeometry().fromPoint(self.center_pt)
            self.vm_center.setCenter(point_snap)
        
        elif self.click_counter == 2: # radius point stored
            self.radius_pt = QgsPointXY(point_snap)
        
        elif self.click_counter == 3: # start arc stored
            _, start_arc, _, _ = self.circular_string.closestSegment(cur_pt)
            self.start_arc_pt = start_arc

        elif self.click_counter == 4: # end arc stored
            _, end_arc, _, _ = self.circular_string.closestSegment(cur_pt)
            self.end_arc_pt = end_arc

            self.shortest_arc = QgsCircularString().fromTwoPointsAndCenter(
                self.start_arc_pt, self.end_arc_pt, self.center_pt, True
            )
            self.longest_arc = QgsCircularString().fromTwoPointsAndCenter(
                self.start_arc_pt, self.end_arc_pt, self.center_pt, False
            )
            self.geomrb_buffer.hide()
            self.geomrb_short_arc.setGeometry(self.shortest_arc)
            self.geomrb_long_arc.setGeometry(self.longest_arc)
        elif self.click_counter == 5: # arc finalised
            # fields = QgsFields()
            # fields.append(QgsField("dimtype", QVariant.String))
            # fields.append(QgsField("dimvalue", QVariant.String))
            # angle_feat = QgsFeature(fields)
            angle_feat = QgsFeature()
            angle_feat.setGeometry(self.final_arc)
            # angle_feat['dimtype'] = 'angle'
            # angle_feat['dimvalue'] = 'test value'
            self.completed.emit(angle_feat)
            
            try:
                self.canvas.scene().removeItem(self.vm_center)
                self.canvas.scene().removeItem(self.vm_1)
                self.canvas.scene().removeItem(self.vm_2)
                self.canvas.scene().removeItem(self.rb_buffer)
                self.canvas.scene().removeItem(self.geomrb_buffer)
                self.canvas.scene().removeItem(self.geomrb_short_arc)
                self.canvas.scene().removeItem(self.geomrb_long_arc)
            except:
                pass


        
# ----------------------------------------------------------- #
#                     Distance Dimension                      #
# ----------------------------------------------------------- #
class DimensionDistanceTool(QgsMapTool):

    completed = pyqtSignal(QgsFeature)

    def __init__(self, iface):
        QgsMapTool.__init__(self, iface)
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.vm_1 = create_vertex_marker(self.canvas, 'CROSS')
        self.vm_2 = create_vertex_marker(self.canvas, 'CIRCLE')
        
        self.rb_draw = create_rubberband(self.canvas)
        self.rb_main = create_rubberband(self.canvas)
        self.rb_start = create_rubberband(self.canvas, 'DASH_LINE')
        self.rb_end = create_rubberband(self.canvas, 'DASH_LINE')

        self.list_vm = []
        self.list_vm.append(self.vm_1)
        self.list_vm.append(self.vm_2)

        self.click_counter = 0
    
    def canvasMoveEvent(self, event):
        point_snap, _ = snapping_point(self.canvas, event.pos())
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
        self.point_snap, _ = snapping_point(self.canvas, event.pos())
        
        if self.click_counter == 1: # indicates finished adding first point
            # print("Canvas clicked for the first time")
            self.vm_1.setCenter(self.point_snap)
            self.start_point = self.point_snap

        elif self.click_counter == 2: # indicates finished adding second point
            self.vm_2.setCenter(self.point_snap)
            self.end_point = self.point_snap
            # print("Canvas clicked for the second time")
            list_point_main = [self.start_point, self.end_point]
            self.main_geom = QgsGeometry().fromPolylineXY(list_point_main)
            self.rb_main.setToGeometry(self.main_geom)
        
        elif self.click_counter == 3: #indicates finished offsetting line           
            try:
                self.canvas.scene().removeItem(self.vm_1)
                self.canvas.scene().removeItem(self.vm_2)
                self.canvas.scene().removeItem(self.rb_draw)
                self.canvas.scene().removeItem(self.rb_main)
                self.canvas.scene().removeItem(self.rb_start)
                self.canvas.scene().removeItem(self.rb_end)
            except:
                pass

            final_feat = QgsFeature()
            final_feat.setGeometry(self.offset_geom)

            self.completed.emit(final_feat)

def snapping_point(canvas, point):
    map_coord = canvas.getCoordinateTransform().toMapCoordinates(point) 
    snapped = canvas.snappingUtils().snapToMap(point)
    
    if snapped.isValid():
        return snapped.point(), snapped.isValid()
    else:
        return map_coord, snapped.isValid()

def create_vertex_marker(canvas, type='BOX'):
    vm = QgsVertexMarker(canvas)

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

def create_rubberband(canvas, line_style = 'SOLID_LINE'):
    rb = QgsRubberBand(canvas, False)
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

def create_geom_rubberband(canvas, line_style = 'SOLID_LINE'):
    # QgsGeometryRubberBand allows the usage of circular string so that it will
    # be possible to draw circle without using buffer function
    
    rb = QgsGeometryRubberBand(canvas, False)
    rb.setStrokeColor(QtGui.QColor(128, 128, 128, 180)) # grey
    rb.setFillColor(QtGui.QColor(0, 0, 0, 0))
    rb.setVertexDrawingEnabled(False)
    rb.setStrokeWidth(1)
    if line_style == 'DASH_LINE':
        rb.setLineStyle(QtCore.Qt.DashLine)
    elif line_style == 'SOLID_LINE':
        rb.setLineStyle(QtCore.Qt.SolidLine)
    elif line_style == 'DOT_LINE':
        rb.setLineStyle(QtCore.Qt.DotLine)
    return rb

def arc_highlight(arc):
    arc.setStrokeWidth(2)
    arc.setStrokeColor(QtGui.QColor(100, 100, 100, 180))


def arc_dehighlight(arc):
    arc.setStrokeWidth(1)
    arc.setStrokeColor(QtGui.QColor(128, 128, 128, 180))
