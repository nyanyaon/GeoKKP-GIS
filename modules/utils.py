import os
from PyQt5.QtGui import QIcon
from qgis.core import (
                    QgsMessageLog,
                    Qgis,
                    QgsCoordinateReferenceSystem,
                    QgsProject,
                    QgsVectorFileWriter,
                    QgsRasterLayer)
from qgis.utils import iface
from qgis.gui import QgsMapToolIdentifyFeature

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')


def logMessage(message, level=Qgis.Info):
    QgsMessageLog.logMessage(message, 'GeoKKP', level=level)


def loadXYZ(url, name):
    rasterLyr = QgsRasterLayer("type=xyz&zmin=0&zmax=21&url=" + url, name, "wms")
    QgsProject.instance().addMapLayer(rasterLyr)


def activate_editing(layer):
    QgsProject.instance().setTopologicalEditing(True)
    layer.startEditing()
    iface.layerTreeView().setCurrentLayer(layer)
    iface.actionAddFeature().trigger()
    # for vertex editing
    # iface.actionVertexTool().trigger()


def is_layer_exist(project, layername):
    for layer in project.instance().mapLayers().values():
        print(layer.name(), " - ", layername)
        if (layer.name == layername):
            print("layer exist")
            return True
        else:
            return False


def edit_by_identify(mapcanvas, layer):
    print("identify", mapcanvas)
    print("layer", layer.name())

    layer = iface.activeLayer()
    mc = iface.mapCanvas()

    mapTool = QgsMapToolIdentifyFeature(mc)
    mapTool.setLayer(layer)
    mc.setMapTool(mapTool)
    mapTool.featureIdentified.connect(onFeatureIdentified)


def onFeatureIdentified(feature):
    fid = feature.id()
    print("feature selected : " + str(fid))


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


def iconPath(name):
    logMessage(os.path.join(os.path.dirname(__file__), "images", name))
    return os.path.join(os.path.dirname(__file__), "..", "images", name)


def icon(name):
    return QIcon(iconPath(name))
