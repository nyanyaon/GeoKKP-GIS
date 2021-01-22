import os
import re

from qgis.PyQt.QtCore import Qt, QTimer, QUrl
from qgis.gui import QgsRubberBand

from PyQt5 import uic
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.core import (Qgis,
                    QgsCoordinateReferenceSystem,
                    QgsCoordinateTransform,
                    QgsRectangle,
                    QgsPoint,
                    QgsPointXY,
                    QgsGeometry,
                    QgsWkbTypes,
                    QgsVectorLayer,
                    QgsFeature,
                    QgsProcessingFeatureSourceDefinition,
                    QgsProcessingParameterVectorLayer,
                    QgsProject, QgsApplication)
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.gui import QgsMapToolIdentifyFeature, QgsMapMouseEvent, QgsMapToolEmitPoint

import processing
from processing.gui import AlgorithmExecutor

#using utils
from .utils import epsg4326, is_layer_exist

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/adjust.ui'))

class AdjustDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog for Parcel Adjust"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        
        super(AdjustDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.project = QgsProject

        uri = os.path.join(os.path.dirname(__file__), '../images/icon.png')
        self.setWindowIcon(QtGui.QIcon(uri))

        self._layer = None
        self.set_identify_layer()

        self.layerAcuan.layerChanged.connect(self.set_reference_layer)
        #self.clickTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.identifyFeature = QgsMapToolIdentifyFeature(self.canvas, self._layer)
        #self.clickTool.canvasClicked.connect(self.test)
        self.adjustButton.clicked.connect(self.adjust_parcel)

        self.activate_selection()
    
    def set_identify_layer(self):
        layername = 'Persil'
        for layer in self.project.instance().mapLayers().values():
            #print(layer.name(), " - ", layername)
            if (layer.name() == layername):
                print("persilada")
                self._layer = layer
        print(self._layer)


    def set_reference_layer(self):

        #if is_layer_exist(self.project, 'Persil'):
        #    print("layer exist")
        #    self._layer = self.project.instance().mapLayersByName('Persil')[0]
        ##else:
        #    print("persil layer not exist")
        self._refLayer = self.layerAcuan.currentLayer()
        print(self._refLayer.name())


    def activate_selection(self):
        print("activate selection")
        #self.iface.actionSelect().trigger()
        ##features = self._layer.selectedFeatures()[0]
        #print(features)
        
        self.identifyFeature.setCursor(QCursor(Qt.PointingHandCursor))
        self.identifyFeature.featureIdentified.connect(self.on_feature_identified)
        self.canvas.setMapTool(self.identifyFeature)

    def on_feature_identified(self, feature):
        print("onfeatureidentified")
        print("feature identified")
        self._layer.selectByIds([feature.id()])
        print(feature[0])
        self.fiturTerpilih.setText("NIB = " + feature[0])
        #self._layer.deselect(feature.id())
        #self.clickTool.canvasClicked.disconnect(self.activate_selection)
        #self.iface.actionPan().trigger()

        #self.iface.openFeatureForm(self._layer, feature)        
        
    def adjust_parcel(self):       
        print("adjust")
        autoadjusttool = QgsApplication.processingRegistry().createAlgorithmById('native:snapgeometries')
        autoadjust2 = autoadjusttool.create({'IN_PLACE': True})
        parameters = {
                'INPUT': self._layer.id(),
                'REFERENCE_LAYER': self._refLayer.id(),
                'TOLERANCE': 10,
                'BEHAVIOR': 2,
                'OUTPUT':'memory:'
            }

        #AlgorithmExecutor.execute_in_place_run(autoadjust2, parameters)

        result = processing.runAndLoadResults(autoadjust2, parameters)
        #print(result['OUTPUT'])

        
