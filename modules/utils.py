from qgis.PyQt.QtCore import Qt, QTimer, QUrl
from qgis.core import (
                    Qgis,
                    QgsCoordinateReferenceSystem,
                    QgsCoordinateTransform,
                    QgsProject,
                    QgsRectangle,
                    QgsPoint,
                    QgsPointXY,
                    QgsGeometry,
                    QgsWkbTypes,
                    QgsVectorLayer,
                    QgsFeature)

from qgis.gui import QgsRubberBand

def __init__(self, iface):
    self.iface = iface
    self.canvas = iface.mapCanvas()
    self.crossRb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
    self.crossRb.setColor(Qt.red)


def zoomTo(self, src_crs, lat, lon):
    canvas_crs = self.canvas.mapSettings().destinationCrs()
    transform = QgsCoordinateTransform(src_crs, canvas_crs, QgsProject.instance())
    x, y = transform.transform(float(lon), float(lat))

    rect = QgsRectangle(x, y, x, y)
    self.canvas.setExtent(rect)

    pt = QgsPointXY(x, y)
    self.highlight(pt)
    self.canvas.refresh()
    return pt

def highlight(self, point):
    currExt = self.canvas.extent()

    leftPt = QgsPoint(currExt.xMinimum(), point.y())
    rightPt = QgsPoint(currExt.xMaximum(), point.y())

    topPt = QgsPoint(point.x(), currExt.yMaximum())
    bottomPt = QgsPoint(point.x(), currExt.yMinimum())

    horizLine = QgsGeometry.fromPolyline([leftPt, rightPt])
    vertLine = QgsGeometry.fromPolyline([topPt, bottomPt])

    self.crossRb.reset(QgsWkbTypes.LineGeometry)
    self.crossRb.addGeometry(horizLine, None)
    self.crossRb.addGeometry(vertLine, None)

    QTimer.singleShot(700, self.resetRubberbands)

def resetRubberbands(self):
    self.crossRb.reset()