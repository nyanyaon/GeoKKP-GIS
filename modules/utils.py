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
    iface.actionAddFeature().trigger()
    # for vertex editing
    #iface.actionVertexTool().trigger()

def is_layer_exist(project, layername):
    for layer in project.instance().mapLayers().values():
        print(layer.name(), " - ", layername)
        if (layer.name == layername):
            print("layer exist")
            _layer = layer
            return True

        else:
            return False

               


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


def save_with_description(layer, outputfile):
    options = QgsVectorFileWriter.SaveVectorOptions()

    # If geopackage exists, append layer to it, else create it
    if os.path.exists(outputfile):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    else:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

    # Use input layer abstract and name in the geopackage
    options.layerOptions = [f"DESCRIPTION={layer.abstract()}"]
    options.layerName = layer.name()
    return QgsVectorFileWriter.writeAsVectorFormat(layer, outputfile, options)