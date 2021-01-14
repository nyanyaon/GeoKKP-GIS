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

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

def loadXYZ(url, name):
    rasterLyr = QgsRasterLayer("type=xyz&zmin=0&zmax=21&url=" + url, name, "wms")
    QgsProject.instance().addMapLayer(rasterLyr)