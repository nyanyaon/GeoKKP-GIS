import re
import os
import json

from multiprocessing.dummy import Pool as ThreadPool
from functools import partial

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QPushButton
from qgis.core import (
                    QgsMessageLog,
                    QgsSettings,
                    Qgis,
                    QgsCoordinateReferenceSystem,
                    QgsProject,
                    QgsVectorFileWriter,
                    QgsRasterLayer,
                    QgsVectorLayer,
                    QgsField,
                    QgsPointXY,
                    QgsGeometry,
                    QgsFeature,
                    QgsApplication,
                    QgsAuthMethodConfig,
                    QgsProcessingFeatureSourceDefinition)
from qgis.utils import iface
from qgis.gui import QgsMapToolIdentifyFeature
from collections import namedtuple
from qgis import processing

"""
Kumpulan Utilities untuk GeoKKP-QGIS
===========================================

Variabel global dan modul global untuk digunakan di plugin GeoKKP-GIS

TODO: Pindah variabel & konstanta global ke modul terpisah
"""


epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

CoordinateValidationResult = namedtuple('CoordinateValidationResult', 'is_valid errors')
CoordinateValidationErrors = namedtuple('CoordinateValidationErrors', 'row, col error_value')

DefaultMessageBarButton = QPushButton()
DefaultMessageBarButton.setText("Show Me")
DefaultMessageBarButton.pressed.connect(iface.openMessageLog)

# constants for NLP
x_origin = 32000
y_origin = 282000
grid_10rb = 6000
grid_2500 = 1500
grid_1000 = 500
grid_500 = 250
grid_250 = 125

# list of layers and basemaps
layer_json_file = os.path.join(
    os.path.dirname(__file__), '../config/layers.json')
basemap_json_file = os.path.join(
    os.path.dirname(__file__), '../config/basemap.json')


def simpan_layer_settings():
    """
    Panggil daftar layer dan simbologi dari file layers.json, simpan ke dalam pengaturan lokal
    """
    f = open(layer_json_file,)
    data = json.load(f)
    for i in data['layers']:
        pass
    f.close()
    storeSetting("geokkp/layers", data['layers'])


def simpan_basemap_settings():
    """
    Panggil daftar basemap dari file basemap.json, simpan ke dalam pengaturan lokal
    """
    f = open(basemap_json_file,)
    data = json.load(f)
    for i in data['basemaps']:
        pass
    f.close()
    storeSetting("geokkp/basemaps", data['basemaps'])


def logMessage(message, level=Qgis.Info):
    """
    Logger untuk debugging
    """
    QgsMessageLog.logMessage(message, 'GeoKKP-GIS', level=level)


def display_message_bar(tag, message, parent=None, level=Qgis.Info, action=DefaultMessageBarButton, duration=5):
    """
    Wrapper untuk menampilkan pesan di message bar
    """
    parent = parent if parent else iface.messageBar()
    widget = parent.createMessage(tag, message)
    if action:
        action.setParent(widget)
        widget.layout().addWidget(action)
    parent.pushWidget(widget, level, duration=duration)


def loadXYZ(url, name):
    """
    Memuat layer dalam bentuk XYZ Tile
    """
    rasterLyr = QgsRasterLayer("type=xyz&zmin=0&zmax=21&url=" + url, name, "wms")
    QgsProject.instance().addMapLayer(rasterLyr)


def activate_editing(layer):
    """
    Activate layer editing tools
    TODO: fix conflicts with built-in layer editing in QGIS
    """
    QgsProject.instance().setTopologicalEditing(True)
    layer.startEditing()
    iface.layerTreeView().setCurrentLayer(layer)
    iface.actionAddFeature().trigger()
    # for vertex editing
    # iface.actionVertexTool().trigger()


def storeSetting(key, value):
    """
    Store value to QGIS Settings
    """
    settings = QgsSettings()
    settings.setValue(key, value)


def readSetting(key, default_value=None):
    """
    Read value from QGIS Settings
    """
    settings = QgsSettings()
    return settings.value(key, default_value)


def clear_all_vars():
    """ Hapus semua value dari QgsSettings yang digunakan oleh GeoKKP"""
    s = QgsSettings()
    for x in sorted(s.allKeys()):
        if x.startswith("geokkp"):
            s.setValue(x, "")
    QgsMessageLog.logMessage("Flushed all user vars", 'GeoKKP-GIS', level=Qgis.Info)


def is_layer_exist(project, layername):
    """
    Boolean check if layer exist
    """
    for layer in project.instance().mapLayers().values():
        if (layer.name == layername):
            return True
        else:
            return False


def set_symbology(self, layer, qml):
    """
    Set layer symbology based on QML files in ./styles folder
    """
    uri = os.path.join(os.path.dirname(__file__), 'styles/'+qml)
    layer.loadNamedStyle(uri)


def properify(self, text):
    """
    Filter text for OS's friendly directory format

    Remove all non-word characters (everything except numbers and letters) and
    replace all runs of whitespace with a single dash

    """
    text = re.sub(r"[^\w\s]", '', text)
    text = re.sub(r"\s+", '_', text)
    return text


def edit_by_identify(mapcanvas, layer):
    layer = iface.activeLayer()
    mc = iface.mapCanvas()
    mapTool = QgsMapToolIdentifyFeature(mc)
    mapTool.setLayer(layer)
    mc.setMapTool(mapTool)
    mapTool.featureIdentified.connect(onFeatureIdentified)


def onFeatureIdentified(feature):
    fid = feature.id()
    return fid


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
    r'''Validate list of coordinate pair with rules below
    1) only number, comma, point, minus, semicolon, whitespace
    2) minus could only be placed in front of number
    3) point could only be placed between number
    4) comma could only be placed between number, whitespace, or tab
    5) simicolon could only be placed after number or whitespace and not in the last position
    6) coordinate number that is allowed are only the number that follow
        this pattern ^\s*(?:-?\d+\.?\d+)\s*$|;\s*(?:-?\d+\.?\d+)\s*;

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
        r'(?:[^-.,;\d\r\n \t])',
        r'(?:(?<!\D)-|-(?=\D))',
        r'(?:(?<=\D)\.|\.(?!\d))',
        r'(?:(?<=[^\d \t]),|,(?=[^\d \t]))',
        r'(?:(?<=[^\d \t]);|;$)',
        r'(?:(?:(?<=^)|(?<=;))\s*(?:-?\d+\.?\d+)\s*(?:(?=;)|(?=$)))'
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


GPOINT = 'Point'
GLINESTRING = 'LineString'
GPOLYGON = 'Polygon'
SDO_GTYPE_MAP = {
    '00': 'Unknown',
    '01': GPOINT,
    '02': GLINESTRING,
    '03': GPOLYGON,
    '04': 'Collection',
    '05': 'MultiPoint',
    '06': 'MultiLine',
    '07': 'MultiPolygon',
    '08': 'Solid',
    '09': 'MultiSolid',
}
SDO_FIELD_EXCLUDE = ['text', 'boundary', 'rotation', 'height']


def parse_sdo_geometry_type(sdo_gtype):
    sdo_gtype_str = str(sdo_gtype).rjust(4, '0')
    gtype = sdo_gtype_str[2:4]
    dim = max(2, int(sdo_gtype_str[0]))
    return SDO_GTYPE_MAP[gtype], dim


def parse_sdo_fields(sdo):
    fields = [field for field in sdo.keys() if field not in SDO_FIELD_EXCLUDE]
    return [QgsField(field, QVariant.String) for field in fields], fields


def parse_sdo_geometry(elem_info, ordinates):
    start_index = elem_info[0] - 1
    gtype, dim = parse_sdo_geometry_type(elem_info[1])

    result = []
    start = start_index
    while True:
        end = start + min(2, dim)
        result.append(QgsPointXY(*ordinates[start:end]))
        start += dim
        if start >= len(ordinates):
            break

    if gtype == GPOINT:
        return QgsGeometry.fromPointXY(result[0])
    elif gtype == GLINESTRING:
        return QgsGeometry.fromPolyline(result)
    elif gtype == GPOLYGON:
        return QgsGeometry.fromPolygonXY([result])


def sdo_to_feature(sdo, fields):
    attrs = [sdo[f] for f in fields]
    geometry = parse_sdo_geometry(sdo['boundary']['sdoElemInfo'], sdo['boundary']['sdoOrdinates'])

    feature = QgsFeature()
    feature.setGeometry(geometry)
    feature.setAttributes(attrs)

    return feature


def sdo_to_layer(sdo, name, crs=None):
    if not isinstance(sdo, list):
        sdo = [sdo]

    gtype, dim = parse_sdo_geometry_type(sdo[0]['boundary']['sdoGtype'])
    uri = gtype if not crs else f'{gtype}?crs={crs}'
    layer = QgsVectorLayer(uri, name, 'memory')
    fields, raw_fields = parse_sdo_fields(sdo[0])

    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()

    pool = ThreadPool()
    func = partial(sdo_to_feature, fields=raw_fields)
    features = pool.map(func, sdo)
    pool.close()
    pool.join()
    provider.addFeatures(features)
    layer.commitChanges()

    return layer


def get_epsg_from_tm3_zone(zone, include_epsg_key=True):
    splitted_zone = zone.split('.')
    major = int(splitted_zone[0])
    minor = int(splitted_zone[1]) if len(splitted_zone) == 2 else 1
    if major < 46 or major > 54:
        return False
    magic = (major * 2 + minor) - 64
    return f'EPSG:238{magic}' if include_epsg_key else f'238{magic}'


def get_saved_credentials():
    auth_mgr = QgsApplication.authManager()
    auth_id = readSetting('geokkp/authId')
    auth_cfg = QgsAuthMethodConfig()
    if auth_id:
        auth_mgr.loadAuthenticationConfig(auth_id, auth_cfg, True)
    return auth_cfg.configMap()


def save_credentials(username, password):
    auth_mgr = QgsApplication.authManager()
    auth_id = readSetting('geokkp/authId')
    auth_cfg = QgsAuthMethodConfig()
    if not auth_id:
        auth_id = auth_cfg.id()
        auth_cfg.setName('geokkp')
        auth_cfg.setMethod('Basic')
    else:
        auth_mgr.loadAuthenticationConfig(auth_id, auth_cfg, True)

    auth_cfg.setConfig('username', username)
    auth_cfg.setConfig('password', password)
    assert auth_cfg.isValid()
    auth_mgr.storeAuthenticationConfig(auth_cfg)
    assert auth_cfg.id()
    storeSetting('geokkp/authId', auth_cfg.id())
    return auth_cfg.id()


def add_layer(layername, type, symbol=None, fields=None, crs=None, parent=None):
    crs = iface.mapCanvas().mapSettings().destinationCrs()
    print("CRSCRSCRSCRSCRSC", crs)

    layer = QgsVectorLayer(f"{type}?crs=epsg:" + str(crs.postgisSrid()), layername, "memory")
    layer_dataprovider = layer.dataProvider()
    if not fields:
        field_list = [
            QgsField("ID", QVariant.String),
            QgsField("Keterangan", QVariant.String),
        ]
    else:
        field_list = []
        for key,value in fields.items():
            if value == 'String':
                field_type = QVariant.String
            elif value == 'Int':
                field_type = QVariant.Int
            elif value == 'Double':
                field_type = QVariant.Double
            field = QgsField(key, field_type)
            field_list.append(field)
    if symbol:
        symbolurl = os.path.join(os.path.dirname(__file__), '../styles/'+symbol)
        layer.loadNamedStyle(symbolurl)

    layer_dataprovider.addAttributes(field_list)
    layer.updateFields()
    QgsProject.instance().addMapLayer(layer)


def resolve_path(name, basepath=None):
    if not basepath:
        basepath = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(basepath, name)


def set_project_crs_by_epsg(epsg):
    crs = QgsCoordinateReferenceSystem(epsg)
    QgsProject.instance().setCrs(crs)


SNAP_ALIGNING_NODE_INSERT_WHEN_REQUIRED = 0
SNAP_CLOSEST_NODE_INSERT_WHEN_REQUIRED = 1
SNAP_ALIGNING_NODE_NOT_INSERT = 2
SNAP_CLOSEST_NODE_NOT_INSERT = 3
SNAP_MOVE_END_POINT_ALIGN_NODE = 4
SNAP_MOVE_END_CLOSEST_NODE = 5
SNAP_ENDPOINT_TO_ENDPOINT = 6
SNAP_ANCHOR_NODES = 7


def snap_geometries_to_layer(
        layer,
        ref_layer,
        tolerance=1,
        behavior=SNAP_MOVE_END_POINT_ALIGN_NODE,
        output='memory:snap'):
    if isinstance(layer, str):
        layer = get_layer_by_id(layer)
    is_selected = bool(layer.selectedFeatureCount())

    parameters = {
        'INPUT': QgsProcessingFeatureSourceDefinition(layer.id(), is_selected),
        'REFERENCE_LAYER': QgsProcessingFeatureSourceDefinition(ref_layer.id(), False),
        'TOLERANCE': tolerance,
        'BEHAVIOR': behavior,
        'OUTPUT': output
    }
    print(parameters)
    result = processing.run('qgis:snapgeometries', parameters)

    return result['OUTPUT']


def explode_polyline(layer, output='memory:explode'):
    if isinstance(layer, str):
        layer = get_layer_by_id(layer)
    is_selected = bool(layer.selectedFeatureCount())

    parameters = {
        'INPUT': QgsProcessingFeatureSourceDefinition(layer.id(), is_selected),
        'OUTPUT': output
    }
    result = processing.run('native:explodelines', parameters)

    return result['OUTPUT']


def polygonize(layer, output='memory:polygonize'):
    if isinstance(layer, str):
        layer = get_layer_by_id(layer)
    is_selected = bool(layer.selectedFeatureCount())

    parameters = {
        'INPUT': QgsProcessingFeatureSourceDefinition(layer.id(), is_selected),
        'OUTPUT': output
    }
    result = processing.run('qgis:polygonize', parameters)

    return result['OUTPUT']


def dissolve(layer, output='memory:dissolve'):
    if isinstance(layer, str):
        layer = get_layer_by_id(layer)
    is_selected = bool(layer.selectedFeatureCount())

    parameters = {
        'INPUT': QgsProcessingFeatureSourceDefinition(layer.id(), is_selected),
        'OUTPUT': output
    }
    result = processing.run('native:dissolve', parameters)

    return result['OUTPUT']


def get_layer_by_id(layer_id):
    return QgsProject.instance().mapLayer(layer_id)


def get_nlp(skala, x, y):
    """
    Cetak Nomor Lembar Peta berdasarkan skala

    argumen:
        skala   : skala peta dalam string
        x       : koordinat x dalam CRS TM3
        y       : koordinat y dalam CRS TM3
    """

    # Skala 10 ribu
    k_10rb = int((x - x_origin)/grid_10rb)+1
    b_10rb = int((y - y_origin)/grid_10rb)+1

    # Skala 2500
    k_2500 = int((x-(x_origin+(k_10rb - 1)*grid_10rb))/grid_2500)+1
    b_2500 = int((y-(y_origin+(b_10rb - 1)*grid_10rb))/grid_2500)+1
    nlp_2500 = 4*(b_2500-1)+k_2500

    # Skala 1000
    k_1000 = int((x-(x_origin+(k_10rb - 1)*grid_10rb + (k_2500-1)*grid_2500))/grid_1000)+1
    b_1000 = int((y-(y_origin+(b_10rb - 1)*grid_10rb + (b_2500-1)*grid_2500))/grid_1000)+1
    nlp_1000 = 3*(b_1000-1)+k_1000

    # Skala 500
    k_500 = int((x-(x_origin+(k_10rb - 1)*grid_10rb + ((k_2500-1)*grid_2500) + (k_1000-1)*grid_1000))/grid_500)+1
    b_500 = int((y-(y_origin+(b_10rb - 1)*grid_10rb + ((b_2500-1)*grid_2500) + (b_1000-1)*grid_1000))/grid_500)+1
    nlp_500 = 2*(b_500-1)+k_500

    # Skala 250
    k_250 = int((x-(x_origin+(k_10rb - 1)*grid_10rb
            + ((k_2500-1)*grid_2500) # noqa
            + ((k_1000-1)*grid_1000)
            + (k_500-1)*grid_500))/grid_250)+1
    b_250 = int((y-(y_origin+(b_10rb - 1)*grid_10rb
            + ((b_2500-1)*grid_2500) # noqa
            + ((b_1000-1)*grid_1000)
            + (b_500-1)*grid_500))/grid_250)+1
    nlp_250 = 2*(b_250-1)+k_250

    if (skala == "10000"):
        return f'{k_10rb:02d}.{b_10rb:03d}'
    elif (skala == "2500"):
        return f'{k_10rb:02d}.{b_10rb:03d}-{nlp_2500:02d}'
    elif (skala == "1000"):
        return f'{k_10rb:02d}.{b_10rb:03d}-{nlp_2500:02d}-{nlp_1000}'
    elif (skala == "500"):
        return f'{k_10rb:02d}.{b_10rb:03d}-{nlp_2500:02d}-{nlp_1000}-{nlp_500}'
    elif (skala == "250"):
        return f'{k_10rb:02d}.{b_10rb:03d}-{nlp_2500:02d}-{nlp_1000}-{nlp_500}-{nlp_250}'
    else:
        return "Kesalahan Penentuan skala"
