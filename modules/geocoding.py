"""
/***************************************************************************
Adopted from a Geocoding & Reverse Geocoding script (2008) 
by ItOpen (info@itopen.it)
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


import os
from .geocoder import OsmGeoCoder
from .geocoding_dialoglokasi import PlaceSelectionDialog


from qgis.PyQt.QtCore import Qt, QTimer
from qgis.gui import QgsRubberBand

from qgis.core import (
    QgsCoordinateTransform,
    QgsVectorLayer,
    QgsPoint,
    QgsVectorLayerSimpleLabeling,
    QgsPointXY,
    QgsGeometry,
    QgsField,
    QgsFeature,
    QgsProject,
    QgsCoordinateReferenceSystem,    
    QgsPalLayerSettings
)

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QCoreApplication, QVariant
from qgis.utils import iface

# using utils
from .utils import dialogBox, icon, logMessage, parse_raw_coordinate


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "../ui/geocoding.ui"))


class GeocodingDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Geocoding"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(GeocodingDialog, self).__init__(parent)
        # self.utils = Utilities
        self.setWindowIcon(icon("icon.png"))
        self._currentcrs = None
        self.setupUi(self)

        self.layerid = ''

        self.geocoder = OsmGeoCoder()
        self.terapkan_lokasi.clicked.connect(self.cariLokasi)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def cariLokasi(self):
        try:
            result = self.geocoder.geocode(unicode(self.cari_lokasi.text()).encode('utf-8'))
        except Exception as e:
            dialogBox(str(e))
            return

        if not result:
            dialogBox("Pencarian tidak mendapatkan hasil")
            return

        places = {}
        for place, point in result:
            places[place] = point

        if len(places) == 1:
            self.process_point(place, point)
        else:
            all_str = QCoreApplication.translate('GeoCoding', 'All')
            place_dlg = PlaceSelectionDialog()
            place_dlg.placesComboBox.addItem(all_str)
            place_dlg.placesComboBox.addItems(places.keys())
            place_dlg.show()
            result = place_dlg.exec_()
            if result == 1 :
                if place_dlg.placesComboBox.currentText() == all_str:
                    for place in places:
                        self.process_point(place, places[place])
                else:
                    point = places[unicode(place_dlg.placesComboBox.currentText())]
                    self.process_point(place_dlg.placesComboBox.currentText(), point)
        return

    def process_point(self, place, point):
        """
        Transforms the point and save
        """
        # lon lat and transform
        point = QgsPoint(float(point[0]), float(point[1]))
        point = self.pointFromWGS84(point, self._get_layer_crs())
        
        # Set the extent to our new point
        self.canvas.setCenter(point)

        # Refresh the map
        self.canvas.refresh()
        # save point
        self.save_point(point, unicode(place))

    def _get_layer_crs(self):
        """get CRS from destination layer or from canvas if the layer does not exist"""
        try:
            return self.layer.crs()
        except:
            return self._get_canvas_crs()

    def _get_canvas_crs(self):
        """compat"""
        try:
            return self.iface.mapCanvas().mapRenderer().destinationCrs()
        except:
            return self.iface.mapCanvas().mapSettings().destinationCrs()

    def _get_registry(self):
        """compat"""
        try:
            return QgsMapLayerRegistry.instance()
        except:
            return QgsProject.instance()

    def pointFromWGS84(self, point, crs):
        f=QgsCoordinateReferenceSystem()
        f.createFromSrid(4326)
        t=crs # QgsCoordinateReferenceSystem()
        #t.createFromProj4(proj4string)
        try:
            transformer = QgsCoordinateTransform(f,t)
        except:
            transformer = QgsCoordinateTransform(f, t, QgsProject.instance())
        try:
            pt = transformer.transform(point)
        except:
            pt = transformer.transform(QgsPointXY(point)) 
        return pt

    def save_point(self, point, address):
        logMessage('Menuju ke lokasi pencarian: ' + str(point[0])  + ' ' + str(point[1]))
        # create and add the point layer if not exists or not set
        if not self._get_registry().mapLayer(self.layerid) :
            # create layer with same CRS as map canvas
            crs = self._get_canvas_crs()
            self.layer = QgsVectorLayer("Point?crs=" + crs.authid(), "Pencarian Lokasi", "memory")
            self.provider = self.layer.dataProvider()

            # add fields
            self.provider.addAttributes([QgsField("address", QVariant.String)])

            # BUG: need to explicitly call it, should be automatic!
            self.layer.updateFields()

            # Labels on
            try:
                label_settings = QgsPalLayerSettings()
                label_settings.fieldName = "address"
                self.layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
                self.layer.setLabelsEnabled(True)
            except:
                self.layer.setCustomProperty("labeling", "pal")
                self.layer.setCustomProperty("labeling/enabled", "true")
                #self.layer.setCustomProperty("labeling/fontFamily", "Arial")
                #self.layer.setCustomProperty("labeling/fontSize", "10")
                self.layer.setCustomProperty("labeling/fieldName", "address")
                self.layer.setCustomProperty("labeling/placement", "2")

            # add layer if not already
            self._get_registry().addMapLayer(self.layer)

            # store layer id
            self.layerid = self.layer.id()


        # add a feature
        try:
            fields=self.layer.pendingFields()
        except:
            fields=self.layer.fields()

        fet = QgsFeature(fields)
        try:
            fet.setGeometry(QgsGeometry.fromPoint(point))
        except:
            fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point)))

        try: # QGIS < 1.9
            fet.setAttributeMap({0 : address})
        except: # QGIS >= 1.9
            fet['address'] = address

        self.layer.startEditing()
        self.layer.addFeatures([ fet ])
        self.layer.commitChanges()
    

    

  
