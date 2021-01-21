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
from qgis.utils import iface
from qgis.gui import QgsRubberBand, QgsMapToolIdentifyFeature, QgsMapToolIdentify

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

def loadXYZ(url, name):
    rasterLyr = QgsRasterLayer("type=xyz&zmin=0&zmax=21&url=" + url, name, "wms")
    QgsProject.instance().addMapLayer(rasterLyr)

def activate_editing(layer):
    QgsProject.instance().setTopologicalEditing(True)
    layer.startEditing()
    iface.layerTreeView().setCurrentLayer(layer)

    # for vertex editing
    #iface.actionVertexTool().trigger()

def edit_by_identify(mapcanvas, layer):
    print("identify", mapcanvas)
    print("layer", layer.name())

    layer = iface.activeLayer()
    mc=iface.mapCanvas()

    mapTool = QgsMapToolIdentifyFeature(mc)
    mapTool.setLayer(layer)
    mc.setMapTool(mapTool)
    mapTool.featureIdentified.connect(onFeatureIdentified)

def onFeatureIdentified(feature):
    fid = feature.id()
    print ("feature selected : " + str(fid))
