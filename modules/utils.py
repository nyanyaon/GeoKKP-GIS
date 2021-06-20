import re
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton
from qgis.core import (
                    QgsMessageLog,
                    Qgis,
                    QgsCoordinateReferenceSystem,
                    QgsProject,
                    QgsVectorFileWriter,
                    QgsRasterLayer,
                    QgsPointXY)
from qgis.utils import iface
from qgis.gui import QgsMapToolIdentifyFeature
from collections import namedtuple

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

CoordinateValidationResult = namedtuple('CoordinateValidationResult', 'is_valid errors')
CoordinateValidationErrors = namedtuple('CoordinateValidationErrors', 'row, col error_value')

DefaultMessageBarButton = QPushButton()
DefaultMessageBarButton.setText("Show Me")
DefaultMessageBarButton.pressed.connect(iface.openMessageLog)

def logMessage(message, level=Qgis.Info):
    QgsMessageLog.logMessage(message, 'GeoKKP', level=level)


def display_message_bar(tag, message, parent=None, level=Qgis.Info, action=DefaultMessageBarButton, duration=5):
    parent = parent if parent else iface.messageBar()
    widget = parent.createMessage(tag, message)
    if action:
        action.setParent(widget)
        widget.layout().addWidget(action)
    parent.pushWidget(widget, level, duration=duration)

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

def validate_raw_coordinates(raw_coords):
    '''Validate list of coordinate pair with rules below
    1) only number, comma, point, minus, semicolon, whitespace
    2) minus could only be placed in front of number
    3) point could only be placed between number
    4) comma could only be placed between number, whitespace, or tab
    5) simicolon could only be placed after number or whitespace and not in the last position
    6) coordinate number that is allowed are only the number that follow this pattern ^\s*(?:-?\d+\.?\d+)\s*$|;\s*(?:-?\d+\.?\d+)\s*;

    Parameters
    ----------
    raw_coords: str
        list of coordinate pair which separated by semicolon for each pair
    
    Returns
    ----------
    CoordinateValidationResult
        CoordinateValidationResult is a namedtuple contain two attributes, is_valid which indicate whether 
        the raw coordinate is valid or not and errors which is tuple that contain CoordinateValidationError.
        CoordinateValidationError is namedtuple contain the row, col and error_value
    '''
    pattern = '|'.join([
        '(?:[^-.,;\d\r\n \t])',
        '(?:(?<!\D)-|-(?=\D))',
        '(?:(?<=\D)\.|\.(?!\d))',
        '(?:(?<=[^\d \t]),|,(?=[^\d \t]))',
        '(?:(?<=[^\d \t]);|;$)',
        '(?:(?:(?<=^)|(?<=;))\s*(?:-?\d+\.?\d+)\s*(?:(?=;)|(?=$)))'
    ])
    re_pattern = re.compile(pattern)
    
    errors = []
    row = 0
    cursor_pos = 0
    for match in re_pattern.finditer(raw_coords):
        if (match):
            col = match.start() + 1
            row += raw_coords[cursor_pos:col].count('\n')
            cursor_pos = col
            prev_error = len(errors) and errors[-1]
            if prev_error and prev_error.row == row and prev_error.col + 1 == col:
              errors[-1] = CoordinateValidationErrors(
                  row=row,
                  col=col,
                  error_value=prev_error.error_value + match.group()
              )
            else:
              errors.append(CoordinateValidationErrors(
                  row=row,
                  col=col,
                  error_value=match.group()
              ))
    return CoordinateValidationResult(
        is_valid=not len(errors),
        errors=tuple(errors)
    )

def parse_raw_coordinate(coordList):
    stripped_coords = coordList.strip()
    splitted_coords = stripped_coords.split(';')
    for coords in splitted_coords:
        coord_components = coords.split(',')
        if len(coord_components) < 2:
            raise ValueError("Coordinate pair must be consist of two number separated by comma")
        point = QgsPointXY(float(coord_components[0]), float(coord_components[1]))
        yield point